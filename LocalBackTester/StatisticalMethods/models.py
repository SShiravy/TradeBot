from abc import ABC, abstractmethod
from collections import defaultdict
import matplotlib.pyplot as plt


class BasePnLHistogram(ABC):
    def __init__(
        self,
        pnl_list: list[float],
        timestamps: list[int],
        plot_name: str,
    ):
        if len(pnl_list) != len(timestamps):
            raise ValueError("pnl_list and timestamps must have same length")

        self.pnl_list = pnl_list
        self.timestamps = timestamps
        self.plot_name = plot_name

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

        for pnl, ts in zip(
            self.pnl_list,
            self.timestamps,
        ):
            category = self.get_category(ts)

            pnl_data[category] += pnl
            trade_count[category] += 1

            if pnl > 0:
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

        ax.set_title(f"{self.__class__.__name__}_{self.plot_name}")
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
