import numpy as np
from ChartModule.models import (
    ChartData,
    CandlesSource,
    MarketSide,
)
from ChartModule.Indicators.models import Indicator, IndicatorPlotter, IndicatorRule
from ChartModule.plot import ChartPane
import pandas as pd


class IndicatorLinePlotter(IndicatorPlotter):
    def __init__(
        self, color: str = "#650087", thickness: int = 2, name: str | None = None
    ) -> None:
        self.color = color
        self.thickness = thickness
        self.name = name

    def __call__(
        self, pane: ChartPane, indicator_data: pd.Series, *args, **kwargs
    ) -> None:
        pane.linear_plot(
            indicator_data.index.to_numpy(),
            indicator_data.to_numpy(),
            legend=self.name,
            color=self.color,
            thickness=self.thickness,
        )

        pane.extend_y_range(float(indicator_data.min()), float(indicator_data.max()))


class WMA(Indicator):
    def __init__(self, n_bar: int, source: CandlesSource = CandlesSource.Close) -> None:
        super().__init__()
        self.n_bar = n_bar
        self.source = source
        self.plotter = IndicatorLinePlotter(color=self._default_color())

    def _default_color(self) -> str:
        return "#2a9d8f"

    def export_configs(self) -> dict:
        configs = super().export_configs()
        configs.update({"n_bar": self.n_bar, "source": self.source.name})
        return configs

    def _weights(self) -> np.ndarray:
        return np.arange(1, self.n_bar + 1, dtype=np.float64)

    @staticmethod
    def _weighted_rolling(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
        n_bar = len(weights)
        weight_sum = weights.sum()
        result = np.full(len(values), np.nan, dtype=np.float64)
        for i in range(n_bar - 1, len(values)):
            window = values[i - n_bar + 1 : i + 1]
            result[i] = np.dot(window, weights) / weight_sum
        return result

    def _calculate(self, chartdata: ChartData, *args, **kwargs) -> pd.Series:
        values = self.source(chartdata)
        result = self._weighted_rolling(values, self._weights())
        return pd.Series(result, index=chartdata.timestamps)

    def _calculate_new(
        self, chartdata: ChartData, start: int, *args, **kwargs
    ) -> pd.Series:
        weights = self._weights()
        lookback = len(weights) - 1
        slice_start = max(0, start - lookback)

        values = self.source(chartdata)[slice_start:]
        result = self._weighted_rolling(values, weights)

        offset = start - slice_start
        return pd.Series(result[offset:], index=chartdata.timestamps[start:])

    def _merge(self, new_segment: pd.Series) -> pd.Series:
        return pd.concat([self.data, new_segment])


class SMA(WMA):
    def _default_color(self) -> str:
        return "#0077b6"

    def _weights(self) -> np.ndarray:
        return np.ones(self.n_bar, dtype=np.float64)


class EMA(WMA):
    def _default_color(self) -> str:
        return "#e63946"

    def _calculate(self, chartdata: ChartData, *args, **kwargs) -> pd.Series:
        values = self.source(chartdata)
        ema = pd.Series(values).ewm(span=self.n_bar, adjust=False).mean().to_numpy()
        return pd.Series(ema, index=chartdata.timestamps)

    def _calculate_new(
        self, chartdata: ChartData, start: int, *args, **kwargs
    ) -> pd.Series:
        alpha = 2 / (1 + self.n_bar)
        values = self.source(chartdata)

        prev_ema = self.data.iloc[-1]
        new_values = np.empty(len(chartdata) - start, dtype=np.float64)
        for i, idx in enumerate(range(start, len(chartdata))):
            prev_ema = alpha * values[idx] + (1 - alpha) * prev_ema
            new_values[i] = prev_ema

        return pd.Series(new_values, index=chartdata.timestamps[start:])

    def _merge(self, new_segment: pd.Series) -> pd.Series:
        return pd.concat([self.data, new_segment])


class HMA(WMA):
    def _default_color(self) -> str:
        return "#f4a261"

    def _calculate(self, chartdata: ChartData, *args, **kwargs) -> pd.Series:
        values = self.source(chartdata)
        return self._hma_from_values(values, chartdata.timestamps)

    def _hma_from_values(self, values: np.ndarray, timestamps: np.ndarray) -> pd.Series:
        half_n = max(1, self.n_bar // 2)
        sqrt_n = max(1, int(round(self.n_bar**0.5)))

        wma_half = self._weighted_rolling(
            values, np.arange(1, half_n + 1, dtype=np.float64)
        )
        wma_full = self._weighted_rolling(
            values, np.arange(1, self.n_bar + 1, dtype=np.float64)
        )
        raw = 2 * wma_half - wma_full

        result = self._weighted_rolling(raw, np.arange(1, sqrt_n + 1, dtype=np.float64))
        return pd.Series(result, index=timestamps)

    def _calculate_new(
        self, chartdata: ChartData, start: int, *args, **kwargs
    ) -> pd.Series:
        sqrt_n = max(1, int(round(self.n_bar**0.5)))
        lookback = self.n_bar + sqrt_n  # generous margin covering both nested windows
        slice_start = max(0, start - lookback)

        values = self.source(chartdata)[slice_start:]
        timestamps = chartdata.timestamps[slice_start:]
        full_result = self._hma_from_values(values, timestamps)

        offset = start - slice_start
        return full_result.iloc[offset:]

    def _merge(self, new_segment: pd.Series) -> pd.Series:
        return pd.concat([self.data, new_segment])


class PriceCrossRule(IndicatorRule):
    def forecast(self, indicator: Indicator, *args, **kwargs) -> MarketSide:
        if (
            indicator.data is None
            or indicator.chartdata is None
            or len(indicator.chartdata) < 2
        ):
            return MarketSide.NEUTRAL

        close = indicator.chartdata.close
        line = indicator.data

        last, prev = line.iloc[-1], line.iloc[-2]
        if np.isnan(last) or np.isnan(prev):
            return MarketSide.NEUTRAL

        prev_above = close[-2] > prev
        curr_above = close[-1] > last

        if not prev_above and curr_above:
            return MarketSide.BULLISH
        if prev_above and not curr_above:
            return MarketSide.BEARISH
        return MarketSide.NEUTRAL


class SlopeRule(IndicatorRule):
    def __init__(self, lookback: int = 3) -> None:
        self.lookback = lookback

    def forecast(self, indicator: Indicator, *args, **kwargs) -> MarketSide:
        if indicator.data is None or len(indicator.data) <= self.lookback:
            return MarketSide.NEUTRAL

        recent = indicator.data.iloc[-self.lookback - 1 :]
        if recent.isna().any():
            return MarketSide.NEUTRAL

        if recent.iloc[-1] > recent.iloc[0]:
            return MarketSide.BULLISH
        if recent.iloc[-1] < recent.iloc[0]:
            return MarketSide.BEARISH
        return MarketSide.NEUTRAL
