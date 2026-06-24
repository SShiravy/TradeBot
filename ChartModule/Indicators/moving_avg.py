import math
from typing import Any
from ChartModule.models import (
    Candle,
    IndicatorBaseModel,
    MarketSide,
    IndicatorCandleSource,
)
from ChartModule.plot import ChartPlot
import pandas as pd


class SMA(IndicatorBaseModel):
    """
    Calculate Simple Moving Average (SMA) over n_bar
    values: dict{time:sma}
    """

    def __init__(self, n_bar: int, source=IndicatorCandleSource.Close) -> None:
        super().__init__()
        self.n_bar = n_bar
        self.source = source

    def export_configs(self):
        configs = super().export_configs()
        configs.update(
            {
            "n_bar": self.n_bar,
            "source":self.source.name
            }
        )
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
        sma = self.values.get(last_candle.time)
        if sma is None:
            return MarketSide.NEUTRAL
        if sma < last_candle.body_bottom:
            return MarketSide.BULLISH
        if sma > last_candle.body_top:
            return MarketSide.BEARISH
        return MarketSide.NEUTRAL

    def plot(self, plot: ChartPlot):
        plot.linear_plot(self.values.keys(), self.values.values(), f"SMA{self.n_bar}")


class EMA(IndicatorBaseModel):
    """
    Calculate Exponential Moving Average (EMA) over n_bar
    values: dict{time:ema}
    """

    def __init__(self, n_bar: int, source=IndicatorCandleSource.Close) -> None:
        super().__init__()
        self.n_bar = n_bar
        self.source = source
    
    def export_configs(self):
        configs = super().export_configs()
        configs.update(
            {
            "n_bar": self.n_bar,
            "source":self.source.name
            }
        )
        return configs

    def _calculate(self) -> dict:
        times = [c.time for c in self.candles]
        source_values = [self.source(c) for c in self.candles]
        # Create DataFrame
        df = pd.DataFrame({"source": source_values}, index=pd.to_datetime(times))
        df["sma"] = df["source"].ewm(com=self.n_bar, adjust=False).mean()
        # Return as dictionary {time: ema}
        return df["sma"].dropna().to_dict()

    def _forcast(self) -> MarketSide:
        last_candle = self.candles[-1]
        ema = self.values[last_candle.time]
        if ema < last_candle.body_bottom:
            return MarketSide.BULLISH
        elif ema > last_candle.body_top:
            return MarketSide.BEARISH
        else:
            return MarketSide.NEUTRAL

    def set(self, candles: list[Candle], *args, **kwargs) -> Any:
        self.candles = candles
        self.values = self._calculate(*args, **kwargs)
        self.last_checked_candle = candles[-1]
        return self.values

    def plot(self, plot: ChartPlot):
        plot.linear_plot(self.values.keys(), self.values.values(), f"EMA{self.n_bar}")


class WMA(IndicatorBaseModel):
    """
    Calculate Weighted Moving Average (WMA) over n_bar
    values: dict{time:wma}
    """

    def __init__(self, n_bar: int, source=IndicatorCandleSource.Close) -> None:
        super().__init__()
        self.n_bar = n_bar
        self.source = source
    
    def export_configs(self):
        configs = super().export_configs()
        configs.update(
            {
            "n_bar": self.n_bar,
            "source":self.source.name
            }
        )
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
        wma = self.values.get(last_candle.time)
        if wma is None:
            return MarketSide.NEUTRAL
        if wma < last_candle.body_bottom:
            return MarketSide.BULLISH
        if wma > last_candle.body_top:
            return MarketSide.BEARISH
        return MarketSide.NEUTRAL

    def plot(self, plot: ChartPlot):
        plot.linear_plot(
            self.values.keys(),
            self.values.values(),
            f"WMA{self.n_bar}",
            color="#FF5733",
        )

    def set(self, candles: list[Candle], *args, **kwargs) -> Any:
        self.candles = candles
        self.values = self._calculate(*args, **kwargs)
        self.last_checked_candle = candles[-1]
        return self.values


class HMA(IndicatorBaseModel):
    """
    Calculate Hull Moving Average (HMA) over n_bar
    values: dict{time:hma}
    """

    def __init__(self, n_bar: int, source=IndicatorCandleSource.Close) -> None:
        super().__init__()
        self.n_bar = n_bar
        self.source = source
    
    def export_configs(self):
        configs = super().export_configs()
        configs.update(
            {
            "n_bar": self.n_bar,
            "source":self.source.name
            }
        )
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

        last_hma = self.values.get(last.time)
        last2_hma = self.values.get(last2.time)
        if last_hma > last2_hma:
            return MarketSide.BULLISH
        else:
            return MarketSide.BEARISH

    def plot(self, plot: ChartPlot):
        green_line_time = []
        green_line_value = []

        last_value = None
        for time, value in self.values.items():
            if last_value:
                if value > last_value:
                    green_line_time.append(time)
                    green_line_value.append(value)
            last_value = value

        plot.linear_plot(
            self.values.keys(), self.values.values(), color="#F10000", thickness=3
        )
        plot.linear_plot(
            green_line_time, green_line_value, color="#0BAC00", thickness=3
        )

    def set(self, candles: list[Candle], *args, **kwargs) -> Any:
        self.candles = candles
        self.values = self._calculate(*args, **kwargs)
        self.last_checked_candle = candles[-1]
        return self.values
