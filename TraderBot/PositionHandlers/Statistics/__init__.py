"""
Statistics over closed positions.

    suite = StatisticsSuite.standard().analyze(trades_manager.closed_positions)
    print(suite)
    suite.plot(label=bot.identifier)

    mfe = MaxFavorableExcursion(Measure.PIPS, candles_range=30)
    mfe.analyze(positions)          # ticks from the CsvChart, or pass tick_source
    print(mfe)
    mfe.plot(show=True)

Layout: `Analyses/` computes immutable results from `PnLReport`s (via
`PnLReportGenerator`) and TimeHandler times; `Plots/` only draws them.
"""

from TraderBot.PositionHandlers.Statistics.Analyses import (
    FOREX_SESSIONS,
    BreakdownResult,
    ExcursionResult,
    HourlyPnL,
    MaxFavorableExcursion,
    PerformanceAnalysis,
    PerformanceResult,
    PnLBreakdown,
    SessionPnL,
    StopLossOvershoot,
    TickExcursionAnalysis,
    TimeBucketAnalysis,
    TimeBucketResult,
    TradingSession,
    WeekdayPnL,
)
from TraderBot.PositionHandlers.Statistics.base import (
    AnalysisResult,
    StatisticalAnalysis,
    TickSource,
)
from TraderBot.PositionHandlers.Statistics.measures import Measure
from TraderBot.PositionHandlers.Statistics.suite import StatisticsSuite


__all__ = [
    "AnalysisResult",
    "StatisticalAnalysis",
    "TickSource",
    "Measure",
    "StatisticsSuite",
    "PerformanceAnalysis",
    "PerformanceResult",
    "PnLBreakdown",
    "BreakdownResult",
    "TimeBucketAnalysis",
    "TimeBucketResult",
    "HourlyPnL",
    "WeekdayPnL",
    "SessionPnL",
    "TradingSession",
    "FOREX_SESSIONS",
    "TickExcursionAnalysis",
    "ExcursionResult",
    "MaxFavorableExcursion",
    "StopLossOvershoot",
]
