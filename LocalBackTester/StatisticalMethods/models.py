from LocalBackTester.models import CsvChart
from TradingModule.models import Position
from TradingModule.trader_bot import TradeConfig
from abc import ABC, abstractmethod
from collections import defaultdict
import matplotlib.pyplot as plt
from typing import Any, TypeAlias


class BaseStatisticalAnalysis(ABC):
    def __init__(
        self,
    ):
        self.name = self.__class__.__name__
        self.all_positions = []

    @abstractmethod
    def analyze(
        self,
        all_positions: list[Position],
        the_config: TradeConfig | None,
        *args,
        **kwargs,
    ) -> Any:
        pass

    @abstractmethod
    def plot(self, plot_name: str, show: bool = True):
        pass

    @classmethod
    def linear_plot(
        cls,
        series: list[float] | list[int],
        title: str,
        xlabel: str,
        ylabel: str,
        plot_name: str,
        filename: str,
        show: bool = True,
        horizontal_marks: list[float] = [],
    ):
        plt.figure(figsize=(16, 8))

        x = range(len(series))

        plt.axhline(
            y=0,
            linestyle="--",
            linewidth=1.5,
            alpha=0.7,
        )

        plt.plot(
            x,
            series,
            linewidth=2,
        )

        if horizontal_marks is not None:
            for value in horizontal_marks:
                plt.axhline(
                    y=value,
                    color="red",
                    linestyle="--",
                    linewidth=1.5,
                )

                plt.text(
                    x=len(series) - 1,
                    y=value,
                    s=f"{value:.2f}",
                    color="red",
                    fontsize=11,
                    ha="right",
                    va="bottom",
                    bbox=dict(
                        facecolor="white",
                        edgecolor="red",
                        alpha=0.7,
                    ),
                )

        plt.title(title, fontsize=18)
        plt.xlabel(xlabel, fontsize=14)
        plt.ylabel(ylabel, fontsize=14)
        plt.xlim(0, len(series) - 1)
        plt.grid(True, which="major", alpha=0.3)
        plt.tight_layout()

        plt.savefig(rf"D:\TraderBot\LocalBackTester\Images\{plot_name}_{filename}.png")

        if show:
            plt.show()

        plt.close()

    @classmethod
    def histogram_plot(
        cls,
        distribution: dict,
        title: str,
        xlabel: str,
        filename: str,
        plot_name: str,
        show: bool = True,
    ):
        if not distribution:
            return

        lengths = sorted(distribution.keys())
        counts = [distribution[length] for length in lengths]
        plt.figure(figsize=(16, 8))
        plt.bar(
            lengths,
            counts,
            width=0.8,
        )

        for x, y in zip(lengths, counts):
            plt.text(
                x,
                y,
                str(y),
                ha="center",
                va="bottom",
                fontsize=10,
            )

        plt.title(title, fontsize=18)
        plt.xlabel(xlabel, fontsize=14)
        plt.ylabel("Occurrences", fontsize=14)
        plt.xticks(lengths)
        plt.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(rf"D:\TraderBot\LocalBackTester\Images\{plot_name}_{filename}.png")
        if show:
            plt.show()
        plt.close()


class BasePnLHistogram(BaseStatisticalAnalysis):
    @abstractmethod
    def get_category(self, timestamp: int) -> str:
        """
        Convert timestamp to category.
        """

    @abstractmethod
    def category_order(self) -> list[str]:
        """
        Ordered categories for plotting.
        """

    def aggregate(self):
        pnl_data = defaultdict(float)
        trade_count = defaultdict(int)
        wins = defaultdict(int)

        for pos in self.all_positions:
            category = self.get_category(pos.open_timestamp)
            pnl_data[category] += pos.pnl
            trade_count[category] += 1
            if pos.pnl > 0:
                wins[category] += 1
        self.pnl_data = pnl_data
        self.trade_count = trade_count
        self.wins = wins

    def analyze(self, all_positions: list[Position], *args, **kwargs) -> Any:
        self.all_positions = all_positions
        self.aggregate()

    def plot(self, plot_name: str, show: bool = True):
        if self.pnl_data is None or self.trade_count is None or self.wins is None:
            self.aggregate()

        categories = self.category_order()
        pnl_values = [float(self.pnl_data[c]) for c in categories]
        _, ax = plt.subplots(figsize=(14, 6))

        bars = ax.bar(
            categories,
            pnl_values,
        )

        ax.axhline(0, linewidth=1)
        ax.set_title(f"{self.name} {plot_name}")
        ax.set_ylabel("Total PnL")

        ax.grid(
            axis="y",
            linestyle="--",
            alpha=0.3,
        )

        # Dynamic padding
        max_abs_value = max(abs(v) for v in pnl_values)

        padding = max_abs_value * 0.05 if max_abs_value != 0 else 1

        ax.set_ylim(
            min(pnl_values) - padding * 4,
            max(pnl_values) + padding * 5,
        )

        # Labels
        for bar, category in zip(
            bars,
            categories,
        ):
            pnl = self.pnl_data[category]
            trades = self.trade_count[category]

            winrate = self.wins[category] / trades * 100 if trades > 0 else 0

            label = f"PnL: {pnl:.1f}\nTrades: {trades}\nWR: {winrate:.0f}%"

            y_position = pnl + padding if pnl >= 0 else pnl - padding

            ax.text(
                bar.get_x() + bar.get_width() / 2,
                y_position,
                label,
                ha="center",
                va="bottom" if pnl >= 0 else "top",
                fontsize=8,
            )

        plt.tight_layout()

        plt.savefig(rf"D:\TraderBot\LocalBackTester\Images\{plot_name}_{self.name}.png")
        if show:
            plt.show()


class BasePnLDistribution(BaseStatisticalAnalysis):
    def __init__(
        self,
        candles_range: int = 30,
    ):
        super().__init__()
        self.name = self.__class__.__name__
        self.candles_range = candles_range
        self.positions = []

    @abstractmethod
    def _calculate(*args, **kwargs) -> Any:
        pass

    @abstractmethod
    def give_distribution(*args, **kwargs) -> Any:
        pass

    def analyze(
        self,
        positions: list[Position],
        the_config: TradeConfig,
    ):
        if not isinstance(the_config.chart, CsvChart):
            raise ValueError(
                "Chart must be CsvChart with ticks_path for BucketPipPnlDistribution"
            )
        self.positions = positions
        self.trade_config = the_config
        for pos in positions:
            self._calculate(
                the_config=the_config,
                pos=pos,
                ticks_handler=the_config.chart.tick_handler,
            )


StatisticalIndicator: TypeAlias = (
    BasePnLDistribution | BasePnLHistogram | BaseStatisticalAnalysis
)
