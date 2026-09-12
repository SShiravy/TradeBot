from typing import Literal

from ChartModule.models import Candle, MarketSide, CandlesSource, TimeFrame
from ChartModule.Indicators.models import IndicatorBaseModel
from ChartModule.Indicators.lines import Line
from ChartModule.plot import ChartPlot
from ChartModule.Indicators.swing_pivots import SwingPivots, PivotPoint
from ChartModule.Indicators.atr import ATR
from dataclasses import dataclass, field, replace
from enum import Enum
import logging


logger = logging.getLogger("AutoTrendlines")


class BreakLogicMode(Enum):
    ATR_DISTANCE = "ATR Distance"
    CANDLE_CLOSE = "Candle Close"
    CLOSE_CROSS = "Close Cross"


@dataclass(slots=True, frozen=True)
class MTREvent:
    candle: Candle
    bullish: bool
    count: int

    @property
    def text(self) -> str:
        if self.count < 2:
            return "MTR"
        suffix = self.count - 1
        return f"MTR{suffix}+" if suffix > 1 else "MTR+"

    def __str__(self) -> str:
        return (
            f"{self.text}|{'bullish' if self.bullish else 'bearish'}|{self.candle.time}"
        )


@dataclass(slots=True)
class TrendlineModel:
    side: Literal[MarketSide.BEARISH, MarketSide.BULLISH]
    source: CandlesSource
    base_index: int
    base_candle: Candle
    slope: float
    group_slope: float
    score: int
    last_touch_index: int
    last_touch_candle: Candle
    aligned_only: bool

    end_candle: Candle = field(init=False)
    broken: bool = field(default=False, init=False)
    confirm_count: int = field(default=0, init=False)

    def __post_init__(self):
        self.end_candle = self.base_candle

    @property
    def base_price(self) -> float:
        return self.source(self.base_candle)

    def value_at(self, timestamp: float) -> float:
        return self.base_price + self.slope * (timestamp - self.base_candle.timestamp)

    def as_line(self) -> Line:
        return Line(self.source, self.base_candle, self.end_candle)

    @property
    def role(self) -> MarketSide:
        if self.aligned_only:
            return self.side
        return MarketSide.BULLISH if self.slope > 0 else MarketSide.BEARISH

    @property
    def is_support(self) -> bool:
        return self.role is MarketSide.BULLISH

    @property
    def is_resistance(self) -> bool:
        return self.role is MarketSide.BEARISH

    def __str__(self) -> str:
        return (
            f"{self.side}|base={self.base_candle.time}"
            f"|broken={self.broken}|score={self.score}"
        )


class AutoTrendlines(IndicatorBaseModel):
    def __init__(
        self,
        depth: int = 12,
        backstep: int = 2,
        atr_len: int = 14,
        touch_mult: float = 0.15,
        break_mult: float = 0.40,
        min_touches: int = 3,
        min_line_bars: int = 15,
        max_span_bars: int = 2000,
        max_stored_pivots: int = 60,
        max_active_per_dir: int = 4,
        max_total_lines: int = 200,
        stale_bars: int = 50,
        merge_projection_bars: int = 50,
        display_only_aligned: bool = True,
        keep_archived: bool = True,
        break_logic_mode: BreakLogicMode = BreakLogicMode.ATR_DISTANCE,
        candle_confirm_count: int = 2,
        max_stored_mtr_events: int = 300,
    ) -> None:
        super().__init__()
        self.data: list[TrendlineModel]
        self.mtr_events: list[MTREvent] = []

        self.pivots = SwingPivots(depth, backstep)
        self.atr = ATR(atr_len)

        self.touch_mult = touch_mult
        self.break_mult = break_mult
        self.min_touches = min_touches
        self.min_line_bars = min_line_bars
        self.max_span_bars = max_span_bars
        self.max_stored_pivots = max_stored_pivots
        self.max_active_per_dir = max_active_per_dir
        self.max_total_lines = max_total_lines
        self.stale_bars = stale_bars
        self.merge_projection_bars = merge_projection_bars
        self.display_only_aligned = display_only_aligned
        self.keep_archived = keep_archived
        self.break_logic_mode = break_logic_mode
        self.candle_confirm_count = candle_confirm_count
        self.max_stored_mtr_events = max_stored_mtr_events

        self._pivot_highs: list[PivotPoint] = []
        self._pivot_lows: list[PivotPoint] = []
        self._lines: list[TrendlineModel] = []

        # `candles` passed into set()/update() is a SLIDING WINDOW (each
        # poll refetches the last `n_candle_check` candles), not an
        # append-only array -- older candles keep falling off the front.
        # `TrendlineModel.base_index`/`last_touch_index` and the indices
        # stored on the pooled pivots in `_pivot_highs`/`_pivot_lows` are
        # all positions WITHIN that window, so they go stale by exactly
        # the number of candles that fell off the front since they were
        # recorded -- and since they're never adjusted, they only ever
        # grow relatively "too large", which is how `_merge_similar_lines`
        # indexing `self.candles[ref_index]` with one of these can
        # eventually run past the end of the (unchanged-length) window.
        # `_last_checked_index` remembers where the last-seen candle sat
        # in the window last time, so `update()` can measure that drift
        # and `_rebase()` everything before doing anything else.
        self._last_checked_index: int = 0

    def export_configs(self) -> dict:
        configs = super().export_configs()
        configs.update(
            {
                "pivots": self.pivots.export_configs(),
                "atr": self.atr.export_configs(),
                "touch_mult": self.touch_mult,
                "break_mult": self.break_mult,
                "min_touches": self.min_touches,
                "min_line_bars": self.min_line_bars,
                "max_span_bars": self.max_span_bars,
                "max_stored_pivots": self.max_stored_pivots,
                "max_active_per_dir": self.max_active_per_dir,
                "max_total_lines": self.max_total_lines,
                "stale_bars": self.stale_bars,
                "merge_projection_bars": self.merge_projection_bars,
                "display_only_aligned": self.display_only_aligned,
                "break_logic_mode": self.break_logic_mode.value,
                "candle_confirm_count": self.candle_confirm_count,
            }
        )
        return configs

    # ─── VALIDATION ─────────────────────────────────

    def _validate_candidate(
        self,
        pivot_pool: list[PivotPoint],
        base_index: int,
        base_price: float,
        base_timestamp: float,
        slope: float,
        cur_index: int,
        is_low: bool,
        break_tol: float,
        touch_tol: float,
    ) -> tuple[int, int, int]:
        """mirrors f_validateLow / f_validateHigh"""
        violations = 0
        touches = 0
        max_gap = 0
        last_touch_index = cur_index

        for pivot in pivot_pool:
            if not (base_index <= pivot.index <= cur_index):
                continue
            line_value = base_price + slope * (pivot.candle.timestamp - base_timestamp)
            diff = pivot.price - line_value

            if is_low:
                if diff < -break_tol:
                    violations += 1
            else:
                if diff > break_tol:
                    violations += 1

            if abs(diff) <= touch_tol:
                touches += 1
                gap = last_touch_index - pivot.index
                if gap > max_gap:
                    max_gap = gap
                last_touch_index = pivot.index

        return violations, touches, max_gap

    # ─── LINE POOL MANAGEMENT ───────────────────────

    def _count_active(self, direction: MarketSide) -> int:
        return sum(
            1 for line in self._lines if not line.broken and line.side is direction
        )

    def _find_most_recent_active(self, direction: MarketSide) -> TrendlineModel | None:
        candidates = [
            line for line in self._lines if not line.broken and line.side is direction
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda line: line.base_index)

    def _find_weakest_active(self, direction: MarketSide) -> TrendlineModel | None:
        candidates = [
            line for line in self._lines if not line.broken and line.side is direction
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda line: line.score)

    def _enforce_max_total_lines(self):
        while len(self._lines) > self.max_total_lines:
            for i, line in enumerate(self._lines):
                if line.broken:
                    del self._lines[i]
                    break
            else:
                self._lines.pop(0)

    def _enforce_max_mtr_events(self):
        # `mtr_events` only ever grows via append in `_process_bar`, with
        # no eviction anywhere -- over a long-running bot this list would
        # otherwise accumulate forever. FIFO cap: keep the most recent
        # `max_stored_mtr_events`, drop the oldest.
        excess = len(self.mtr_events) - self.max_stored_mtr_events
        if excess > 0:
            del self.mtr_events[:excess]

    def _rebase(self, shift: int):
        """
        The candles window shifted forward by `shift` bars (that many
        candles fell off the front since the last call). Every previously
        recorded position needs to move back by the same amount so it
        still points at the same real candle in the new window.
        """
        for line in self._lines:
            line.base_index -= shift
            line.last_touch_index -= shift

        self._pivot_highs = [
            replace(p, index=p.index - shift, confirmed_index=p.confirmed_index - shift)
            for p in self._pivot_highs
        ]
        self._pivot_lows = [
            replace(p, index=p.index - shift, confirmed_index=p.confirmed_index - shift)
            for p in self._pivot_lows
        ]
        # `mtr_events` only ever stores a direct Candle reference (like
        # base_candle/last_touch_candle elsewhere), never a position
        # index, so nothing there needs rebasing.

    def _add_new_line(
        self,
        direction: Literal[MarketSide.BEARISH, MarketSide.BULLISH],
        base_index: int,
        base_candle: Candle,
        slope: float,
        score: int,
        touch_index: int,
        touch_candle: Candle,
    ):
        if self._count_active(direction) >= self.max_active_per_dir:
            weakest = self._find_weakest_active(direction)
            if weakest is not None:
                weakest.broken = True

        source = (
            CandlesSource.Low if direction is MarketSide.BULLISH else CandlesSource.High
        )
        new_line = TrendlineModel(
            side=direction,
            source=source,
            base_index=base_index,
            base_candle=base_candle,
            slope=slope,
            group_slope=slope,
            score=score,
            last_touch_index=touch_index,
            last_touch_candle=touch_candle,
            aligned_only=self.display_only_aligned,
        )
        self._lines.append(new_line)
        logger.debug(f"new trendline added: {new_line}")
        self._enforce_max_total_lines()

    def _try_merge_or_add(
        self,
        direction: Literal[MarketSide.BEARISH, MarketSide.BULLISH],
        base_index: int,
        base_candle: Candle,
        new_index: int,
        new_candle: Candle,
        candidate_slope: float,
        score: int,
        similar_tolerance: float,
        merge_projection_seconds: float,
    ):
        merge_target = self._find_most_recent_active(direction)
        merged = False

        if merge_target is not None:
            divergence = (
                abs(candidate_slope - merge_target.group_slope)
                * merge_projection_seconds
            )
            if divergence <= similar_tolerance:
                new_slope = (
                    merge_target.source(new_candle) - merge_target.base_price
                ) / (new_candle.timestamp - merge_target.base_candle.timestamp)
                slope_ok = not self.display_only_aligned or (
                    new_slope > 0 if direction is MarketSide.BULLISH else new_slope < 0
                )
                if slope_ok:
                    merge_target.slope = new_slope
                    merge_target.last_touch_index = new_index
                    merge_target.last_touch_candle = new_candle
                    merge_target.score += score
                    merge_target.confirm_count = 0
                    merged = True

        if not merged:
            self._add_new_line(
                direction,
                base_index,
                base_candle,
                candidate_slope,
                score,
                new_index,
                new_candle,
            )

    def _merge_similar_lines(self, current_candle: Candle, similar_tolerance: float):
        """mirrors f_mergeSimilarLines: drops (at most) one duplicate per call"""
        active = [line for line in self._lines if not line.broken]
        for i in range(len(active)):
            line_i = active[i]
            for j in range(i + 1, len(active)):
                line_j = active[j]
                if line_i.side is not line_j.side:
                    continue

                ref_index = max(line_i.base_index, line_j.base_index)
                ref_candle = self.candles[ref_index]

                d1 = abs(
                    line_i.value_at(ref_candle.timestamp)
                    - line_j.value_at(ref_candle.timestamp)
                )
                d2 = abs(
                    line_i.value_at(current_candle.timestamp)
                    - line_j.value_at(current_candle.timestamp)
                )
                if d1 <= similar_tolerance and d2 <= similar_tolerance:
                    weaker = line_i if line_i.score < line_j.score else line_j
                    self._lines.remove(weaker)
                    return

    # ─── PIVOT PROCESSING ────────────────────────────

    def _process_new_pivot(
        self,
        pivot: PivotPoint,
        cur_index: int,
        touch_tol: float,
        break_tol: float,
        similar_tolerance: float,
        merge_projection_seconds: float,
    ):
        pool = self._pivot_highs if pivot.is_high else self._pivot_lows
        pool.insert(0, pivot)
        if len(pool) > self.max_stored_pivots:
            pool.pop()

        if len(pool) < 2:
            return

        best_score = -1
        best_base: PivotPoint | None = None
        best_slope = 0.0

        for candidate in pool[1:]:
            span = cur_index - candidate.index
            if span < self.min_line_bars:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"candidate {'High' if pivot.is_high else 'Low'} "
                        f"base={candidate.candle.time}({candidate.price}) "
                        f"touch={pivot.candle.time}({pivot.price}) "
                        f"span={span}/{self.min_line_bars} -> rejected (span < min_line_bars)"
                    )
                continue

            slope = (pivot.price - candidate.price) / (
                pivot.candle.timestamp - candidate.candle.timestamp
            )

            violations, touches, max_gap = self._validate_candidate(
                pool,
                candidate.index,
                candidate.price,
                candidate.candle.timestamp,
                slope,
                cur_index,
                not pivot.is_high,
                break_tol,
                touch_tol,
            )

            aligned = True
            if self.display_only_aligned:
                aligned = slope < 0 if pivot.is_high else slope > 0

            passed = (
                violations == 0
                and touches >= self.min_touches
                and max_gap <= self.max_span_bars
                and aligned
            )

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    f"candidate {'High' if pivot.is_high else 'Low'} "
                    f"base={candidate.candle.time}({candidate.price}) "
                    f"touch={pivot.candle.time}({pivot.price}) "
                    f"span={span} slope={slope:.6f} violations={violations} "
                    f"touches={touches}/{self.min_touches} max_gap={max_gap}/{self.max_span_bars} "
                    f"aligned={aligned} -> {'PASSED' if passed else 'rejected'}"
                )

            if passed:
                score = touches * 100 + span
                if score > best_score:
                    best_score = score
                    best_base = candidate
                    best_slope = slope

        if best_base is None:
            return

        direction = MarketSide.BEARISH if pivot.is_high else MarketSide.BULLISH
        self._try_merge_or_add(
            direction,
            best_base.index,
            best_base.candle,
            cur_index,
            pivot.candle,
            best_slope,
            best_score,
            similar_tolerance,
            merge_projection_seconds,
        )

    # ─── BREAK DETECTION ─────────────────────────────

    def _check_break(
        self,
        line: TrendlineModel,
        candle: Candle,
        line_value: float,
        is_support: bool,
        break_tol: float,
    ) -> bool:
        """mirrors the breakLogicMode branch in the per-bar loop"""
        if self.break_logic_mode is BreakLogicMode.ATR_DISTANCE:
            return (
                candle.close < line_value - break_tol
                if is_support
                else candle.close > line_value + break_tol
            )

        crossed = candle.close < line_value if is_support else candle.close > line_value

        if self.break_logic_mode is BreakLogicMode.CANDLE_CLOSE:
            opposite_color = (
                candle.close < candle.open if is_support else candle.close > candle.open
            )
            confirming = opposite_color and crossed
        else:  # CLOSE_CROSS
            confirming = crossed

        line.confirm_count = line.confirm_count + 1 if confirming else 0
        return line.confirm_count >= self.candle_confirm_count

    # ─── MAIN CALCULATION ────────────────────────────

    def _bar_seconds(self) -> float:
        timeframe = self.candles[0].timeframe
        if isinstance(timeframe, TimeFrame):
            return timeframe.minutes * 60

        diffs = [
            b.timestamp - a.timestamp
            for a, b in zip(self.candles[:200], self.candles[1:201])
            if b.timestamp - a.timestamp > 0
        ]
        return min(diffs) if diffs else 60.0

    def _prepare_run(
        self, start_index: int
    ) -> tuple[dict[int, list[PivotPoint]], float]:
        candles = self.candles
        self.pivots.set(candles)
        self.atr.set(candles)

        merge_projection_seconds = self.merge_projection_bars * self._bar_seconds()

        pivots_by_confirm_index: dict[int, list[PivotPoint]] = {}
        for pivot in self.pivots.data:
            if pivot.confirmed_index >= start_index:
                pivots_by_confirm_index.setdefault(pivot.confirmed_index, []).append(
                    pivot
                )

        return pivots_by_confirm_index, merge_projection_seconds

    def _process_bar(
        self,
        i: int,
        candle: Candle,
        pivots_by_confirm_index: dict[int, list[PivotPoint]],
        merge_projection_seconds: float,
    ):
        atr_value = self.atr.data.get(candle.timestamp, 0.0)
        touch_tol = atr_value * self.touch_mult
        break_tol = atr_value * self.break_mult
        similar_tolerance = touch_tol * 2.5

        for pivot in pivots_by_confirm_index.get(i, []):
            self._process_new_pivot(
                pivot,
                i,
                touch_tol,
                break_tol,
                similar_tolerance,
                merge_projection_seconds,
            )

        resistance_breaks = 0
        support_breaks = 0

        for line in self._lines.copy():
            if line.broken:
                continue

            line.end_candle = candle
            line_value = line.value_at(candle.timestamp)
            is_support = line.side is MarketSide.BULLISH

            touched = (
                abs(candle.low - line_value) <= touch_tol
                if is_support
                else abs(candle.high - line_value) <= touch_tol
            )
            if touched:
                line.last_touch_index = i
                line.last_touch_candle = candle

            broke = self._check_break(line, candle, line_value, is_support, break_tol)

            mtr_eligible = not self.display_only_aligned or (
                line.slope > 0 if is_support else line.slope < 0
            )
            if broke and mtr_eligible:
                if is_support:
                    support_breaks += 1
                else:
                    resistance_breaks += 1

            stale = (i - line.last_touch_index) > self.stale_bars

            if broke or stale:
                line.broken = True
                logger.debug(
                    f"trendline archived (broke={broke}, stale={stale}): {line}"
                )
                if not self.keep_archived:
                    self._lines.remove(line)

        if resistance_breaks > 0:
            self.mtr_events.append(MTREvent(candle, True, resistance_breaks))
        if support_breaks > 0:
            self.mtr_events.append(MTREvent(candle, False, support_breaks))
        self._enforce_max_mtr_events()

        self._merge_similar_lines(candle, similar_tolerance)
        self._enforce_max_total_lines()

    def _visible_lines(self) -> list[TrendlineModel]:
        if not self.keep_archived:
            return [line for line in self._lines if not line.broken]
        return self._lines

    def _calculate(self) -> list[TrendlineModel]:
        candles = self.candles
        if len(candles) < self.pivots.depth + 2:
            return []

        self._pivot_highs = []
        self._pivot_lows = []
        self._lines = []
        self.mtr_events = []

        pivots_by_confirm_index, merge_projection_seconds = self._prepare_run(0)

        for i, candle in enumerate(candles):
            self._process_bar(
                i, candle, pivots_by_confirm_index, merge_projection_seconds
            )

        self._last_checked_index = len(candles) - 1
        return self._visible_lines()

    def _forcast(self) -> MarketSide:
        return MarketSide.NEUTRAL

    def plot(
        self,
        plot: ChartPlot,
        show_archived: bool | None = None,
        show_trendlines: bool = True,
        show_mtr_labels: bool = True,
    ):
        show_archived = self.keep_archived if show_archived is None else show_archived

        if show_trendlines:
            for line in self.data:
                if line.broken and not show_archived:
                    continue
                color = "#26a69a" if line.side is MarketSide.BULLISH else "#e53935"
                plot.draw_line(
                    line.base_candle.time,
                    line.base_price,
                    line.end_candle.time,
                    line.value_at(line.end_candle.timestamp),
                    color=color,
                    width=1,
                )

        if show_mtr_labels:
            for event in self.mtr_events:
                atr_value = self.atr.data.get(event.candle.timestamp, 0.0)
                offset = atr_value * 0.6 if atr_value else event.candle.close * 0.001
                if event.bullish:
                    # resistance broken -> bullish break, label below the low
                    plot.draw_label(
                        event.candle.time,
                        event.candle.low - offset,
                        event.text,
                        color="#00e676",
                        anchor=(0.5, 0.0),
                    )
                else:
                    # support broken -> bearish break, label above the high
                    plot.draw_label(
                        event.candle.time,
                        event.candle.high + offset,
                        event.text,
                        color="#ff9100",
                        anchor=(0.5, 1.0),
                    )

    def update(self, candles: list[Candle], *args, **kwargs) -> list[TrendlineModel]:
        if self.last_checked_candle is None:
            raise ValueError("last_checked_candle is None")

        start_index = self.find_new_candle_index(candles)
        if start_index >= len(candles):
            return self.data

        # position of the last-seen candle in the NEW window vs where it
        # was recorded last time -> how far the window has slid forward.
        # Must rebase BEFORE `_prepare_run` (which touches self.pivots/
        # self.atr) or any of the per-bar processing below, since
        # everything downstream compares against these stored indices.
        shift = self._last_checked_index - (start_index - 1)
        if shift > 0:
            self._rebase(shift)

        self.candles = candles

        pivots_by_confirm_index, merge_projection_seconds = self._prepare_run(
            start_index
        )

        for i in range(start_index, len(candles)):
            self._process_bar(
                i, candles[i], pivots_by_confirm_index, merge_projection_seconds
            )

        self.data = self._visible_lines()
        self.last_checked_candle = candles[-1]
        self._last_checked_index = len(candles) - 1
        return self.data
