from typing import Any

from LocalBackTester.models import CsvChart, TickDataHandler
from TradingModule.models import Position
from TradingModule.trader_bot import TradeConfig
from abc import ABC, abstractmethod
from collections import defaultdict
import matplotlib.pyplot as plt
from copy import deepcopy


class BasePnLHistogram(ABC):
    def __init__(
        self,
        all_positions: list[Position],
        plot_name: str,
    ):
        self.all_positions = all_positions
        self.plot_name = plot_name
        self.name = self.__class__.__name__

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

        return pnl_data, trade_count, wins

    def plot(self, show: bool = True):
        pnl_data, trade_count, wins = self.aggregate()

        categories = self.category_order()

        pnl_values = [float(pnl_data[c]) for c in categories]

        fig, ax = plt.subplots(figsize=(14, 6))

        bars = ax.bar(
            categories,
            pnl_values,
        )

        ax.axhline(0, linewidth=1)

        ax.set_title(f"{self.name} {self.plot_name}")
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
            pnl = pnl_data[category]
            trades = trade_count[category]

            winrate = wins[category] / trades * 100 if trades > 0 else 0

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

        plt.savefig(
            rf"D:\TraderBot\LocalBackTester\Images\{self.__class__.__name__}_{self.plot_name}.png"
        )
        if show:
            plt.show()


class BasePnLDistribution(ABC):
    def __init__(
        self,
        plot_name: str,
        candles_range: int = 5,
        trade_config: TradeConfig | None = None,
    ):
        self.name = self.__class__.__name__
        self.candles_range = candles_range
        self.trade_config = trade_config
        self.positions = []
        self.plot_name = plot_name

    @abstractmethod
    def _calculate(*args, **kwargs) -> Any:
        pass

    @abstractmethod
    def give_distribution(*args, **kwargs) -> Any:
        pass

    @abstractmethod
    def plot(show=True):
        pass

    def set_method(self, the_config: TradeConfig, positions: list[Position], ticks_handler:TickDataHandler|None=None):
        if not ticks_handler:
            if (
            not isinstance(the_config.chart, CsvChart)
            or the_config.chart.ticks_path is None):
                raise ValueError(
                    "Chart must be CsvChart with ticks_path for BucketPipPnlDistribution"
                )
            else:
                ticks_handler = TickDataHandler(parquet_path=the_config.chart.ticks_path)
        self.positions = positions
        self.trade_config = the_config
        for pos in positions:
            self._calculate(the_config=the_config, pos=pos, ticks_handler=ticks_handler)
