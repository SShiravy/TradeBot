from TraderBot.models import Position
from TraderBot.PositionHandlers.Statistics.Analyses import (
    HourlyPnL,
    PerformanceAnalysis,
    PnLBreakdown,
    SessionPnL,
    WeekdayPnL,
)
from TraderBot.PositionHandlers.Statistics.base import (
    DEFAULT_PLOTS_DIR,
    StatisticalAnalysis,
)
from pathlib import Path
from typing import Iterable, Self, Sequence


class StatisticsSuite:
    """Runs several analyses over the same positions, prints and plots them together."""

    def __init__(self, analyses: Sequence[StatisticalAnalysis]) -> None:
        self.analyses = list(analyses)

    @classmethod
    def standard(cls) -> Self:
        """Every analysis that needs positions only; add tick-based ones explicitly."""
        return cls(
            [
                PerformanceAnalysis(),
                PnLBreakdown(),
                HourlyPnL(),
                WeekdayPnL(),
                SessionPnL(),
            ]
        )

    def analyze(self, positions: Iterable[Position]) -> Self:
        positions = list(positions)
        for analysis in self.analyses:
            analysis.analyze(positions)
        return self

    def plot(
        self,
        label: str = "",
        show: bool = False,
        save_dir: str | Path | None = DEFAULT_PLOTS_DIR,
    ) -> list[Path]:
        return [
            path
            for analysis in self.analyses
            for path in analysis.plot(label, show, save_dir)
        ]

    def __str__(self) -> str:
        return "\n\n".join(str(analysis) for analysis in self.analyses)
