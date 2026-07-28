from ChartModule.models import Candle, MarketSide
from ChartModule.Indicators.models import IndicatorBaseModel
from ChartModule.plot import ChartPlot
from SRZoneModule.swing_pivots import SwingPivots, PivotPoint
from SRZoneModule.atr import ATR
from dataclasses import dataclass, field
from statistics import median
import logging
import math


logger = logging.getLogger("SRZones")


@dataclass(slots=True)
class ZoneModel:
    """
    A single auto-detected support/resistance zone (candidate/active/archived).

    is_support: True  -> built from swing Lows (support, sits below price)
                False -> built from swing Highs (resistance, sits above price)

    Field names mirror the Pine reference's `Zone` UDT 1:1 (center, width,
    sum_price, member_count, touch_count, break_count, consec_break,
    was_in_band, max_touch_gap, raw_score, score_pct) so the two can be
    read side by side. `invalidated_index` is Pine's `invalidBar` — None
    while still valid, exactly like Pine's `na`.
    """

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

    def __post_init__(self):
        self.sum_price = self.center

    @property
    def upper(self) -> float:
        return self.center + self.width

    @property
    def lower(self) -> float:
        return self.center - self.width

    @property
    def broken(self) -> bool:
        return self.invalidated_index is not None

    def __str__(self) -> str:
        side = "Support" if self.is_support else "Resistance"
        return (
            f"{side}|center={self.center:.5f}|touch={self.touch_count}"
            f"|break={self.break_count}|broken={self.broken}|score={self.score_pct:.1f}"
        )


class SRZones(IndicatorBaseModel):
    """
    Support & Resistance Zone Engine (ATR Adaptive)  --  faithful port of the
    "S/R Zone Engine [ZigZag Pivots]" (v2, FIXED) Pine Script indicator.

    Structured like AutoTrendlineModule.auto_trendline.AutoTrendlines on
    purpose (same pivot source: SwingPivots -- causal, no Deviation input,
    same as this project's AutoTrendlines; same ATR source: ATR), but every
    knob and every rule from the Pine version is reproduced, not just the
    shape:

      - Pivot Detection: `depth`/`backstep`; `max_candidates` bounds an
        internal pivot log the same way `i_maxCandidates` bounds Pine's
        `g_candidates`/`g_zoneUsedBar` arrays (Python doesn't need the
        dedup array Pine used -- SwingPivots hands each pivot exactly once
        -- so this only bounds the log kept for parity/debugging).
      - Adaptive Radius: `atr_len` + `atr_median_lookback` -> a ROLLING
        MEDIAN of ATR (not raw ATR), then `radius_factor` scales it and
        `min_radius_mult`/`max_radius_mult` clamp it -> `base_radius`.
        This is Pine's `medianATR` / `baseRadius` exactly; the earlier
        version of this port skipped the median + clamp entirely.
      - Clustering: `merge_nearby`, `merge_interval_bars` (Pine hardcodes
        this at 300 via `bar_index % 300 == 0`; exposed here instead of
        hardcoded, per completeness).
      - Zone Width: `width_mult` and the `0.1*medianATR .. 2*base_radius`
        clamp Pine applies both when extending a zone AND when seeding a
        new one via `fallback_width_factor` (was missing entirely before).
      - Zone Score: `max_zone_touches`, `max_zone_breaks`, `zone_break_bars`
        are THREE SEPARATE Pine inputs, not one. A zone survives up to
        `max_zone_breaks - 1` break events (each needing `zone_break_bars`
        consecutive closes outside it) before it's actually invalidated --
        the earlier version invalidated on the very first break, collapsing
        all three into one knob. Score itself is Pine's exact two-factor
        formula (touch count + age vs. median pivot spacing), rank-
        percentiled across all zones (`raw_score` / `score_pct`), computed
        once at the end -- not the simplified `touches*100+age` linear
        stand-in used before.
      - Touch Spacing: `min_bars_between_touches`/`max_bars_between_touches`
        gate BOTH new-pivot touches (`f_updateZones`) and per-bar break/
        band-entry touches (`f_checkZoneBreaks`) -- same gate, same field
        (`zone.last_touch_index`), exactly like the Pine version's headline
        fix ("touchCount was being incremented from two independent paths").
      - Merge: Pine always merges the OLDER zone <- newer zone (array order,
        i<j), in a full pass that can chain multiple merges into the same
        target within one call, and marks the loser `invalidBar` (kept, not
        deleted) rather than removing it. The earlier version merged
        "whichever has more touches" and permanently `list.remove()`'d the
        loser after at most one merge per call -- both fixed here.
      - Pivot matching (`f_updateZones`): Pine takes the FIRST same-side
        zone within radius in array (= chronological) order, not the
        nearest one, and -- if a matched zone gets invalidated by the max-
        gap rule -- keeps scanning for another candidate before giving up
        and seeding a new zone. The earlier version picked nearest-by-
        distance and gave up immediately on a gap violation. Fixed here.
      - Display: `plot()` now reproduces Pine's per-refresh selection block
        -- filter by `min_score_percentile`, rank by
        `score_pct * (1 + proximity_boost * exp(-|close-center|/medianATR))`,
        keep the top `max_zones_display`, draw ALL of them (valid or
        invalid -- Pine never hides invalid zones, it just renders them more
        transparent with an "[INVALID]" tag), colored by `support_color`/
        `resist_color`. Two Pine-only pieces have no real equivalent here
        and are called out rather than silently dropped:
          * `f_safeBar` clamps box coordinates because Pine's renderer
            rejects bar_index more than ~10000 bars from the current bar.
            finplot draws on real timestamps, not bar-index offsets, so
            there is no such limit and nothing to clamp.
          * Pine's `label.new` draws free-floating text; `ChartPlot` has no
            equivalent primitive (only line/candle/signal markers), so the
            top-3 "info labels" (`i_showLabels`) are emitted via
            `logger.info` instead of drawn on the chart.

    Repaint: `SwingPivots.live_pivots` (the still-forming, unconfirmed
    extreme) is exposed as-is and previewed in `plot(show_live=...)` against
    the nearest same-side zone -- display only, it never mutates a
    `ZoneModel`, exactly like Pine's live tip never touches touchCount/score.

    values: list[ZoneModel]
    """

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

        self._zones: list[ZoneModel] = []
        self._pivot_log: list[PivotPoint] = []
        self._last_median_atr: float = 0.0
        self._last_base_radius: float = 0.0

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
        """
        Mirrors Pine's f_mergeZonesNew exactly: a full pass, older zone
        (lower array index) always absorbs newer overlapping same-side
        zones, can chain multiple merges into the same target within one
        call, and the loser is marked invalidated (kept for history/prune)
        rather than removed outright.
        """
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

    def _prune_zones(self, bar_index: int):
        """mirrors f_pruneZones: drop zones invalidated more than `prune_after_bars` ago"""
        self._zones = [
            z
            for z in self._zones
            if z.invalidated_index is None or (bar_index - z.invalidated_index) <= self.prune_after_bars
        ]

    # --- PIVOT PROCESSING ------------------------------

    def _process_new_pivot(self, pivot: PivotPoint, base_radius: float, median_atr: float):
        """
        Mirrors f_updateZones exactly: scan zones in (chronological) array
        order, take the FIRST same-side zone within `base_radius` -- not the
        nearest one. If that zone fails the max-gap rule it gets invalidated
        on the spot and the scan CONTINUES to the next candidate, rather
        than immediately giving up and seeding a new zone.
        """
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
        """mirrors f_checkZoneBreaks exactly, including its two-separate-`if` gating order"""
        for zone in self._zones:
            if zone.invalidated_index is not None:
                continue
            if (bar_index - zone.last_touch_index) > self.max_bars_between_touches:
                zone.invalidated_index = bar_index
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
                else:
                    zone.touch_count += 1
                    zone.last_touch_index = bar_index
                    zone.last_touch_candle = candle

            if zone.invalidated_index is None and zone.consec_break >= self.zone_break_bars:
                zone.break_count += 1
                zone.consec_break = 0
                if zone.break_count >= self.max_zone_breaks or zone.touch_count >= self.max_zone_touches:
                    zone.invalidated_index = bar_index

            if zone.invalidated_index is None and in_band and not zone.was_in_band:
                gap = bar_index - zone.last_touch_index
                if gap < self.min_bars_between_touches:
                    pass
                elif gap > self.max_bars_between_touches:
                    zone.invalidated_index = bar_index
                else:
                    zone.touch_count += 1
                    zone.last_touch_index = bar_index
                    zone.last_touch_candle = candle
                    if zone.touch_count >= self.max_zone_touches:
                        zone.invalidated_index = bar_index

            zone.was_in_band = in_band

    # --- SCORING ---------------------------------------

    def _compute_scores(self, bar_index: int, med_pivot_spacing: float):
        """mirrors f_computeZoneScore: touches + age (vs. median pivot spacing), sqrt-blended"""
        for zone in self._zones:
            age_bars = bar_index - zone.base_index
            age_comp = 1 - math.exp(-age_bars / max(1.0, med_pivot_spacing))
            touch_comp = math.log(1 + zone.touch_count)
            zone.raw_score = (touch_comp**0.5) * (max(age_comp, 0.001) ** 0.5)

    def _percentile_filter(self):
        """mirrors f_percentileFilterZones: rank-percentile raw_score across all zones"""
        scores = [z.raw_score for z in self._zones]
        n = len(scores)
        for zone in self._zones:
            if n <= 1:
                zone.score_pct = 50.0
                continue
            below = sum(1 for s in scores if s < zone.raw_score)
            zone.score_pct = 100.0 * below / (n - 1)

    # --- MAIN CALCULATION (mirrors PER-BAR + PER-REFRESH Pine sections) --

    def _calculate(self) -> list[ZoneModel]:
        candles = self.candles
        n = len(candles)
        if n < self.pivots.depth + 2:
            return []

        self.pivots.set(candles)
        self.atr.set(candles)

        pivots_by_confirm_index: dict[int, list[PivotPoint]] = {}
        for pivot in self.pivots.data:
            pivots_by_confirm_index.setdefault(pivot.confirmed_index, []).append(pivot)

        self._zones = []
        self._pivot_log = []

        atr_buf: list[float] = []
        pivot_gaps: list[int] = []
        last_confirmed_index: int | None = None
        med_pivot_spacing = 20.0
        median_atr: float | None = None
        base_radius: float | None = None

        for i, candle in enumerate(candles):
            atr_value = self.atr.data.get(candle.timestamp)
            if atr_value is not None:
                atr_buf.append(atr_value)
                if len(atr_buf) > self.atr_median_lookback:
                    atr_buf.pop(0)
            if atr_buf:
                median_atr = median(atr_buf)
                raw_radius = median_atr * self.radius_factor
                base_radius = self._clamp(
                    raw_radius, self.min_radius_mult * median_atr, self.max_radius_mult * median_atr
                )
            self._last_median_atr = median_atr or 0.0
            self._last_base_radius = base_radius or 0.0

            for pivot in pivots_by_confirm_index.get(i, []):
                self._pivot_log.append(pivot)
                if len(self._pivot_log) > self.max_candidates:
                    self._pivot_log.pop(0)

                if base_radius is not None and median_atr is not None:
                    self._process_new_pivot(pivot, base_radius, median_atr)

                if last_confirmed_index is not None:
                    gap = pivot.index - last_confirmed_index
                    if gap > 0:
                        pivot_gaps.append(gap)
                        if len(pivot_gaps) > 10:
                            pivot_gaps.pop(0)
                last_confirmed_index = pivot.index
                if pivot_gaps:
                    med_pivot_spacing = median(pivot_gaps)

            if base_radius is not None:
                self._check_zone_breaks(candle, i)
                if i % self.merge_interval_bars == 0:
                    self._merge_overlapping_zones(i)
                    self._prune_zones(i)

        last_index = n - 1
        self._compute_scores(last_index, med_pivot_spacing)
        self._percentile_filter()

        return self._zones

    def _forcast(self) -> MarketSide:
        return MarketSide.NEUTRAL

    # --- DISPLAY ---------------------------------------

    def _nearest_zone(self, price: float, is_support: bool) -> ZoneModel | None:
        """
        Display-only nearest-zone lookup for the live/repaint preview. Not
        used anywhere in `_calculate` -- Pine has no equivalent lookup for a
        real pivot (see `_process_new_pivot`'s first-in-array-order rule);
        "nearest" is simply the more sensible choice for a plain preview.
        """
        best: ZoneModel | None = None
        best_dist: float | None = None
        for zone in self._zones:
            if zone.invalidated_index is not None or zone.is_support != is_support:
                continue
            dist = abs(price - zone.center)
            if best_dist is None or dist < best_dist:
                best, best_dist = zone, dist
        return best

    def plot(
        self,
        plot: ChartPlot,
        min_score_percentile: float = 0.0,
        max_zones_display: int | None = 8,
        proximity_boost: float = 0.3,
        support_color: str = "#008080",
        resist_color: str = "#ff0000",
        show_labels: bool = True,
        show_live: bool = True,
    ):
        """
        Mirrors Pine's PER-REFRESH display block: filter by
        `min_score_percentile`, rank by
        score_pct * (1 + proximity_boost * exp(-|close-center|/medianATR)),
        keep the top `max_zones_display` (pass `None` for no cap -- shows
        every zone in `self.data`, which was never capped to begin with;
        only this display step was). Invalid zones are NOT hidden --
        Pine never hides them either, it just renders them more transparent
        with an "[INVALID]" tag; here that distinction is approximated by
        logging (see class docstring for why: no text-label primitive).

        Pine extends a still-valid zone's box 25 bars into blank future
        space (`bar_index + 25`) because its renderer can draw past the
        last actual bar. finplot cannot -- `fplt.add_line` resolves a time
        to an x-position via the ALREADY-PLOTTED candle series, so a
        timestamp past `self.candles[-1].time` has nothing to resolve to
        and raises `IndexError` deep inside finplot. Every other line-
        drawing indicator in this project (e.g. AutoTrendlines, whose
        `end_candle` is always a real candle, never extrapolated) avoids
        this the same way: still-valid zones are drawn out to the real
        last candle's time, not a synthetic future one.
        """
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

        for rank, zone in enumerate(candidates):
            color = support_color if zone.is_support else resist_color
            zone_end = (
                self.candles[zone.invalidated_index].time
                if zone.invalidated_index is not None
                else end_time
            )
            plot.draw_horizontal_line(zone.base_candle.time, zone_end, zone.upper, color)
            plot.draw_horizontal_line(zone.base_candle.time, zone_end, zone.lower, color)

            if show_labels and rank < 3:
                status = " [INVALID]" if zone.broken else ""
                logger.info(
                    f"{'Support' if zone.is_support else 'Resist'} "
                    f"score:{zone.score_pct:.0f} touch:{zone.touch_count} "
                    f"break:{zone.break_count}{status}"
                )

        if show_live:
            for pivot in self.pivots.live_pivots:
                is_support = not pivot.is_high
                zone = self._nearest_zone(pivot.price, is_support)
                if zone is None:
                    continue
                plot.draw_horizontal_line(zone.base_candle.time, end_time, zone.center, "#ffffff80")

    def update(self, candles: list[Candle], *args, **kwargs):
        pass
