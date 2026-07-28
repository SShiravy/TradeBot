from ChartModule.Indicators.models import IndicatorBaseModel
from ChartModule.models import Candle
from ChartModule.plot import ChartPlot
from typing import Any


class ATR(IndicatorBaseModel):
    """
    Average True Range (Wilder Smoothing)

    values: dict[timestamp, atr]
    """

    def __init__(self, n_bar: int = 14) -> None:
        super().__init__()
        self.data: dict[int, float]
        self.n_bar = n_bar
        self.last_close: float
        self.avg_tr: float

    def export_configs(self) -> dict:
        configs = super().export_configs()
        configs.update({"n_bar": self.n_bar})
        return configs

    @staticmethod
    def _true_range(candle: Candle, prev_close: float | None) -> float:
        if prev_close is None:
            return candle.high - candle.low
        return max(
            candle.high - candle.low,
            abs(candle.high - prev_close),
            abs(candle.low - prev_close),
        )

    def _calculate(self) -> dict:
        if len(self.candles) < self.n_bar + 1:
            return {}

        true_ranges = []
        prev_close = None
        for candle in self.candles:
            true_ranges.append(self._true_range(candle, prev_close))
            prev_close = candle.close

        values = {}

        # Initial Wilder average
        self.avg_tr = sum(true_ranges[: self.n_bar]) / self.n_bar
        values[self.candles[self.n_bar].timestamp] = self.avg_tr

        # Continue incrementally
        for i in range(self.n_bar, len(true_ranges)):
            self.avg_tr = (self.avg_tr * (self.n_bar - 1) + true_ranges[i]) / self.n_bar
            values[self.candles[i].timestamp] = self.avg_tr

        self.last_close = self.candles[-1].close

        return values

    def update(self, candles: list[Candle], *args, **kwargs) -> Any:
        if self.last_checked_candle is None:
            raise ValueError("last_checked_candle is None")

        start_index = self.find_new_candle_index(candles)

        if start_index >= len(candles):
            return

        for candle in candles[start_index:]:
            tr = self._true_range(candle, self.last_close)

            self.avg_tr = (self.avg_tr * (self.n_bar - 1) + tr) / self.n_bar

            self.data[candle.timestamp] = self.avg_tr
            self.last_close = candle.close

        self.candles = candles
        self.last_checked_candle = candles[-1]

    def plot(self, plot: ChartPlot, ax=None):
        plot.linear_plot(
            self.data.keys(), self.data.values(), legend="ATR", ax=ax
        )
