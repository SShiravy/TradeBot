import numpy as np

from ChartModule.Indicators.models import Indicator
from ChartModule.Indicators.moving_avg import IndicatorLinePlotter
from ChartModule.models import ChartData


class ATR(Indicator):
    """
    Average True Range (Wilder's smoothing).
    self.data: np.ndarray, same length as chartdata, aligned by index
    (first n_bar entries are NaN -- undefined until enough history exists).
    """

    def __init__(self, n_bar: int = 14) -> None:
        super().__init__()
        self.n_bar = n_bar
        self.plotter = IndicatorLinePlotter(color="#8d6a9f")

        # Wilder recurrence state, needed for incremental updates
        self._avg_tr: float = 0.0
        self._last_close: float = 0.0

    def export_configs(self) -> dict:
        configs = super().export_configs()
        configs.update({"n_bar": self.n_bar})
        return configs

    @staticmethod
    def _true_ranges(chartdata: ChartData) -> np.ndarray:
        high, low, close = chartdata.high, chartdata.low, chartdata.close
        prev_close = np.empty_like(close)
        prev_close[0] = np.nan
        prev_close[1:] = close[:-1]

        range_hl = high - low
        range_hc = np.abs(high - prev_close)
        range_lc = np.abs(low - prev_close)

        tr = np.maximum(range_hl, np.maximum(range_hc, range_lc))
        tr[0] = range_hl[0]  # no prior close -> plain high-low
        return tr

    def _calculate(self, chartdata: ChartData, *args, **kwargs) -> np.ndarray:
        n = len(chartdata)
        result = np.full(n, np.nan, dtype=np.float64)

        if n < self.n_bar + 1:
            return result

        true_ranges = self._true_ranges(chartdata)

        avg_tr = true_ranges[: self.n_bar].mean()
        result[self.n_bar] = avg_tr

        for i in range(self.n_bar, n - 1):
            avg_tr = (avg_tr * (self.n_bar - 1) + true_ranges[i]) / self.n_bar
            result[i + 1] = avg_tr

        self._avg_tr = avg_tr
        self._last_close = float(chartdata.close[-1])
        return result

    def _calculate_new(
        self, chartdata: ChartData, start: int, *args, **kwargs
    ) -> np.ndarray:
        high, low, close = chartdata.high, chartdata.low, chartdata.close
        n_new = len(chartdata) - start
        new_values = np.empty(n_new, dtype=np.float64)

        avg_tr, prev_close = self._avg_tr, self._last_close

        for i, idx in enumerate(range(start, len(chartdata))):
            tr = max(
                high[idx] - low[idx],
                abs(high[idx] - prev_close),
                abs(low[idx] - prev_close),
            )
            avg_tr = (avg_tr * (self.n_bar - 1) + tr) / self.n_bar
            new_values[i] = avg_tr
            prev_close = close[idx]

        self._avg_tr, self._last_close = avg_tr, prev_close
        return new_values

    def _merge(self, new_segment: np.ndarray) -> np.ndarray:
        return np.concatenate([self.data, new_segment])
