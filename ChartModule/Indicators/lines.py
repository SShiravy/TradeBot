from typing import Any

from ChartModule.models import Candle, MarketSide, CandlesSource
from ChartModule.Indicators.models import IndicatorBaseModel, SupportCandleConditions
from ChartModule.plot import ChartPlot
import numpy as np


class Line:
    def __init__(
        self, source: CandlesSource, start_candle: Candle, end_candle: Candle
    ) -> None:
        self.source = source
        self.start_candle = start_candle
        self.end_candle = end_candle

    @property
    def slope(self) -> float:
        slope = round(
            self.source(self.end_candle) - self.source(self.start_candle), 10
        ) / (self.end_candle.timestamp - self.start_candle.timestamp)
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

    def plot(self, plot: ChartPlot):
        plot.draw_straight_line(self.start_candle, self.end_candle, self.source)


class TrendLine(IndicatorBaseModel):
    def __init__(
        self,
        source: CandlesSource,
        min_step: int,
        max_step: int,
        ignore_shadow_cross=True,
        support_conditions=SupportCandleConditions.RAW,
    ) -> None:
        super().__init__()
        self.source = source
        self.min_step = min_step
        self.max_step = max_step
        self.ignore_shadow_cross = ignore_shadow_cross
        self.support_conditions = support_conditions

    def export_configs(self) -> dict:
        configs = super().export_configs()
        configs.update(
            {
                "source": self.source,
                "min_step": self.min_step,
                "max_step": self.max_step,
                "ignore_shadow_cross": self.ignore_shadow_cross,
                "support_conditions": self.support_conditions,
            }
        )
        return configs

    def valid_trendline(
        self, candles: list[Candle], start_index: int, end_index: int
    ) -> Line | None:
        if len(candles) - start_index > self.max_step:
            return None
        source_list = []
        time_list = []
        start_candle = candles[start_index]
        the_line = Line(self.source, start_candle, candles[end_index])

        candle_source = self.source
        if self.source in [CandlesSource.Low, CandlesSource.Bottom]:
            cross_multiplier = 1
            if self.ignore_shadow_cross:
                candle_source = CandlesSource.Bottom
        else:
            cross_multiplier = -1
            if self.ignore_shadow_cross:
                candle_source = CandlesSource.Top

        for candle in candles[end_index:start_index:-1]:
            source_list.append(candle_source(candle))
            time_list.append(candle.timestamp)

        expected_low = (
            np.array(time_list) - candles[start_index].time.timestamp()
        ) * the_line.slope + self.source(start_candle)

        if np.any((np.array(source_list) - expected_low) * cross_multiplier < 0):
            # invalid (line crossed candles)
            return None
        return the_line

    def _calculate(self) -> list[Line]:
        lines = []
        last_index = len(self.candles) - 1
        last_candle = self.candles[last_index]

        candle_source = self.source

        if self.source in (CandlesSource.Low, CandlesSource.Bottom):
            cross_multiplier = 1
            if self.ignore_shadow_cross:
                candle_source = CandlesSource.Bottom
        else:
            cross_multiplier = -1
            if self.ignore_shadow_cross:
                candle_source = CandlesSource.Top

        last_value = self.source(last_candle)

        indices = np.arange(self.max_step + 1, dtype=np.float64)
        source_values = np.empty(self.max_step + 1, dtype=np.float64)

        count = 0

        start = last_index
        stop = max(-1, last_index - self.max_step)

        for candle_index in range(start, stop, -1):
            candle = self.candles[candle_index]

            if not self.support_conditions.check(self.candles[: candle_index + 2]):
                continue

            start_value = candle_source(candle)

            source_values[count] = start_value
            count += 1

            step = last_index - candle_index

            if step < self.min_step:
                continue

            slope = (last_value - start_value) / step

            line_values = start_value + indices[:count] * slope

            if np.any((source_values[:count] - line_values) * cross_multiplier < 0):
                continue

            lines.append(Line(self.source, candle, last_candle))

        return lines

    def _forcast(self) -> MarketSide:
        return self.data[-1].direction

    def plot(self, plot: ChartPlot):
        plot.draw_straight_line(
            self.data[-1].start_candle, self.data[-1].end_candle, self.source
        )

    def update(self, candles: list[Candle], *args, **kwargs) -> Any:
        pass
