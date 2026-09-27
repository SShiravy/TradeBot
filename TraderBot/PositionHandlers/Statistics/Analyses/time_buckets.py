from Settings.timing import TimeHandler
from TraderBot.models import PnLReport, Position
from TraderBot.PositionHandlers.trades_pnl import PnLReportGenerator
from TraderBot.PositionHandlers.Statistics.base import (
    AnalysisResult,
    StatisticalAnalysis,
)
from TraderBot.PositionHandlers.Statistics.Plots.base import ResultPlotter
from TraderBot.PositionHandlers.Statistics.Plots.time_buckets import TimeBucketPlotter
from TraderBot.PositionHandlers.Statistics.text import (
    TextReport,
    money,
    percent,
    signed,
)
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from functools import reduce
from typing import NamedTuple, Sequence
import operator


@dataclass(frozen=True, slots=True, eq=False)
class TimeBucketResult(AnalysisResult):
    """One merged `PnLReport` per bucket, in display order; None for an empty bucket."""

    bucket_label: str
    buckets: dict[str, PnLReport | None]

    @property
    def active(self) -> dict[str, PnLReport]:
        return {name: r for name, r in self.buckets.items() if r is not None}

    @property
    def total_trades(self) -> int:
        return sum(r.total_positions for r in self.active.values())

    @staticmethod
    def win_rate(report: PnLReport) -> float:
        return report.wins / report.total_positions * 100

    def report(self) -> TextReport:
        text = TextReport(self.title, "by entry time (UTC)")
        active = self.active
        if not active:
            return text.line("No closed positions.")

        best = max(active, key=lambda name: active[name].pnl_dollar)
        worst = min(active, key=lambda name: active[name].pnl_dollar)
        text.field("Trades", self.total_trades)
        text.field("Best", f"{best} ({money(active[best].pnl_dollar)})")
        text.field("Worst", f"{worst} ({money(active[worst].pnl_dollar)})")

        rows = []
        for name, r in self.buckets.items():
            if r is None:
                rows.append((name, 0, "-", "-", "-", "-"))
                continue
            rows.append(
                (
                    name,
                    r.total_positions,
                    percent(self.win_rate(r)),
                    signed(r.pnl_dollar),
                    signed(r.pnl_dollar / r.total_positions),
                    f"{signed(r.pnl_percent)}%",
                )
            )
        text.section("Buckets")
        text.table(
            (self.bucket_label, "Trades", "Win%", "Net $", "Avg $", "Net %"), rows
        )
        return text


class TimeBucketAnalysis(StatisticalAnalysis[TimeBucketResult]):
    """
    PnL grouped by when positions were opened. The entry time is the report's
    `first_time`, read in the TimeHandler timezone (UTC). Each bucket is the
    sum of its positions' `PnLReport`s.
    """

    bucket_label: str = "Bucket"

    def __init__(self, plotter: ResultPlotter[TimeBucketResult] | None = None):
        super().__init__(plotter or TimeBucketPlotter())

    @abstractmethod
    def buckets(self) -> list[str]:
        """Bucket names in display order."""

    @abstractmethod
    def bucket_of(self, moment: datetime) -> str:
        """Bucket name for an entry time."""

    def _compute(self, positions: list[Position]) -> TimeBucketResult:
        grouped: dict[str, list[PnLReport]] = {name: [] for name in self.buckets()}
        for pos in positions:
            report = PnLReportGenerator.from_position(pos)
            grouped[self.bucket_of(TimeHandler.to_datetime(report.first_time))].append(
                report
            )
        return TimeBucketResult(
            title=self.title,
            bucket_label=self.bucket_label,
            buckets={
                name: reduce(operator.add, reports) if reports else None
                for name, reports in grouped.items()
            },
        )


class HourlyPnL(TimeBucketAnalysis):
    title = "Hourly PnL"
    bucket_label = "Hour (UTC)"

    def buckets(self) -> list[str]:
        return [f"{hour:02d}" for hour in range(24)]

    def bucket_of(self, moment: datetime) -> str:
        return f"{moment.hour:02d}"


class WeekdayPnL(TimeBucketAnalysis):
    title = "Weekday PnL"
    bucket_label = "Weekday (UTC)"

    WEEKDAYS = (
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    )

    def buckets(self) -> list[str]:
        return list(self.WEEKDAYS)

    def bucket_of(self, moment: datetime) -> str:
        return self.WEEKDAYS[moment.weekday()]


class TradingSession(NamedTuple):
    name: str
    start_hour: int  # inclusive, UTC
    end_hour: int  # exclusive, UTC


FOREX_SESSIONS = (
    TradingSession("Sydney/Tokyo", 0, 6),
    TradingSession("Tokyo", 6, 8),
    TradingSession("Tokyo/London", 8, 9),
    TradingSession("London", 9, 13),
    TradingSession("London/New York", 13, 17),
    TradingSession("New York", 17, 21),
    TradingSession("Sydney/New York", 21, 22),
    TradingSession("Sydney", 22, 24),
)


class SessionPnL(TimeBucketAnalysis):
    title = "Session PnL"
    bucket_label = "Session (UTC)"

    def __init__(
        self,
        sessions: Sequence[TradingSession] = FOREX_SESSIONS,
        plotter: ResultPlotter[TimeBucketResult] | None = None,
    ):
        super().__init__(plotter)
        covered = sorted(h for s in sessions for h in range(s.start_hour, s.end_hour))
        if covered != list(range(24)):
            raise ValueError("sessions must cover every UTC hour exactly once")
        self.sessions = tuple(sessions)

    def buckets(self) -> list[str]:
        return [session.name for session in self.sessions]

    def bucket_of(self, moment: datetime) -> str:
        return next(
            s.name for s in self.sessions if s.start_hour <= moment.hour < s.end_hour
        )
