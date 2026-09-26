from TraderBot.models import PnLReport, Position
from TraderBot.PositionHandlers.trades_pnl import PnLReportGenerator
from TraderBot.PositionHandlers.Statistics.base import (
    AnalysisResult,
    StatisticalAnalysis,
)
from TraderBot.PositionHandlers.Statistics.Plots.base import ResultPlotter
from TraderBot.PositionHandlers.Statistics.Plots.breakdown import BreakdownPlotter
from TraderBot.PositionHandlers.Statistics.text import (
    TextReport,
    money,
    percent,
    signed,
)
from dataclasses import dataclass


@dataclass(frozen=True, slots=True, eq=False)
class BreakdownResult(AnalysisResult):
    """One merged `PnLReport` per identifier, best net PnL first."""

    reports: list[PnLReport]

    @staticmethod
    def label(report: PnLReport) -> str:
        return f"{report.source} | {report.side.value} | {report.chart}"

    @staticmethod
    def win_rate(report: PnLReport) -> float:
        return report.wins / report.total_positions * 100

    def report(self) -> TextReport:
        text = TextReport(self.title, "by source, side and chart")
        if not self.reports:
            return text.line("No closed positions.")

        text.table(
            ("Source", "Side", "Chart", "Trades", "Win%", "Net $", "Avg $", "Pips"),
            [
                (
                    r.source,
                    r.side.value,
                    r.chart,
                    r.total_positions,
                    percent(self.win_rate(r)),
                    signed(r.pnl_dollar),
                    signed(r.pnl_dollar / r.total_positions),
                    signed(r.pnl_pips, 1),
                )
                for r in self.reports
            ],
        )
        total = sum(r.pnl_dollar for r in self.reports)
        text.line("")
        text.field("Net PnL", money(total))
        return text


class PnLBreakdown(StatisticalAnalysis[BreakdownResult]):
    """Net result per (source, side, chart) from `PnLReportGenerator.identifier_reports`."""

    title = "PnL Breakdown"

    def __init__(self, plotter: ResultPlotter[BreakdownResult] | None = None):
        super().__init__(plotter or BreakdownPlotter())

    def _compute(self, positions: list[Position]) -> BreakdownResult:
        reports = PnLReportGenerator.identifier_reports(positions)
        return BreakdownResult(
            title=self.title,
            reports=sorted(reports, key=lambda r: r.pnl_dollar, reverse=True),
        )
