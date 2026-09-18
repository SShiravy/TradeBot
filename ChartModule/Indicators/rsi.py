from ChartModule.Indicators.models import Indicator, IndicatorPlotter, IndicatorRule
from ChartModule.models import CandlesSource, ChartData, MarketSide
from ChartModule.plot import ChartPane
import numpy as np


class RSIPlotter(IndicatorPlotter):
    def __init__(
        self,
        upper_bound: float = 30,
        lower_bound: float = 70,
        color: str = "#4341A7",
        thickness: int = 2,
        name: str | None = None,
    ) -> None:
        self.upper_bound = upper_bound
        self.lower_bound = lower_bound
        self.color = color
        self.thickness = thickness
        self.name = name

    def __call__(
        self, pane: ChartPane, indicator_data: np.ndarray, timestamps: np.ndarray
    ) -> None:
        pane.linear_plot(
            timestamps,
            indicator_data,
            legend=self.name,
            color=self.color,
            thickness=self.thickness,
        )

        start_time = int(timestamps[0])
        end_time = int(timestamps[-1])
        pane.draw_horizontal_line(
            start_time, end_time, self.upper_bound, color="#2b9000"
        )
        pane.draw_horizontal_line(
            start_time, end_time, self.lower_bound, color="#900000"
        )

        pane.extend_y_range(0, 100)


class RSI(Indicator):
    """
    Relative Strength Index (Wilder's smoothing).
    self.data: np.ndarray, same length as chartdata, aligned by index
    (first n_bar entries are NaN -- undefined until enough history exists).
    """

    def __init__(
        self,
        n_bar: int = 14,
        source: CandlesSource = CandlesSource.Close,
        upper_bound: float = 70,
        lower_bound: float = 30,
        rules: list[IndicatorRule] = [],
    ) -> None:
        super().__init__(rules=rules)
        self.n_bar = n_bar
        self.source = source
        self.upper_bound = upper_bound
        self.lower_bound = lower_bound
        self.plotter = RSIPlotter(upper_bound, lower_bound)

        # Wilder recurrence state, needed for incremental updates
        self._avg_gain: float = 0.0
        self._avg_loss: float = 0.0
        self._last_price: float = 0.0

    def export_configs(self) -> dict:
        configs = super().export_configs()
        configs.update({"n_bar": self.n_bar, "source": self.source.name})
        return configs

    @staticmethod
    def _rsi_from_averages(avg_gain: float, avg_loss: float) -> float:
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - 100 / (1 + rs)

    def _calculate(self, chartdata: ChartData, *args, **kwargs) -> np.ndarray:
        prices = self.source(chartdata)
        n = len(prices)
        result = np.full(n, np.nan, dtype=np.float64)

        if n < self.n_bar + 1:
            return result

        deltas = np.diff(prices)
        gains = np.maximum(deltas, 0.0)
        losses = np.maximum(-deltas, 0.0)

        avg_gain = gains[: self.n_bar].mean()
        avg_loss = losses[: self.n_bar].mean()
        result[self.n_bar] = self._rsi_from_averages(avg_gain, avg_loss)

        for i in range(self.n_bar, n - 1):
            avg_gain = (avg_gain * (self.n_bar - 1) + gains[i]) / self.n_bar
            avg_loss = (avg_loss * (self.n_bar - 1) + losses[i]) / self.n_bar
            result[i + 1] = self._rsi_from_averages(avg_gain, avg_loss)

        self._avg_gain = avg_gain
        self._avg_loss = avg_loss
        self._last_price = float(prices[-1])
        return result

    def _calculate_new(
        self, chartdata: ChartData, start: int, *args, **kwargs
    ) -> np.ndarray:
        prices = self.source(chartdata)
        n_new = len(chartdata) - start
        new_values = np.empty(n_new, dtype=np.float64)

        avg_gain, avg_loss, last_price = (
            self._avg_gain,
            self._avg_loss,
            self._last_price,
        )

        for i, idx in enumerate(range(start, len(chartdata))):
            price = prices[idx]
            delta = price - last_price
            gain = max(delta, 0.0)
            loss = max(-delta, 0.0)

            avg_gain = (avg_gain * (self.n_bar - 1) + gain) / self.n_bar
            avg_loss = (avg_loss * (self.n_bar - 1) + loss) / self.n_bar

            new_values[i] = self._rsi_from_averages(avg_gain, avg_loss)
            last_price = price

        self._avg_gain, self._avg_loss, self._last_price = (
            avg_gain,
            avg_loss,
            last_price,
        )
        return new_values

    def _merge(self, new_segment: np.ndarray) -> np.ndarray:
        return np.concatenate([self.data, new_segment])


class RsiBoundryRule(IndicatorRule):
    def forecast(self, indicator: RSI, *args, **kwargs) -> MarketSide:
        if (
            indicator.data is None
            or len(indicator.data) == 0
            or np.isnan(indicator.data[-1])
        ):
            return MarketSide.NEUTRAL
        last = indicator.data[-1]
        if last >= indicator.upper_bound:
            return MarketSide.BEARISH
        if last <= indicator.lower_bound:
            return MarketSide.BULLISH
        return MarketSide.NEUTRAL
