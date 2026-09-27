from TraderBot.models import PnLReport, Position
from TraderBot.PositionHandlers.trades_pnl import PnLReportGenerator
from TraderBot.PositionHandlers.Statistics.base import (
    AnalysisResult,
    StatisticalAnalysis,
)
from TraderBot.PositionHandlers.Statistics.Plots.base import ResultPlotter
from TraderBot.PositionHandlers.Statistics.Plots.performance import PerformancePlotter
from TraderBot.PositionHandlers.Statistics.text import (
    TextReport,
    duration,
    moment,
    money,
    number,
    percent,
    signed,
)
from collections import Counter
from dataclasses import dataclass
import numpy as np


def run_lengths(mask: np.ndarray) -> np.ndarray:
    """Lengths of every run of consecutive True values."""
    padded = np.concatenate(([False], mask, [False]))
    edges = np.flatnonzero(padded[1:] != padded[:-1])
    return edges[1::2] - edges[::2]


def length_distribution(lengths: np.ndarray) -> dict[int, int]:
    return {int(k): v for k, v in sorted(Counter(lengths.tolist()).items())}


@dataclass(frozen=True, slots=True, eq=False)
class PerformanceResult(AnalysisResult):
    """
    Per-trade arrays in close order. Cumulative series start with a 0 point
    "before the first trade", so their index equals the number of trades done.
    """

    overall: PnLReport | None
    close_times: np.ndarray
    trade_pnl: np.ndarray
    trade_percent: np.ndarray
    outcomes: np.ndarray  # +1 win, -1 loss, 0 flat, as classified by PnLReport
    holding_seconds: np.ndarray

    @property
    def n_trades(self) -> int:
        return len(self.trade_pnl)

    # ---- series --------------------------------------------------------------
    @property
    def equity(self) -> np.ndarray:
        return np.concatenate(([0.0], np.cumsum(self.trade_pnl)))

    @property
    def equity_percent(self) -> np.ndarray:
        return np.concatenate(([0.0], np.cumsum(self.trade_percent)))

    @property
    def high_watermark(self) -> np.ndarray:
        return np.maximum.accumulate(self.equity)

    @property
    def drawdown(self) -> np.ndarray:
        return self.equity - self.high_watermark

    @property
    def win_loss_score(self) -> np.ndarray:
        return np.concatenate(([0], np.cumsum(self.outcomes)))

    @property
    def running_win_rate(self) -> np.ndarray:
        """Win rate (%) after trade 1..n."""
        return np.cumsum(self.outcomes > 0) / np.arange(1, self.n_trades + 1) * 100

    @property
    def running_average(self) -> np.ndarray:
        """Average trade PnL after trade 1..n."""
        return np.cumsum(self.trade_pnl) / np.arange(1, self.n_trades + 1)

    # ---- streaks (flats neither extend nor break a streak, like overall_report) -
    @property
    def win_streaks(self) -> dict[int, int]:
        decided = self.outcomes[self.outcomes != 0]
        return length_distribution(run_lengths(decided > 0))

    @property
    def loss_streaks(self) -> dict[int, int]:
        decided = self.outcomes[self.outcomes != 0]
        return length_distribution(run_lengths(decided < 0))

    # ---- metrics -------------------------------------------------------------
    @property
    def wins(self) -> int:
        return int((self.outcomes > 0).sum())

    @property
    def losses(self) -> int:
        return int((self.outcomes < 0).sum())

    @property
    def flats(self) -> int:
        return int((self.outcomes == 0).sum())

    @property
    def win_rate(self) -> float:
        return self.wins / self.n_trades * 100 if self.n_trades else float("nan")

    @property
    def gross_profit(self) -> float:
        return float(self.trade_pnl[self.trade_pnl > 0].sum())

    @property
    def gross_loss(self) -> float:
        return float(self.trade_pnl[self.trade_pnl < 0].sum())

    @property
    def profit_factor(self) -> float:
        if self.gross_loss:
            return self.gross_profit / -self.gross_loss
        return float("inf") if self.gross_profit else float("nan")

    @property
    def expectancy(self) -> float:
        return float(self.trade_pnl.mean()) if self.n_trades else float("nan")

    @property
    def average_win(self) -> float:
        winners = self.trade_pnl[self.trade_pnl > 0]
        return float(winners.mean()) if winners.size else float("nan")

    @property
    def average_loss(self) -> float:
        losers = self.trade_pnl[self.trade_pnl < 0]
        return float(losers.mean()) if losers.size else float("nan")

    @property
    def payoff_ratio(self) -> float:
        return self.average_win / -self.average_loss

    @property
    def sqn(self) -> float:
        """System Quality Number: sqrt(n) * mean / std of trade PnL."""
        if self.n_trades < 2 or not self.trade_pnl.std(ddof=1):
            return float("nan")
        return float(
            np.sqrt(self.n_trades) * self.trade_pnl.mean() / self.trade_pnl.std(ddof=1)
        )

    @property
    def max_drawdown(self) -> float:
        return float(self.drawdown.min())

    @property
    def max_drawdown_trade(self) -> int:
        return int(self.drawdown.argmin())

    @property
    def recovery_factor(self) -> float:
        if not self.max_drawdown:
            return float("nan")
        return float(self.equity[-1] / -self.max_drawdown)

    @property
    def longest_drawdown(self) -> int:
        """Most consecutive trades spent below the high watermark."""
        underwater = run_lengths(self.drawdown < 0)
        return int(underwater.max()) if underwater.size else 0

    def report(self) -> TextReport:
        text = TextReport(self.title)
        if self.overall is None:
            return text.line("No closed positions.")

        overall = self.overall
        text.field(
            "Period",
            f"{moment(overall.first_time)} -> {moment(overall.last_time)}"
            f" ({duration(overall.duration.total_seconds())})",
        )
        text.field(
            "Trades",
            f"{self.n_trades} ({self.wins} wins / {self.losses} losses"
            f" / {self.flats} flats)",
        )
        text.field("Win rate", percent(self.win_rate))
        text.field("Avg holding", duration(self.holding_seconds.mean()))

        text.section("Returns")
        text.field("Net PnL", money(overall.pnl_dollar))
        text.field("Net PnL %", f"{signed(overall.pnl_percent)}%")
        text.field("Net pips", signed(overall.pnl_pips, 1))
        text.field("Gross profit", money(self.gross_profit))
        text.field("Gross loss", money(self.gross_loss))
        text.field("Profit factor", number(self.profit_factor))
        text.field("Expectancy", f"{money(self.expectancy)} / trade")
        text.field("Average win", money(self.average_win))
        text.field("Average loss", money(self.average_loss))
        text.field("Payoff ratio", number(self.payoff_ratio))
        text.field("Largest win", money(float(self.trade_pnl.max())))
        text.field("Largest loss", money(float(self.trade_pnl.min())))
        text.field("SQN", number(self.sqn))

        text.section("Risk")
        dd_trade = self.max_drawdown_trade
        dd_when = (
            f" (trade {dd_trade}, {moment(int(self.close_times[dd_trade - 1]))})"
            if dd_trade
            else ""
        )
        text.field("Max drawdown", f"{money(self.max_drawdown)}{dd_when}")
        text.field("Recovery factor", number(self.recovery_factor))
        text.field("Longest drawdown", f"{self.longest_drawdown} trades")

        text.section("Streaks")
        wins, losses = self.win_streaks, self.loss_streaks
        lengths = sorted(set(wins) | set(losses))
        text.table(
            ("Length", "Win streaks", "Loss streaks"),
            [(n, wins.get(n, 0), losses.get(n, 0)) for n in lengths],
        )
        return text


class PerformanceAnalysis(StatisticalAnalysis[PerformanceResult]):
    """
    Trade-by-trade performance: equity curve, high watermark, drawdown, running
    win rate / average trade, streaks and summary metrics. Every trade's PnL
    comes from `PnLReportGenerator.from_position`, the totals from `overall_report`.
    """

    title = "Performance"

    def __init__(self, plotter: ResultPlotter[PerformanceResult] | None = None):
        super().__init__(plotter or PerformancePlotter())

    def _compute(self, positions: list[Position]) -> PerformanceResult:
        reports = [PnLReportGenerator.from_position(pos) for pos in positions]
        return PerformanceResult(
            title=self.title,
            overall=PnLReportGenerator.overall_report(positions) if positions else None,
            close_times=np.array(
                [pos.closed_timestamp for pos in positions], dtype=np.int64
            ),
            trade_pnl=np.array([r.pnl_dollar for r in reports], dtype=np.float64),
            trade_percent=np.array([r.pnl_percent for r in reports], dtype=np.float64),
            outcomes=np.array([r.wins - r.loses for r in reports], dtype=np.int64),
            holding_seconds=np.array(
                [r.last_time - r.first_time for r in reports], dtype=np.float64
            ),
        )
