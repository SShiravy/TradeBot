from ChartModule.models import (
    Candle,
    MarketSide,
    IndicatorBaseModel,
    IndicatorCandleSource,
)
from ChartModule.Indicators.models import SupportConditions
from ChartModule.plot import PlotChart
from copy import copy
import numpy as np


class Line:
    def __init__(
        self, source: IndicatorCandleSource, start_candle: Candle, end_candle: Candle
    ) -> None:
        self.source = source
        self.start_candle = start_candle
        self.end_candle = end_candle

    @property
    def slope(self) -> float:
        slope = round(
            self.source(self.end_candle) - self.source(self.start_candle), 10
        ) / (self.end_candle.time.timestamp() - self.start_candle.time.timestamp())
        return slope

    def direction(self) -> MarketSide:
        if not self.start_candle or not self.end_candle:
            return MarketSide.NEUTRAL
        if self.source(self.start_candle) > self.source(self.end_candle):
            return MarketSide.BEARISH
        elif self.source(self.start_candle) < self.source(self.end_candle):
            return MarketSide.BULLISH
        else:
            return MarketSide.NEUTRAL

    def plot(self, plot: PlotChart):
        plot.draw_straight_line(self.start_candle, self.end_candle, self.source)


class TrendLine(IndicatorBaseModel):
    def __init__(
        self,
        source: IndicatorCandleSource,
        min_step: int,
        max_step: int,
        ignore_shadow_cross=True,
        support_conditions=SupportConditions.RAW,
    ) -> None:
        super().__init__()
        self.source = source
        self.min_step = min_step
        self.max_step = max_step
        self.ignore_shadow_cross = ignore_shadow_cross
        self.support_conditions = support_conditions

    def valid_trendline(
        self, candles: list[Candle], start_index: int, end_index: int
    ) -> Line | None:
        if len(candles) - start_index > self.max_step:
            return None
        source_list = []
        time_list = []
        start_candle = candles[start_index]
        the_line = Line(self.source, start_candle, candles[end_index])

        candle_source = copy(self.source)
        if self.source in [IndicatorCandleSource.Low, IndicatorCandleSource.Bottom]:
            cross_multiplier = 1
            if self.ignore_shadow_cross:
                candle_source = IndicatorCandleSource.Bottom
        else:
            cross_multiplier = -1
            if self.ignore_shadow_cross:
                candle_source = IndicatorCandleSource.Top

        for candle in candles[end_index:start_index:-1]:
            source_list.append(candle_source(candle))
            time_list.append(candle.time.timestamp())

        expected_low = (
            np.array(time_list) - candles[start_index].time.timestamp()
        ) * the_line.slope + self.source(start_candle)

        if np.any((np.array(source_list) - expected_low) * cross_multiplier < 0):
            # invalid (line crossed candles)
            return None
        return the_line

    def _calculate(self) -> list[Line]:
        lines = []
        last_candle = self.candles[-1]
        len_candles = len(self.candles)
        source_list = []
        time_list = []

        candle_source = copy(self.source)

        if self.source in [IndicatorCandleSource.Low, IndicatorCandleSource.Bottom]:
            cross_multiplier = 1
            if self.ignore_shadow_cross:
                candle_source = IndicatorCandleSource.Bottom
        else:
            cross_multiplier = -1
            if self.ignore_shadow_cross:
                candle_source = IndicatorCandleSource.Top

        for candle in self.candles[-self.min_step : -self.max_step : -1]:
            candle_index = self.candles.index(candle)
            if len_candles - candle_index > self.max_step:
                break
            if not self.support_conditions.check(self.candles[: candle_index + 2]):
                continue

            source_list.append(candle_source(candle))
            time_list.append(candle.time.timestamp())
            if len_candles - 1 - candle_index < self.min_step:
                continue

            the_line = Line(self.source, candle, last_candle)

            expected_low = (
                np.array(time_list) - candle.time.timestamp()
            ) * the_line.slope + self.source(candle)

            if np.any((np.array(source_list) - expected_low) * cross_multiplier < 0):
                # invalid (line crossed candles)
                continue
            lines.append(the_line)

        return lines

    def _forcast(self) -> MarketSide:
        return self.values[-1].direction

    def plot(self, plot: PlotChart):
        plot.draw_straight_line(
            self.values[-1].start_candle, self.values[-1].end_candle, self.source
        )
