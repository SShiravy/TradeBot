from ChartModule.models import Candle, MarketSide
from ChartModule.Indicators.models import IndicatorBaseModel
from ChartModule.plot import ChartPlot
from ChartModule.Indicators.swing_pivots import SwingPivots, PivotPoint
from SRZoneModule.atr import ATR
from dataclasses import dataclass, field, replace
from statistics import median
import logging
import math


logger = logging.getLogger("SRZones")


@dataclass(slots=True)
class ZoneModel:
    is_support: bool
    center: float
    width: float
    base_index: int
    base_candle: Candle
    last_touch_index: int
    last_touch_candle: Candle

    sum_price: float = field(init=False)
    member_count: int = field(default=1, init=False)
    touch_count: int = field(default=1, init=False)
    break_count: int = field(default=0, init=False)
    consec_break: int = field(default=0, init=False)
    was_in_band: bool = field(default=False, init=False)
    max_touch_gap: int = field(default=0, init=False)
    raw_score: float = field(default=0.0, init=False)
    score_pct: float = field(default=0.0, init=False)

    invalidated_index: int | None = field(default=None, init=False)
    # kept alongside invalidated_index: `self.candles` is a sliding window,
    # so an index recorded now can point at the wrong candle (or even go
    # negative/out of range) once the window has shifted by the time this
    # zone is drawn. A direct Candle reference (like base_candle/
    # last_touch_candle already are) stays correct no matter how the
    # window moves.
    invalidated_candle: Candle | None = field(default=None, init=False)

    # role-reversal ("change of nature"): when `max_zone_breaks > 1`, a
    # zone is allowed to survive a break instead of being invalidated by
    # it -- and a support/resistance level that price has broken through
    # conventionally flips role (broken support acts as resistance from
    # then on, and vice versa). `polarity_segments` records that history:
    # the candle at which each polarity started, paired with the polarity
    # that was in effect from that candle onward. It always has at least
    # one entry (the zone's original candle/polarity) and gets a new
    # entry appended every time the zone flips.
    polarity_segments: list[tuple[Candle, bool]] = field(default_factory=list, init=False)

    def __post_init__(self):
        self.sum_price = self.center
        self.polarity_segments = [(self.base_candle, self.is_support)]

    @property
    def upper(self) -> float:
        return self.center + self.width

    @property
    def lower(self) -> float:
        return self.center - self.width

    @property
    def broken(self) -> bool:
        return self.invalidated_index is not None

    @property
    def flipped(self) -> bool:
        return len(self.polarity_segments) > 1

    def __str__(self) -> str:
        side = "Support" if self.is_support else "Resistance"
        flip = f"|flips={len(self.polarity_segments) - 1}" if self.flipped else ""
        return (
            f"{side}|center={self.center:.5f}|touch={self.touch_count}"
            f"|break={self.break_count}|broken={self.broken}{flip}|score={self.score_pct:.1f}"
        )


class SRZones(IndicatorBaseModel):
    def __init__(
        self,
        # (1) Pivot Detection (ZigZag)
        depth: int = 12,
        backstep: int = 2,
        max_candidates: int = 150,
        # (2) Adaptive Radius
        atr_len: int = 14,
        atr_median_lookback: int = 21,
        radius_factor: float = 1.0,
        min_radius_mult: float = 0.25,
        max_radius_mult: float = 3.0,
        # (3) Clustering
        merge_nearby: bool = True,
        merge_interval_bars: int = 300,
        # (5) Zone Width
        width_mult: float = 1.0,
        fallback_width_factor: float = 0.35,
        # (6) Zone Score
        max_zone_touches: int = 5,
        max_zone_breaks: int = 1,
        zone_break_bars: int = 2,
        # (7) Touch Spacing
        min_bars_between_touches: int = 3,
        max_bars_between_touches: int = 300,
        # bookkeeping (mirrors Pine's hardcoded f_pruneZones age, 4500)
        prune_after_bars: int = 4500,
        # storage cap (not a Pine input -- Pine's box/label count is capped
        # by the indicator() call's max_boxes_count/max_labels_count instead;
        # this is the equivalent guard for update()'s persistent zone list)
        max_stored_zones: int = 200,
    ) -> None:
        super().__init__()
        self.data: list[ZoneModel]

        self.pivots = SwingPivots(depth, backstep)
        self.atr = ATR(atr_len)

        self.max_candidates = max_candidates
        self.atr_median_lookback = atr_median_lookback
        self.radius_factor = radius_factor
        self.min_radius_mult = min_radius_mult
        self.max_radius_mult = max_radius_mult
        self.merge_nearby = merge_nearby
        self.merge_interval_bars = merge_interval_bars
        self.width_mult = width_mult
        self.fallback_width_factor = fallback_width_factor
        self.max_zone_touches = max_zone_touches
        self.max_zone_breaks = max_zone_breaks
        self.zone_break_bars = zone_break_bars
        self.min_bars_between_touches = min_bars_between_touches
        self.max_bars_between_touches = max_bars_between_touches
        self.prune_after_bars = prune_after_bars
        self.max_stored_zones = max_stored_zones

        self._zones: list[ZoneModel] = []
        self._pivot_log: list[PivotPoint] = []
        self._last_median_atr: float = 0.0
        self._last_base_radius: float = 0.0

        # running state carried between `_calculate()` and every subsequent
        # `update()` call, so update() can resume exactly where the last
        # call left off instead of recomputing from bar 0 -- same idea as
        # `SwingPivots`'s own `_direction`/`_high_idx`/... running state.
        self._atr_buf: list[float] = []
        self._pivot_gaps: list[int] = []
        self._last_confirmed_bar_index: int | None = None
        self._med_pivot_spacing: float = 20.0
        self._median_atr: float | None = None
        self._base_radius: float | None = None
        # highest `confirmed_index` already fed into `_process_new_pivot`.
        # `SwingPivots.update()` rebuilds its ENTIRE confirmed list from
        # scratch every call (backstep is re-applied over the full
        # cumulative raw-pivot history), so `self.pivots.data` on update()
        # is not "just the new pivots" -- this is what filters it back down
        # to only the ones this engine hasn't already committed to a zone.
        self._last_processed_confirm_index: int | None = None

        # `candles` is a SLIDING WINDOW (each poll refetches the last
        # `n_candle_check` candles), not an append-only array, so every
        # index stored above (`base_index`, `last_touch_index`,
        # `invalidated_index`, pivot indices in `_pivot_log`, etc.) goes
        # stale by however many candles fell off the front since it was
        # recorded. `_last_checked_index` remembers where the last-seen
        # candle sat in the window last time, so `update()` can measure
        # that drift and `_rebase()` everything before doing anything else.
        # Without this, a fresh pivot's (correctly-based) index can end up
        # SMALLER than a stale `_last_processed_confirm_index`, so the
        # pivot gets silently filtered out and never turns into a new
        # zone -- and stale `last_touch_index`/`invalidated_index` values
        # make zones look younger than they are, so they never get broken
        # or pruned and keep lingering (with their origin candle long
        # outside any freshly plotted window).
        self._last_checked_index: int = 0

    def export_configs(self) -> dict:
        configs = super().export_configs()
        configs.update(
            {
                "pivots": self.pivots.export_configs(),
                "atr": self.atr.export_configs(),
                "max_candidates": self.max_candidates,
                "atr_median_lookback": self.atr_median_lookback,
                "radius_factor": self.radius_factor,
                "min_radius_mult": self.min_radius_mult,
                "max_radius_mult": self.max_radius_mult,
                "merge_nearby": self.merge_nearby,
                "merge_interval_bars": self.merge_interval_bars,
                "width_mult": self.width_mult,
                "fallback_width_factor": self.fallback_width_factor,
                "max_zone_touches": self.max_zone_touches,
                "max_zone_breaks": self.max_zone_breaks,
                "zone_break_bars": self.zone_break_bars,
                "min_bars_between_touches": self.min_bars_between_touches,
                "max_bars_between_touches": self.max_bars_between_touches,
                "prune_after_bars": self.prune_after_bars,
                "max_stored_zones": self.max_stored_zones,
            }
        )
        return configs

    # --- PURE HELPERS ---------------------------------

    @staticmethod
    def _clamp(x: float, lo: float, hi: float) -> float:
        return max(min(x, hi), lo)

    # --- ZONE POOL MANAGEMENT -------------------------

    def _add_new_zone(
        self, is_support: bool, price: float, index: int, candle: Candle, width: float
    ) -> ZoneModel:
        new_zone = ZoneModel(
            is_support=is_support,
            center=price,
            width=width,
            base_index=index,
            base_candle=candle,
            last_touch_index=index,
            last_touch_candle=candle,
        )
        self._zones.append(new_zone)
        logger.debug(f"new zone added: {new_zone}")
        return new_zone

    def _merge_overlapping_zones(self, bar_index: int):
        if not self.merge_nearby:
            return
        n = len(self._zones)
        for i in range(n - 1):
            zi = self._zones[i]
            if zi.invalidated_index is not None:
                continue
            for j in range(i + 1, n):
                zj = self._zones[j]
                if zj.invalidated_index is not None or zi.is_support != zj.is_support:
                    continue
                overlaps = zi.lower <= zj.upper and zj.lower <= zi.upper
                if not overlaps:
                    continue

                zi.sum_price += zj.sum_price
                zi.member_count += zj.member_count
                zi.center = zi.sum_price / zi.member_count
                zi.width = max(zi.width, zj.width)
                zi.touch_count += zj.touch_count
                zi.break_count = max(zi.break_count, zj.break_count)
                zi.max_touch_gap = max(zi.max_touch_gap, zj.max_touch_gap)
                if zj.base_index < zi.base_index:
                    zi.base_index = zj.base_index
                    zi.base_candle = zj.base_candle
                if zj.last_touch_index > zi.last_touch_index:
                    zi.last_touch_index = zj.last_touch_index
                    zi.last_touch_candle = zj.last_touch_candle
                zj.invalidated_index = bar_index
                zj.invalidated_candle = self.candles[bar_index]

    def _prune_zones(self, bar_index: int):
        self._zones = [
            z
            for z in self._zones
            if z.invalidated_index is None or (bar_index - z.invalidated_index) <= self.prune_after_bars
        ]

    def _enforce_storage_cap(self):
        # FIFO cap: `self._zones` is chronologically ordered by creation
        # (new zones are always appended in `_add_new_zone`), so once a
        # new zone pushes the count over the cap, drop the oldest zone(s)
        # from the front to make room and keep at most `max_stored_zones`
        # in total.
        excess = len(self._zones) - self.max_stored_zones
        if excess <= 0:
            return
        self._zones = self._zones[excess:]

    def _rebase(self, shift: int):
        """
        The candles window shifted forward by `shift` bars (that many
        candles fell off the front since the last call). Every previously
        recorded position needs to move back by the same amount so it
        still points at the same real candle in the new window.
        """
        for zone in self._zones:
            zone.base_index -= shift
            zone.last_touch_index -= shift
            if zone.invalidated_index is not None:
                zone.invalidated_index -= shift

        self._pivot_log = [
            replace(p, index=p.index - shift, confirmed_index=p.confirmed_index - shift)
            for p in self._pivot_log
        ]

        if self._last_confirmed_bar_index is not None:
            self._last_confirmed_bar_index -= shift
        if self._last_processed_confirm_index is not None:
            self._last_processed_confirm_index -= shift

    # --- PIVOT PROCESSING ------------------------------

    def _process_new_pivot(self, pivot: PivotPoint, base_radius: float, median_atr: float):
        is_support = not pivot.is_high
        matched = False

        for zone in self._zones:
            if zone.invalidated_index is not None or zone.is_support != is_support:
                continue
            if abs(pivot.price - zone.center) > base_radius:
                continue

            gap = pivot.index - zone.last_touch_index
            if gap < self.min_bars_between_touches:
                # same-swing noise: claim the pivot but don't count it
                matched = True
                break
            elif gap > self.max_bars_between_touches:
                zone.invalidated_index = pivot.index
                zone.invalidated_candle = pivot.candle
                # not matched -> keep scanning other zones, or seed fresh below
                continue
            else:
                zone.max_touch_gap = max(zone.max_touch_gap, gap)
                zone.member_count += 1
                zone.sum_price += pivot.price
                zone.center = zone.sum_price / zone.member_count
                zone.touch_count += 1
                zone.last_touch_index = pivot.index
                zone.last_touch_candle = pivot.candle
                new_width = max(zone.width, abs(pivot.price - zone.center) * self.width_mult)
                zone.width = self._clamp(new_width, 0.1 * median_atr, 2 * base_radius)
                matched = True
                break

        if not matched:
            fallback_width = self._clamp(
                self.fallback_width_factor * base_radius, 0.1 * median_atr, 2 * base_radius
            )
            self._add_new_zone(is_support, pivot.price, pivot.index, pivot.candle, fallback_width)

    def _check_zone_breaks(self, candle: Candle, bar_index: int):
        for zone in self._zones:
            if zone.invalidated_index is not None:
                continue
            if (bar_index - zone.last_touch_index) > self.max_bars_between_touches:
                zone.invalidated_index = bar_index
                zone.invalidated_candle = candle
                continue

            in_band = zone.lower <= candle.close <= zone.upper
            broke_now = candle.close < zone.lower if zone.is_support else candle.close > zone.upper
            zone.consec_break = zone.consec_break + 1 if broke_now else 0

            if zone.consec_break == 1:
                gap = bar_index - zone.last_touch_index
                if gap < self.min_bars_between_touches:
                    pass
                elif gap > self.max_bars_between_touches:
                    zone.invalidated_index = bar_index
                    zone.invalidated_candle = candle
                else:
                    zone.touch_count += 1
                    zone.last_touch_index = bar_index
                    zone.last_touch_candle = candle

            if zone.invalidated_index is None and zone.consec_break >= self.zone_break_bars:
                zone.break_count += 1
                zone.consec_break = 0
                if zone.break_count >= self.max_zone_breaks or zone.touch_count >= self.max_zone_touches:
                    zone.invalidated_index = bar_index
                    zone.invalidated_candle = candle
                else:
                    # zone survives this break: classic S/R role reversal
                    # -- a broken support acts as resistance from here on
                    # (and vice versa). Only reachable when
                    # `max_zone_breaks > 1` lets a zone live past its
                    # first break at all.
                    zone.is_support = not zone.is_support
                    zone.polarity_segments.append((candle, zone.is_support))

            if zone.invalidated_index is None and in_band and not zone.was_in_band:
                gap = bar_index - zone.last_touch_index
                if gap < self.min_bars_between_touches:
                    pass
                elif gap > self.max_bars_between_touches:
                    zone.invalidated_index = bar_index
                    zone.invalidated_candle = candle
                else:
                    zone.touch_count += 1
                    zone.last_touch_index = bar_index
                    zone.last_touch_candle = candle
                    if zone.touch_count >= self.max_zone_touches:
                        zone.invalidated_index = bar_index
                        zone.invalidated_candle = candle

            zone.was_in_band = in_band

    # --- SCORING ---------------------------------------

    def _compute_scores(self, bar_index: int, med_pivot_spacing: float):
        for zone in self._zones:
            age_bars = bar_index - zone.base_index
            age_comp = 1 - math.exp(-age_bars / max(1.0, med_pivot_spacing))
            touch_comp = math.log(1 + zone.touch_count)
            zone.raw_score = (touch_comp**0.5) * (max(age_comp, 0.001) ** 0.5)

    def _percentile_filter(self):
        scores = [z.raw_score for z in self._zones]
        n = len(scores)
        for zone in self._zones:
            if n <= 1:
                zone.score_pct = 50.0
                continue
            below = sum(1 for s in scores if s < zone.raw_score)
            zone.score_pct = 100.0 * below / (n - 1)

    # --- MAIN CALCULATION (mirrors PER-BAR + PER-REFRESH Pine sections) --

    def _process_bar(self, i: int, candle: Candle, pivots_by_confirm_index: dict[int, list[PivotPoint]]):
        atr_value = self.atr.data.get(candle.timestamp)
        if atr_value is not None:
            self._atr_buf.append(atr_value)
            if len(self._atr_buf) > self.atr_median_lookback:
                self._atr_buf.pop(0)
        if self._atr_buf:
            self._median_atr = median(self._atr_buf)
            raw_radius = self._median_atr * self.radius_factor
            self._base_radius = self._clamp(
                raw_radius, self.min_radius_mult * self._median_atr, self.max_radius_mult * self._median_atr
            )
        self._last_median_atr = self._median_atr or 0.0
        self._last_base_radius = self._base_radius or 0.0

        for pivot in pivots_by_confirm_index.get(i, []):
            self._pivot_log.append(pivot)
            if len(self._pivot_log) > self.max_candidates:
                self._pivot_log.pop(0)

            if self._base_radius is not None and self._median_atr is not None:
                self._process_new_pivot(pivot, self._base_radius, self._median_atr)

            if self._last_confirmed_bar_index is not None:
                gap = pivot.index - self._last_confirmed_bar_index
                if gap > 0:
                    self._pivot_gaps.append(gap)
                    if len(self._pivot_gaps) > 10:
                        self._pivot_gaps.pop(0)
            self._last_confirmed_bar_index = pivot.index
            if self._pivot_gaps:
                self._med_pivot_spacing = median(self._pivot_gaps)

            if self._last_processed_confirm_index is None or pivot.confirmed_index > self._last_processed_confirm_index:
                self._last_processed_confirm_index = pivot.confirmed_index

        if self._base_radius is not None:
            self._check_zone_breaks(candle, i)
            if i % self.merge_interval_bars == 0:
                self._merge_overlapping_zones(i)
                self._prune_zones(i)

    def _finalize(self, last_index: int) -> list[ZoneModel]:
        # one more merge/prune pass regardless of the mod-`merge_interval_bars`
        # cadence, so nothing overlapping is ever left in the returned data.
        self._merge_overlapping_zones(last_index)
        self._prune_zones(last_index)

        self._compute_scores(last_index, self._med_pivot_spacing)
        self._enforce_storage_cap()
        self._percentile_filter()

        return self._zones

    def _new_pivots_by_confirm_index(self) -> dict[int, list[PivotPoint]]:
        pivots_by_confirm_index: dict[int, list[PivotPoint]] = {}
        for pivot in self.pivots.data:
            if self._last_processed_confirm_index is not None and pivot.confirmed_index <= self._last_processed_confirm_index:
                continue
            pivots_by_confirm_index.setdefault(pivot.confirmed_index, []).append(pivot)
        return pivots_by_confirm_index

    def _calculate(self) -> list[ZoneModel]:
        candles = self.candles
        n = len(candles)
        if n < self.pivots.depth + 2:
            return []

        self.pivots.set(candles)
        self.atr.set(candles)

        self._zones = []
        self._pivot_log = []
        self._atr_buf = []
        self._pivot_gaps = []
        self._last_confirmed_bar_index = None
        self._med_pivot_spacing = 20.0
        self._median_atr = None
        self._base_radius = None
        self._last_processed_confirm_index = None

        pivots_by_confirm_index = self._new_pivots_by_confirm_index()

        for i, candle in enumerate(candles):
            self._process_bar(i, candle, pivots_by_confirm_index)

        self._last_checked_index = n - 1
        return self._finalize(n - 1)

    def _forcast(self) -> MarketSide:
        return MarketSide.NEUTRAL

    # --- DISPLAY ---------------------------------------

    def plot(
        self,
        plot: ChartPlot,
        min_score_percentile: float = 0.0,
        max_zones_display: int | None = 8,
        proximity_boost: float = 0.3,
        support_color: str = "#00808040",
        resist_color: str = "#ff000040",
        flip_marker_color: str = "#ffff00d0",
        show_labels: bool = True,
        show_live: bool = True,
    ):
        if not self.candles:
            return

        end_time = self.candles[-1].time
        close = self.candles[-1].close
        median_atr = self._last_median_atr or 1e-9

        candidates = [z for z in self.data if z.score_pct >= min_score_percentile]

        def priority(zone: ZoneModel) -> float:
            prox = math.exp(-abs(close - zone.center) / max(median_atr, 1e-9))
            return zone.score_pct * (1 + proximity_boost * prox)

        candidates.sort(key=priority, reverse=True)
        candidates = candidates if max_zones_display is None else candidates[:max_zones_display]

        # `ChartPlot.plot()` trims its own candles down to `plot_n_candles`
        # (default 100) the first time `plot.ax` is touched -- accessing it
        # here (before drawing anything) guarantees that trim has already
        # happened, so `plot.give_chartdata()` reflects the window that
        # will actually be visible in the sent image.
        _ = plot.ax
        visible_candles = plot.give_chartdata().candles
        earliest_visible_time = (
            visible_candles[0].time if visible_candles else self.candles[0].time
        )

        for rank, zone in enumerate(candidates):
            zone_end = (
                zone.invalidated_candle.time
                if zone.invalidated_candle is not None
                else end_time
            )

            # A zone can flip role mid-life (`max_zone_breaks > 1` lets it
            # survive a break instead of being invalidated by it, and a
            # broken support conventionally starts acting as resistance
            # from that point on, and vice versa). `polarity_segments`
            # holds one (candle, is_support) entry per stretch of the
            # zone's life; draw each stretch as its own rect in its own
            # color so a flip actually shows up in the image, instead of
            # silently drawing the whole box in whatever `is_support`
            # happens to be right now.
            for seg_index, (seg_candle, seg_is_support) in enumerate(zone.polarity_segments):
                seg_end = (
                    zone.polarity_segments[seg_index + 1][0].time
                    if seg_index + 1 < len(zone.polarity_segments)
                    else zone_end
                )
                # Same reasoning as the single-segment case used to have:
                # don't draw past the left edge of the visible image.
                seg_start = max(seg_candle.time, earliest_visible_time)
                color = support_color if seg_is_support else resist_color
                plot.draw_filled_rect(seg_start, seg_end, zone.upper, zone.lower, color)

            # explicit marker at every flip point, so the role-reversal is
            # visible even where the two segment colors are hard to tell
            # apart at a glance (e.g. thumbnail size on a phone screen)
            for seg_candle, _ in zone.polarity_segments[1:]:
                flip_time = max(seg_candle.time, earliest_visible_time)
                plot.draw_line(
                    flip_time, zone.lower, flip_time, zone.upper,
                    color=flip_marker_color, width=2,
                )

            if show_labels and rank < 3:
                status = " [INVALID]" if zone.broken else ""
                flip_note = f" [FLIPPED x{len(zone.polarity_segments) - 1}]" if zone.flipped else ""
                logger.info(
                    f"{'Support' if zone.is_support else 'Resist'} "
                    f"score:{zone.score_pct:.0f} touch:{zone.touch_count} "
                    f"break:{zone.break_count}{status}{flip_note}"
                )

        if show_live:
            for pivot in self.pivots.live_pivots:
                is_support = not pivot.is_high
                # only draw the live-test line when price is genuinely
                # inside a zone that's actually shown in this image --
                # matching purely on "nearest zone of the right side" (the
                # old behavior) picked whatever zone was geometrically
                # closest even when price was nowhere near it, which is
                # why a dashed line could show up cutting through the
                # middle of an unrelated zone's box.
                zone = next(
                    (
                        z for z in candidates
                        if z.is_support == is_support and z.lower <= pivot.price <= z.upper
                    ),
                    None,
                )
                if zone is None:
                    continue
                zone_start = max(zone.base_candle.time, earliest_visible_time)
                plot.draw_horizontal_line(zone_start, end_time, zone.center, "#ffffff80")

    def update(self, candles: list[Candle], *args, **kwargs) -> list[ZoneModel]:
        if self.last_checked_candle is None:
            raise ValueError("last_checked_candle is None")

        start_index = self.find_new_candle_index(candles)
        if start_index >= len(candles):
            return self.data

        # position of the last-seen candle in the NEW window vs where it
        # was recorded last time -> how far the window has slid forward.
        # Must rebase BEFORE touching self.pivots/self.atr or computing
        # anything below, since everything downstream compares against
        # these stored indices.
        shift = self._last_checked_index - (start_index - 1)
        if shift > 0:
            self._rebase(shift)

        self.candles = candles
        self.pivots.update(candles)
        self.atr.update(candles)

        pivots_by_confirm_index = self._new_pivots_by_confirm_index()

        for i in range(start_index, len(candles)):
            self._process_bar(i, candles[i], pivots_by_confirm_index)

        self.data = self._finalize(len(candles) - 1)
        self.last_checked_candle = candles[-1]
        self._last_checked_index = len(candles) - 1
        return self.data
