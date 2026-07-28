from ChartModule.models import Candle, MarketSide, CandlesSource, TimeFrame
from ChartModule.Indicators.models import IndicatorBaseModel
from ChartModule.Indicators.lines import Line
from ChartModule.plot import ChartPlot
from AutoTrendlineModule.swing_pivots import SwingPivots, PivotPoint
from AutoTrendlineModule.atr import ATR
from dataclasses import dataclass, field
import logging


logger = logging.getLogger("AutoTrendlines")


@dataclass(slots=True)
class TrendlineModel:
    """
    A single auto-detected trendline (candidate/active/archived).

    direction: BULLISH -> support line anchored on Lows (rising)
               BEARISH -> resistance line anchored on Highs (falling)
    """

    direction: MarketSide
    source: CandlesSource
    base_index: int
    base_candle: Candle
    slope: float
    group_slope: float
    score: int
    last_touch_index: int
    last_touch_candle: Candle

    end_candle: Candle = field(init=False)
    broken: bool = field(default=False, init=False)

    def __post_init__(self):
        self.end_candle = self.base_candle

    @property
    def base_price(self) -> float:
        return self.source(self.base_candle)

    def value_at(self, timestamp: float) -> float:
        return self.base_price + self.slope * (timestamp - self.base_candle.timestamp)

    def as_line(self) -> Line:
        return Line(self.source, self.base_candle, self.end_candle)

    def __str__(self) -> str:
        return (
            f"{self.direction}|base={self.base_candle.time}"
            f"|broken={self.broken}|score={self.score}"
        )


class AutoTrendlines(IndicatorBaseModel):
    """
    Auto Trendlines (ATR Adaptive)

    Ported from the "Auto Trendlines (ATR Adaptive)" Pine Script indicator.

    Confirmed ZigZag pivots are used as trendline anchors/touches. A candidate
    line between two same-side pivots (Low-Low for support, High-High for
    resistance) is accepted only if it is not violated by any pivot in
    between (ATR break tolerance) and is touched at least `min_touches` times
    (ATR touch tolerance). Accepted candidates are merged into the most
    recent active line of the same direction when their slope is similar,
    otherwise a new line is started (pruning the weakest one if the
    per-direction limit is reached). Every bar, active lines are extended,
    checked for a new touch, and archived when price closes through them or
    when they go untouched for `stale_bars` bars. Near duplicate active
    lines are periodically merged.

    values: list[TrendlineModel]
    """

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
        max_total_lines: int = 20,
        stale_bars: int = 50,
        merge_projection_bars: int = 50,
        display_only_aligned: bool = True,
        keep_archived: bool = True,
    ) -> None:
        super().__init__()
        self.data: list[TrendlineModel]

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

        self._pivot_highs: list[PivotPoint] = []
        self._pivot_lows: list[PivotPoint] = []
        self._lines: list[TrendlineModel] = []

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
            1 for line in self._lines if not line.broken and line.direction is direction
        )

    def _find_most_recent_active(self, direction: MarketSide) -> TrendlineModel | None:
        candidates = [
            line for line in self._lines if not line.broken and line.direction is direction
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda line: line.base_index)

    def _find_weakest_active(self, direction: MarketSide) -> TrendlineModel | None:
        candidates = [
            line for line in self._lines if not line.broken and line.direction is direction
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda line: line.score)

    def _remove_oldest_archived(self):
        if len(self._lines) <= self.max_total_lines:
            return
        for i, line in enumerate(self._lines):
            if line.broken:
                del self._lines[i]
                return

    def _add_new_line(
        self,
        direction: MarketSide,
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

        source = CandlesSource.Low if direction is MarketSide.BULLISH else CandlesSource.High
        new_line = TrendlineModel(
            direction=direction,
            source=source,
            base_index=base_index,
            base_candle=base_candle,
            slope=slope,
            group_slope=slope,
            score=score,
            last_touch_index=touch_index,
            last_touch_candle=touch_candle,
        )
        self._lines.append(new_line)
        logger.debug(f"new trendline added: {new_line}")
        self._remove_oldest_archived()

    def _try_merge_or_add(
        self,
        direction: MarketSide,
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
                abs(candidate_slope - merge_target.group_slope) * merge_projection_seconds
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
                    merged = True

        if not merged:
            self._add_new_line(
                direction, base_index, base_candle, candidate_slope, score, new_index, new_candle
            )

    def _merge_similar_lines(self, current_candle: Candle, similar_tolerance: float):
        """mirrors f_mergeSimilarLines: drops (at most) one duplicate per call"""
        active = [line for line in self._lines if not line.broken]
        for i in range(len(active)):
            line_i = active[i]
            for j in range(i + 1, len(active)):
                line_j = active[j]
                if line_i.direction is not line_j.direction:
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

            if (
                violations == 0
                and touches >= self.min_touches
                and max_gap <= self.max_span_bars
                and aligned
            ):
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

    # ─── MAIN CALCULATION ────────────────────────────

    def _bar_seconds(self) -> float:
        """
        Seconds represented by one candle, so a price/second slope can be
        projected across `merge_projection_bars` *bars* (not seconds).
        """
        timeframe = self.candles[0].timeframe
        if isinstance(timeframe, TimeFrame):
            return timeframe.minutes * 60

        diffs = [
            b.timestamp - a.timestamp
            for a, b in zip(self.candles[:200], self.candles[1:201])
            if b.timestamp - a.timestamp > 0
        ]
        return min(diffs) if diffs else 60.0

    def _calculate(self) -> list[TrendlineModel]:
        candles = self.candles
        if len(candles) < self.pivots.depth + 2:
            return []

        self.pivots.set(candles)
        self.atr.set(candles)

        merge_projection_seconds = self.merge_projection_bars * self._bar_seconds()

        pivots_by_confirm_index: dict[int, list[PivotPoint]] = {}
        for pivot in self.pivots.data:
            pivots_by_confirm_index.setdefault(pivot.confirmed_index, []).append(pivot)

        self._pivot_highs = []
        self._pivot_lows = []
        self._lines = []

        for i, candle in enumerate(candles):
            atr_value = self.atr.data.get(candle.timestamp, 0.0)
            touch_tol = atr_value * self.touch_mult
            break_tol = atr_value * self.break_mult
            similar_tolerance = touch_tol * 2.5

            for pivot in pivots_by_confirm_index.get(i, []):
                self._process_new_pivot(
                    pivot, i, touch_tol, break_tol, similar_tolerance, merge_projection_seconds
                )

            for line in self._lines.copy():
                if line.broken:
                    continue

                line.end_candle = candle
                line_value = line.value_at(candle.timestamp)

                touched = (
                    abs(candle.low - line_value) <= touch_tol
                    if line.direction is MarketSide.BULLISH
                    else abs(candle.high - line_value) <= touch_tol
                )
                if touched:
                    line.last_touch_index = i
                    line.last_touch_candle = candle

                broke = (
                    candle.close < line_value - break_tol
                    if line.direction is MarketSide.BULLISH
                    else candle.close > line_value + break_tol
                )
                stale = (i - line.last_touch_index) > self.stale_bars

                if broke or stale:
                    line.broken = True
                    logger.debug(f"trendline archived (broke={broke}, stale={stale}): {line}")
                    if not self.keep_archived:
                        self._lines.remove(line)

            self._merge_similar_lines(candle, similar_tolerance)

        if not self.keep_archived:
            return [line for line in self._lines if not line.broken]
        return self._lines

    def _forcast(self) -> MarketSide:
        return MarketSide.NEUTRAL

    def plot(self, plot: ChartPlot, show_archived: bool | None = None):
        show_archived = self.keep_archived if show_archived is None else show_archived
        for line in self.data:
            if line.broken and not show_archived:
                continue
            color = "#26a69a" if line.direction is MarketSide.BULLISH else "#e53935"
            plot.draw_line(
                line.base_candle.time,
                line.base_price,
                line.end_candle.time,
                line.value_at(line.end_candle.timestamp),
                color=color,
                width=1,
            )

    def update(self, candles: list[Candle], *args, **kwargs):
        pass
