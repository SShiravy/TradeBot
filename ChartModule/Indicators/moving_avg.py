import math
from typing import Any
from ChartModule.models import (
    Candle,
    MarketSide,
    CandlesSource,
)
from ChartModule.Indicators.models import IndicatorBaseModel
from ChartModule.plot import ChartPlot
import pandas as pd


class SMA(IndicatorBaseModel):
    """
    Calculate Simple Moving Average (SMA) over n_bar
    values: dict{time:sma}
    """

    def __init__(self, n_bar: int, source=CandlesSource.Close) -> None:
        super().__init__()
        self.n_bar = n_bar
        self.source = source

    def export_configs(self):
        configs = super().export_configs()
        configs.update({"n_bar": self.n_bar, "source": self.source.name})
        return configs

    def _calculate(self) -> dict:
        if len(self.candles) < self.n_bar:
            return {}
        sma_values = {}
        values = []
        for i, candle in enumerate(self.candles):
            values.append(self.source(candle))
            if i < self.n_bar:
                continue
            sma = sum(values[i - self.n_bar + 1 :]) / (self.n_bar)
            sma_values[candle.time] = sma

        return sma_values

    def _forcast(self) -> MarketSide:
        last_candle = self.candles[-1]
        sma = self.data.get(last_candle.timestamp)
        if sma is None:
            return MarketSide.NEUTRAL
        if sma < last_candle.body_bottom:
            return MarketSide.BULLISH
        if sma > last_candle.body_top:
            return MarketSide.BEARISH
        return MarketSide.NEUTRAL

    def plot(self, plot: ChartPlot):
        plot.linear_plot(self.data.keys(), self.data.values(), f"SMA{self.n_bar}")


class EMA(IndicatorBaseModel):
    """
    Calculate Exponential Moving Average (EMA) over n_bar
    values: dict{timestamp:ema}
    """

    def __init__(self, n_bar: int, source=CandlesSource.Close) -> None:
        super().__init__()
        self.n_bar = n_bar
        self.source = source

    def export_configs(self):
        configs = super().export_configs()
        configs.update({"n_bar": self.n_bar, "source": self.source.name})
        return configs

    def _calculate(self) -> dict:
        source_values = [self.source(c) for c in self.candles]
        ema_values = (
            pd.Series(source_values).ewm(span=self.n_bar, adjust=False).mean().to_numpy()
        )
        return {candle.timestamp: ema for candle, ema in zip(self.candles, ema_values)}

    def _forcast(self) -> MarketSide:
        last_candle = self.candles[-1]
        ema = self.data[last_candle.timestamp]
        if ema < last_candle.body_bottom:
            return MarketSide.BULLISH
        elif ema > last_candle.body_top:
            return MarketSide.BEARISH
        else:
            return MarketSide.NEUTRAL

    def update(self, candles: list[Candle], *args, **kwargs) -> Any:
        if not self.last_checked_candle:
            raise ValueError("update with None last_checked_candle!!")
        if candles[-1].timestamp == self.last_checked_candle.timestamp:
            return

        alpha = 2 / (1 + self.n_bar)
        old_len = len(self.candles)
        self.candles = candles

        for candle in candles[old_len:]:
            prev_ema = self.data[self.last_checked_candle.timestamp]

            current_price = self.source(candle)

            ema = alpha * current_price + (1 - alpha) * prev_ema

            self.data[candle.timestamp] = ema
            self.last_checked_candle = candle

    def plot(self, plot: ChartPlot):
        plot.linear_plot(self.data.keys(), self.data.values(), f"EMA{self.n_bar}")


class WMA(IndicatorBaseModel):
    """
    Calculate Weighted Moving Average (WMA) over n_bar
    values: dict{time:wma}
    """

    def __init__(self, n_bar: int, source=CandlesSource.Close) -> None:
        super().__init__()
        self.n_bar = n_bar
        self.source = source

    def export_configs(self):
        configs = super().export_configs()
        configs.update({"n_bar": self.n_bar, "source": self.source.name})
        return configs

    def _calculate(self) -> dict:
        if len(self.candles) < self.n_bar:
            return {}

        weights = list(range(1, self.n_bar + 1))
        weight_sum = self.n_bar * (self.n_bar + 1) // 2

        wma = {}

        for i in range(len(self.candles)):
            if i < self.n_bar - 1:
                continue

            weighted_sum = 0.0
            for w, j in zip(weights, range(i - self.n_bar + 1, i + 1)):
                weighted_sum += self.source(self.candles[j]) * w

            wma[self.candles[i].time] = weighted_sum / weight_sum

        return wma

    def _forcast(self) -> MarketSide:
        last_candle = self.candles[-1]
        wma = self.data.get(last_candle.time)
        if wma is None:
            return MarketSide.NEUTRAL
        if wma < last_candle.body_bottom:
            return MarketSide.BULLISH
        if wma > last_candle.body_top:
            return MarketSide.BEARISH
        return MarketSide.NEUTRAL

    def plot(self, plot: ChartPlot):
        plot.linear_plot(
            self.data.keys(),
            self.data.values(),
            f"WMA{self.n_bar}",
            color="#FF5733",
        )


class HMA(IndicatorBaseModel):
    """
    Calculate Hull Moving Average (HMA) over n_bar
    values: dict{time:hma}
    """

    def __init__(self, n_bar: int, source=CandlesSource.Close) -> None:
        super().__init__()
        self.n_bar = n_bar
        self.source = source

    def export_configs(self):
        configs = super().export_configs()
        configs.update({"n_bar": self.n_bar, "source": self.source.name})
        return configs

    def _calculate(self) -> dict:
        if len(self.candles) < self.n_bar:
            return {}
        sqrt_p = int(math.sqrt(self.n_bar))

        wma_half = WMA(self.n_bar // 2, self.source).set(self.candles)
        wma_full = WMA(self.n_bar, self.source).set(self.candles)

        times = [c.time for c in self.candles]

        diff = {}
        for t in times:
            wh = wma_half.get(t)
            wf = wma_full.get(t)

            if wh is None or wf is None:
                continue
            diff[t] = 2 * wh - wf

        weights = list(range(1, sqrt_p + 1))
        weight_sum = sqrt_p * (sqrt_p + 1) // 2

        result = {}

        for i, t in enumerate(times):
            if i < (self.n_bar - 1) + (sqrt_p - 1):
                result[t] = None
                continue

            weighted_sum = 0.0
            for w, j in zip(weights, range(i - sqrt_p + 1, i + 1)):
                val = diff[times[j]]
                weighted_sum += val * w

            result[t] = weighted_sum / weight_sum

        return result

    def _forcast(self) -> MarketSide:
        last = self.candles[-1]
        last2 = self.candles[-2]

        last_hma = self.data.get(last.time)
        last2_hma = self.data.get(last2.time)
        if last_hma > last2_hma:
            return MarketSide.BULLISH
        else:
            return MarketSide.BEARISH

    def plot(self, plot: ChartPlot):
        green_line_time = []
        green_line_value = []

        last_value = None
        for time, value in self.data.items():
            if last_value:
                if value > last_value:
                    green_line_time.append(time)
                    green_line_value.append(value)
            last_value = value

        plot.linear_plot(
            self.data.keys(), self.data.values(), color="#F10000", thickness=3
        )
        plot.linear_plot(
            green_line_time, green_line_value, color="#0BAC00", thickness=3
        )
