from ChartModule.models import IndicatorBaseModel, MarketSide, IndicatorCandleSource
from ChartModule.plot import PlotChart
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
        sma = self.values[last_candle.time]
        if sma < last_candle.body_bottom:
            return MarketSide.BULLISH
        elif sma > last_candle.body_top:
            return MarketSide.BEARISH
        else:
            return MarketSide.NEUTRAL

    def plot(self, plot: PlotChart):
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

    def plot(self, plot: PlotChart):
        plot.linear_plot(self.values.keys(), self.values.values(), f"EMA{self.n_bar}")
