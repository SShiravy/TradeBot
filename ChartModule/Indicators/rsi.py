from ChartModule.Indicators.models import IndicatorBaseModel
from ChartModule.models import CandlesSource
from ChartModule.plot import ChartPlot
import numpy as np


class RSI(IndicatorBaseModel):
    """
    Relative Strength Index

    values: dict[timestamp, rsi]
    """

    def __init__(
        self,
        n_bar: int = 14,
        source: CandlesSource = CandlesSource.Close,
        upper_bond=70,
        lower_bond=30,
    ):
        super().__init__()
        self.data: dict[int, float]
        self.n_bar = n_bar
        self.source = source
        self.upper_bond = upper_bond
        self.lower_bond = lower_bond
        self.last_price: float
        self.avg_gain: float
        self.avg_loss: float

    def export_configs(self):
        configs = super().export_configs()
        configs.update(
            {
                "n_bar": self.n_bar,
                "source": self.source.name,
            }
        )
        return configs

    def _calculate(self) -> dict:
        if len(self.candles) < self.n_bar + 1:
            return {}
        prices = []
        timestamps = []
        for candle in self.candles:
            prices.append(self.source(candle))
            timestamps.append(candle.timestamp)

        prices = np.array(prices, dtype=float)

        deltas = np.diff(prices)
        gains = np.maximum(deltas, 0)
        losses = np.maximum(-deltas, 0)

        values = {timestamp: 50.0 for timestamp in timestamps[: self.n_bar + 1]}

        # Initial Wilder averages
        self.avg_gain = gains[: self.n_bar].mean()
        self.avg_loss = losses[: self.n_bar].mean()

        if self.avg_loss == 0:
            values[timestamps[self.n_bar]] = 100.0
        else:
            rs = self.avg_gain / self.avg_loss
            values[timestamps[self.n_bar]] = 100 - 100 / (1 + rs)

        # Continue incrementally
        for i in range(self.n_bar + 1, len(gains)):
            self.avg_gain = (self.avg_gain * (self.n_bar - 1) + gains[i]) / self.n_bar

            self.avg_loss = (self.avg_loss * (self.n_bar - 1) + losses[i]) / self.n_bar

            if self.avg_loss == 0:
                rsi = 100.0
            else:
                rs = self.avg_gain / self.avg_loss
                rsi = 100 - 100 / (1 + rs)

            values[timestamps[i + 1]] = rsi

        self.last_price = prices[-1]

        return values

    def update(self, candles, *args, **kwargs):
        if self.last_checked_candle is None:
            raise ValueError("last_checked_candle is None")

        start_index = self.find_new_candle_index(candles)

        if start_index >= len(candles):
            return

        for candle in candles[start_index:]:
            current_price = self.source(candle)

            delta = current_price - self.last_price

            gain = max(delta, 0.0)
            loss = max(-delta, 0.0)

            self.avg_gain = (self.avg_gain * (self.n_bar - 1) + gain) / self.n_bar

            self.avg_loss = (self.avg_loss * (self.n_bar - 1) + loss) / self.n_bar

            if self.avg_loss == 0:
                rsi = 100.0
            else:
                rs = self.avg_gain / self.avg_loss
                rsi = 100 - 100 / (1 + rs)

            self.data[candle.timestamp] = rsi

            self.last_price = current_price

        self.candles = candles
        self.last_checked_candle = candles[-1]

    def plot(self, plot: ChartPlot, ax=None):
        start_time = self.candles[0].time
        end_time = self.candles[-1].time
        plot.draw_line(
            start_time,
            self.upper_bond,
            end_time,
            self.upper_bond,
            color="#2b9000",
            width=2,
            ax=ax,
        )
        plot.draw_line(
            start_time,
            self.lower_bond,
            end_time,
            self.lower_bond,
            color="#900000",
            width=2,
            ax=ax,
        )
