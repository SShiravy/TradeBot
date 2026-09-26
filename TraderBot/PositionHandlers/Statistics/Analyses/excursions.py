from TraderBot.models import Position, PositionSide
from TraderBot.PositionHandlers.Statistics.base import (
    AnalysisResult,
    StatisticalAnalysis,
    TickSource,
)
from TraderBot.PositionHandlers.Statistics.measures import Measure
from TraderBot.PositionHandlers.Statistics.Plots.base import ResultPlotter
from TraderBot.PositionHandlers.Statistics.Plots.excursions import ExcursionPlotter
from TraderBot.PositionHandlers.Statistics.text import TextReport
from abc import abstractmethod
from collections import Counter
from dataclasses import dataclass
import numpy as np
import math


class Unmeasurable(Exception):
    """Raised by `_excursion` when a position can't be measured; the message is the reason."""


def nice_step(span: float, target_bins: int = 25) -> float:
    """A 1/2/2.5/5 x 10^k bin width giving about `target_bins` bins over `span`."""
    raw = span / target_bins
    magnitude = 10 ** math.floor(math.log10(raw))
    return next(m * magnitude for m in (1, 2, 2.5, 5, 10) if m * magnitude >= raw)


@dataclass(frozen=True, slots=True, eq=False)
class ExcursionResult(AnalysisResult):
    """Excursions (>= 0, in `measure`) of the measured long and short positions."""

    description: str
    measure: Measure
    candles_range: int
    long: np.ndarray
    short: np.ndarray
    unmeasured: dict[str, int]  # reason -> positions
    bin_size: float | None

    @property
    def all(self) -> np.ndarray:
        return np.concatenate((self.long, self.short))

    def bin_edges(self) -> np.ndarray:
        top = float(self.all.max()) if self.all.size else 0.0
        if top <= 0:
            top = 1.0
        step = self.bin_size or nice_step(top)
        return np.arange(0.0, top + step, step)

    def histogram(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """(bin edges, long counts, short counts)"""
        edges = self.bin_edges()
        return (
            edges,
            np.histogram(self.long, bins=edges)[0],
            np.histogram(self.short, bins=edges)[0],
        )

    @staticmethod
    def reach_share(values: np.ndarray, levels: np.ndarray) -> np.ndarray:
        """Share (%) of `values` that reached at least each level."""
        if values.size == 0:
            return np.full(levels.shape, np.nan)
        ordered = np.sort(values)
        below = np.searchsorted(ordered, levels, side="left")
        return (1 - below / ordered.size) * 100

    def report(self) -> TextReport:
        text = TextReport(
            self.title,
            f"{self.measure.value}, {self.candles_range} candles window",
        )
        text.line(self.description)
        text.line("")

        measured = self.all.size
        skipped = sum(self.unmeasured.values())
        text.field("Measured", f"{measured} of {measured + skipped} positions")
        if skipped:
            reasons = ", ".join(
                f"{reason}: {n}" for reason, n in self.unmeasured.items()
            )
            text.field("Not measured", reasons)
        if not measured:
            return text

        decimals = self.measure.decimals

        def row(side: str, values: np.ndarray) -> tuple:
            if values.size == 0:
                return (side, 0, *("-",) * 6)
            p25, p50, p75, p90 = np.percentile(values, (25, 50, 75, 90))
            stats = (values.mean(), p25, p50, p75, p90, values.max())
            return (side, values.size, *(f"{v:,.{decimals}f}" for v in stats))

        text.section(f"Distribution ({self.measure.value})")
        text.table(
            ("Side", "Trades", "Mean", "P25", "Median", "P75", "P90", "Max"),
            [row("Long", self.long), row("Short", self.short), row("All", self.all)],
        )
        return text


class TickExcursionAnalysis(StatisticalAnalysis[ExcursionResult]):
    """
    Measures how price moved around a position using tick data, inside a window
    of `candles_range` candles of the position's timeframe. Prices are the ones
    the position could close at: bid for longs, ask for shorts.

    Ticks come from `tick_source`, or else from the position's chart when it
    carries one (BackTest's `CsvChart.tick_handler`).
    """

    description: str = ""

    def __init__(
        self,
        measure: Measure = Measure.PIPS,
        candles_range: int = 30,
        bin_size: float | None = None,
        tick_source: TickSource | None = None,
        plotter: ResultPlotter[ExcursionResult] | None = None,
    ):
        super().__init__(plotter or ExcursionPlotter())
        self.measure = measure
        self.candles_range = candles_range
        self.bin_size = bin_size
        self.tick_source = tick_source

    @abstractmethod
    def _excursion(self, position: Position) -> float:
        """The position's excursion (>= 0), or raise `Unmeasurable`."""

    def _ticks(self, position: Position) -> TickSource:
        if self.tick_source is not None:
            return self.tick_source
        source = getattr(position.chart, "tick_handler", None)
        if source is None:
            raise ValueError(
                f"{self.name} needs tick data: pass tick_source, "
                f"or use a chart with ticks (got {position.chart})"
            )
        return source

    def _exit_prices(self, position: Position, start: int) -> np.ndarray:
        window = position.chart.timeframe.minutes * 60 * self.candles_range
        ticks = self._ticks(position).get_ticks_from_timstamp_range(
            start, start + window
        )
        column = "bid" if position.side is PositionSide.LONG else "ask"
        prices = ticks[column].to_numpy(dtype=np.float64)
        if prices.size == 0:
            raise Unmeasurable("no ticks in window")
        return prices

    def _compute(self, positions: list[Position]) -> ExcursionResult:
        long, short = [], []
        unmeasured: Counter[str] = Counter()
        for pos in positions:
            try:
                value = self._excursion(pos)
            except Unmeasurable as reason:
                unmeasured[str(reason)] += 1
                continue
            (long if pos.side is PositionSide.LONG else short).append(value)

        return ExcursionResult(
            title=self.title,
            description=self.description,
            measure=self.measure,
            candles_range=self.candles_range,
            long=np.array(long, dtype=np.float64),
            short=np.array(short, dtype=np.float64),
            unmeasured=dict(unmeasured),
            bin_size=self.bin_size,
        )


class MaxFavorableExcursion(TickExcursionAnalysis):
    title = "Max Favorable Excursion"
    description = (
        "Best move in the position's favour after entry, until the initial\n"
        "stop-loss is touched or the window ends. Guides take-profit placement."
    )

    def _excursion(self, position: Position) -> float:
        entry_time = position.open_timestamp or position.defined_timestamp
        prices = self._exit_prices(position, entry_time)
        factor = position.side.factor

        # once stopped out, later favourable prices were unreachable
        stopped = np.flatnonzero(
            (prices - position.initial_stoploss_price) * factor <= 0
        )
        if stopped.size:
            prices = prices[: stopped[0]]
        if prices.size == 0:
            return 0.0

        best = prices[np.argmax(prices * factor)]
        return max(self.measure.move(position, position.entry_price, best), 0.0)


class StopLossOvershoot(TickExcursionAnalysis):
    title = "Stop-Loss Overshoot"
    description = (
        "For stopped-out positions: how far price ran past the stop before\n"
        "trading back through it (by `tolerance`), i.e. how much wider a stop\n"
        "would have survived. Stops price never came back to are not measured."
    )

    def __init__(
        self,
        measure: Measure = Measure.PIPS,
        candles_range: int = 30,
        tolerance: float = 0.0,
        bin_size: float | None = None,
        tick_source: TickSource | None = None,
        plotter: ResultPlotter[ExcursionResult] | None = None,
    ):
        """`tolerance`, in `measure` units, is how far back through the stop counts as a recovery."""
        super().__init__(measure, candles_range, bin_size, tick_source, plotter)
        self.tolerance = tolerance

    def _excursion(self, position: Position) -> float:
        stoploss = position.stoploss
        if stoploss.triggered_timestamp is None:
            raise Unmeasurable("not stopped out")

        factor = position.side.factor
        recovery_level = stoploss.price + factor * self.measure.price_distance(
            position, stoploss.price, self.tolerance
        )
        prices = self._exit_prices(position, stoploss.triggered_timestamp)
        recovered = np.flatnonzero((prices - recovery_level) * factor > 0)
        if recovered.size == 0:
            raise Unmeasurable("stop held (no recovery in window)")

        before = prices[: recovered[0]]
        if before.size == 0:
            return 0.0
        worst = before[np.argmin(before * factor)]
        return max(self.measure.move(position, worst, stoploss.price), 0.0)
