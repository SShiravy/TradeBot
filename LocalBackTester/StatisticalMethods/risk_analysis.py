from LocalBackTester.StatisticalMethods.models import BaseStatisticalAnalysis
from TradingModule.models import Position


class RiskAnalysis(BaseStatisticalAnalysis):
    def __init__(self):
        super().__init__()
        self.pnl_series = [0.0]
        self.win_lose_series = [0.0]
        self.pnl_percentage_series = [0.0]
        self.high_watermark_series = [0.0]
        self.drawdown_series = [0.0]
        self.win_rate_series = [0.0]
        self.average_trade_series = [0.0]
        self.win_streak_distribution: dict[int, int] = {}
        self.loss_streak_distribution: dict[int, int] = {}

    def analyze(self, all_positions: list[Position], *args, **kwargs) -> None:
        self.positions = all_positions
        win_count = 0
        current_consecutive_wins = 0
        current_consecutive_losses = 0

        for pos in self.positions:
            self.pnl_series.append(self.pnl_series[-1] + pos.pnl)
            self.win_lose_series.append(
                self.win_lose_series[-1] + (1 if pos.pnl > 0 else -1)
            )
            self.pnl_percentage_series.append(
                self.pnl_percentage_series[-1] + pos.pnl_percent
            )

            current_pnl = self.pnl_series[-1]
            current_high_watermark = max(self.high_watermark_series[-1], current_pnl)
            self.high_watermark_series.append(current_high_watermark)
            self.drawdown_series.append(current_pnl - current_high_watermark)

            # Win Rate
            if pos.pnl > 0:
                win_count += 1
            self.win_rate_series.append(win_count / (len(self.win_rate_series)) * 100)
            self.average_trade_series.append(
                current_pnl / (len(self.average_trade_series))
            )

            if pos.pnl > 0:
                current_consecutive_wins += 1
                if current_consecutive_losses > 0:
                    self.loss_streak_distribution[current_consecutive_losses] = (
                        self.loss_streak_distribution.get(current_consecutive_losses, 0)
                        + 1
                    )
                    current_consecutive_losses = 0
            else:
                current_consecutive_losses += 1
                if current_consecutive_wins > 0:
                    self.win_streak_distribution[current_consecutive_wins] = (
                        self.win_streak_distribution.get(current_consecutive_wins, 0)
                        + 1
                    )
                    current_consecutive_wins = 0

        if current_consecutive_wins > 0:
            self.win_streak_distribution[current_consecutive_wins] = (
                self.win_streak_distribution.get(current_consecutive_wins, 0) + 1
            )

        if current_consecutive_losses > 0:
            self.loss_streak_distribution[current_consecutive_losses] = (
                self.loss_streak_distribution.get(current_consecutive_losses, 0) + 1
            )

    def plot(self, plot_name: str, show: bool = True):
        self.linear_plot(
            series=self.pnl_series,
            title=f"Cumulative PnL - {plot_name}",
            xlabel="Trade Number",
            ylabel="PnL",
            plot_name=plot_name,
            filename="Cumulative_PnL",
            show=show,
        )

        self.linear_plot(
            series=self.win_lose_series,
            title=f"Cumulative Win/Lose - {plot_name}",
            xlabel="Trade Number",
            ylabel="Win/Lose Score",
            plot_name=plot_name,
            filename="Cumulative_Win_Lose",
            show=show,
        )

        self.linear_plot(
            series=self.pnl_percentage_series,
            title=f"Cumulative PnL Percentage - {plot_name}",
            xlabel="Trade Number",
            ylabel="PnL %",
            plot_name=plot_name,
            filename="Cumulative_PnL_Percentage",
            show=show,
        )

        self.linear_plot(
            series=self.high_watermark_series,
            title=f"High Watermark - {plot_name}",
            xlabel="Trade Number",
            ylabel="High Watermark",
            plot_name=plot_name,
            filename="High_WaterMark",
            show=show,
            horizontal_marks=[max(self.high_watermark_series)],
        )

        self.linear_plot(
            series=self.drawdown_series,
            title=f"Drawdown - {plot_name}",
            xlabel="Trade Number",
            ylabel="Drawdown",
            plot_name=plot_name,
            filename="Drawdown",
            show=show,
            horizontal_marks=[min(self.drawdown_series)],
        )

        self.linear_plot(
            series=self.win_rate_series,
            title=f"Running Win Rate - {plot_name}",
            xlabel="Trade Number",
            ylabel="Win Rate",
            plot_name=plot_name,
            filename="Running_Win_Rate",
            show=show,
        )

        self.linear_plot(
            series=self.average_trade_series,
            title=f"Running Average Trade - {plot_name}",
            xlabel="Trade Number",
            ylabel="Average Trade PnL",
            plot_name=plot_name,
            filename="Running_Average_Trade",
            show=show,
        )

        self.histogram_plot(
            distribution=self.win_streak_distribution,
            title=f"Winning Streak Distribution - {plot_name}",
            xlabel="Consecutive Winning Trades",
            filename="Winning_Streak_Distribution",
            plot_name=plot_name,
            show=show,
        )

        self.histogram_plot(
            distribution=self.loss_streak_distribution,
            title=f"Losing Streak Distribution - {plot_name}",
            xlabel="Consecutive Losing Trades",
            filename="Losing_Streak_Distribution",
            plot_name=plot_name,
            show=show,
        )
