from LocalBackTester.StatisticalMethods.models import BasePnLDistribution
from LocalBackTester.models import TickDataHandler
from TradingModule.models import OrderSide, Position
from TradingModule.trader_bot import TradeConfig
from matplotlib import pyplot as plt
import numpy as np
import logging


logger = logging.getLogger("BucketPipPnlDistribution")


class BucketPipPnlDistribution(BasePnLDistribution):
    def __init__(
        self,
        max_pip_bucket: int,
        candles_range: int,
        plot_name: str,
        trade_config: TradeConfig | None = None,
    ):
        super().__init__(plot_name, candles_range, trade_config)
        self.name = "Pip Pnl Distribution"
        self.max_pip_bucket = max_pip_bucket
        self.long_max_profit_pip_list = []
        self.short_max_profit_pip_list = []

        # TODO: add one to one list for extra information

    def _calculate(
        self,
        the_config: TradeConfig,
        pos: Position,
        ticks_handler: TickDataHandler,
        *args,
        **kwargs,
    ):
        seconds_check_range = (
            the_config.chart.timeframe.minutes * 60 * self.candles_range
        )
        pos_ticks = ticks_handler.get_ticks_from_timstamp_range(
            pos.open_timestamp, pos.open_timestamp + seconds_check_range
        )
        # If pos is Buy, then you can sell in ask price & otherwise in bid price
        if pos.side is OrderSide.BUY:
            prices = pos_ticks["ask"].to_numpy()
            logger.debug(f"{prices=}")
            hit_indices = np.where(prices <= pos.stoploss)[0]
            logger.debug(f"{hit_indices =}")
            if hit_indices.size == 0 or hit_indices[0] == 0:
                return
            hit_index = hit_indices[0]
            prices = prices[:hit_index]
            if prices.size == 0:
                return
            logger.debug(f"{prices=} | by hit_index")
            max_profit = (prices - pos.entry_price).max()
            if max_profit <= 0:
                return
            self.long_max_profit_pip_list.append(max_profit * 10)

        else:  # pos.side is OrderSide.SELL
            prices = pos_ticks["bid"].to_numpy()
            hit_indices = np.where(prices >= pos.stoploss)[0]
            logger.debug(f"{hit_indices=}")
            if hit_indices.size == 0 or hit_indices[0] == 0:
                return
            hit_index = hit_indices[0]
            prices = prices[:hit_index]
            if prices.size == 0:
                return
            logger.debug(f"{prices=} | by hit_index")
            max_profit = (prices - pos.entry_price).min() * -1
            if max_profit <= 0:
                return
            self.short_max_profit_pip_list.append(max_profit * 10)

    def give_distribution(self, *args, **kwargs):
        """
        return:
            long_hist, short_hist, bins
        """
        total_max_profit_pip_list = (
            self.long_max_profit_pip_list + self.short_max_profit_pip_list
        )
        pip_step = 5
        bins = np.arange(0, max(total_max_profit_pip_list) + pip_step, pip_step)
        long_hist, _ = np.histogram(self.long_max_profit_pip_list, bins=bins)
        short_hist, _ = np.histogram(self.short_max_profit_pip_list, bins=bins)
        return {"long": long_hist, "short": short_hist, "bins": bins}

    def give_cumulative_distribution(self):
        all_profits = np.array(
            self.long_max_profit_pip_list + self.short_max_profit_pip_list
        )
        levels = np.arange(int(all_profits.min()), int(all_profits.max()) + 1)
        long_profits = np.array(self.long_max_profit_pip_list)
        short_profits = np.array(self.short_max_profit_pip_list)

        long_counts = np.array([(long_profits >= level).sum() for level in levels])

        short_counts = np.array([(short_profits >= level).sum() for level in levels])

        return {"long": long_counts, "short": short_counts, "levels": levels}

    def plot(self, show=True):
        distribution = self.give_distribution()
        long_hist = distribution["long"]
        short_hist = distribution["short"]
        bins = distribution["bins"]

        width = 2.5

        plt.figure(figsize=(14, 7))

        bucket_upper_bounds = bins[1:]

        plt.bar(
            bucket_upper_bounds,
            long_hist,
            color="limegreen",
            alpha=0.8,
            label="Long",
            width=width,
        )

        plt.bar(
            bucket_upper_bounds,
            short_hist,
            bottom=long_hist,
            color="tomato",
            alpha=0.8,
            label="Short",
            width=width,
        )

        plt.xticks(
            bucket_upper_bounds, [f"{x:.1f}" for x in bucket_upper_bounds], rotation=90
        )
        plt.title(self.name + " " + self.plot_name)
        plt.xlabel("Pip Pnl Bucket")
        plt.ylabel("Count")
        plt.legend()
        plt.tight_layout()

        plt.savefig(
            rf"D:\TraderBot\LocalBackTester\Images\{self.__class__.__name__}_{self.plot_name}.png"
        )

        if show:
            plt.show()

        # Cumulative -----------------
        cum_distribution = self.give_cumulative_distribution()
        long_counts = cum_distribution["long"]
        short_counts = cum_distribution["short"]
        levels = cum_distribution["levels"]

        plt.figure(figsize=(14, 7))

        plt.plot(levels, long_counts, label="Long", linewidth=2, color="limegreen")

        plt.plot(levels, short_counts, label="Short", linewidth=2, color="tomato")

        plt.plot(levels, long_counts + short_counts, label="total", linewidth=3)

        plt.title(self.name + " " + self.plot_name)
        plt.xlabel("Cumulative Pip Pnl Bucket")
        plt.ylabel("Count")
        plt.legend()
        plt.tight_layout()

        plt.savefig(
            rf"D:\TraderBot\LocalBackTester\Images\{self.__class__.__name__}_Cumulative_{self.plot_name}.png"
        )

        if show:
            plt.show()
