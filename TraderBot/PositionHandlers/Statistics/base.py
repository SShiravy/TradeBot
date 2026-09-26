from TraderBot.models import Position
from TraderBot.PositionHandlers.Statistics.text import TextReport
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Protocol
import pandas as pd

if TYPE_CHECKING:
    from TraderBot.PositionHandlers.Statistics.Plots.base import ResultPlotter


DEFAULT_PLOTS_DIR = Path("Images") / "Statistics"


class TickSource(Protocol):
    """Serves bid/ask ticks by unix-second range, e.g. BackTest's `TickDataHandler`."""

    def get_ticks_from_timstamp_range(
        self, start_timestamp: int, end_timestamp: int
    ) -> pd.DataFrame: ...


@dataclass(frozen=True, slots=True, eq=False)
class AnalysisResult(ABC):
    """Immutable output of an analysis. `str()` renders its text report."""

    title: str

    @abstractmethod
    def report(self) -> TextReport:
        pass

    def __str__(self) -> str:
        return str(self.report())


def closed_positions(positions: Iterable[Position]) -> list[Position]:
    """Closed positions ordered by close time, the order their PnL was realised."""
    closed = [pos for pos in positions if pos.closed_timestamp is not None]
    return sorted(closed, key=lambda pos: pos.closed_timestamp or 0)


class StatisticalAnalysis[R: AnalysisResult](ABC):
    """
    One statistical method over closed positions: configure it, `analyze()` the
    positions, then read `result`, print it, or `plot()` it. Subclasses only
    implement `_compute`; drawing is delegated to `plotter`.
    """

    title: str = ""

    def __init__(self, plotter: "ResultPlotter[R]") -> None:
        self.plotter = plotter
        self._result: R | None = None

    @property
    def name(self) -> str:
        return self.title or self.__class__.__name__

    @abstractmethod
    def _compute(self, positions: list[Position]) -> R:
        """Build the result from closed positions ordered by close time."""

    def analyze(self, positions: Iterable[Position]) -> R:
        self._result = self._compute(closed_positions(positions))
        return self._result

    @property
    def result(self) -> R:
        if self._result is None:
            raise RuntimeError(f"{self.name}: call analyze() before reading results")
        return self._result

    def plot(
        self,
        label: str = "",
        show: bool = True,
        save_dir: str | Path | None = DEFAULT_PLOTS_DIR,
    ) -> list[Path]:
        """Draw the result, save each figure under `save_dir` (None: don't save), return the paths."""
        return self.plotter.render(self.result, label, show, save_dir)

    def __str__(self) -> str:
        if self._result is None:
            return f"{self.name}: not analyzed yet"
        return str(self._result)
