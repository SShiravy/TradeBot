from ChartModule.models import TickPrice, MarketSide
from ChartModule.Indicators.models import IndicatorBaseModel
from ChartModule.plot import ChartPlot
from datetime import datetime
from enum import Enum
import numpy as np


class FiboLevels(Enum):
    LEVEL_0 = 0.0
    LEVEL_236 = 0.236
    LEVEL_382 = 0.382
    LEVEL_5 = 0.5
    LEVEL_618 = 0.618
    LEVEL_786 = 0.786
    LEVEL_1 = 1.0
    LEVEL_1_618 = 1.618
    LEVEL_2_618 = 2.618

    @property
    def color(self):
        match self:
            case FiboLevels.LEVEL_0:
                return "#8B8B8B"
            case FiboLevels.LEVEL_236:
                return "#E71919"
            case FiboLevels.LEVEL_382:
                return "#FF7513"
            case FiboLevels.LEVEL_5:
                return "#47FF50"
            case FiboLevels.LEVEL_618:
                return "#59A635"
            case FiboLevels.LEVEL_786:
                return "#65ACF7"
            case FiboLevels.LEVEL_1:
                return "#464646"
            case FiboLevels.LEVEL_1_618:
                return "#0069D8"
            case FiboLevels.LEVEL_2_618:
                return "#9C0000"


class FibonacciRetracement(IndicatorBaseModel):
    def __init__(
        self,
        start_tick: TickPrice,
        end_tick: TickPrice,
        fibonacci_levels: list[FiboLevels] = list(FiboLevels),
    ) -> None:
        super().__init__()
        self.start_tick = start_tick
        self.end_tick = end_tick
        self.fibonacci_levels = fibonacci_levels

        self.ratios = np.array([level.value for level in fibonacci_levels])

        self.data = self._calculate()

    def _calculate(self):
        diff = self.start_tick.price - self.end_tick.price
        return self.end_tick.price + self.ratios * diff

    def give_level_price(self, level: FiboLevels):
        diff = self.start_tick.price - self.end_tick.price
        return round(self.end_tick.price + level.value * diff, 4)

    def _forcast(self) -> MarketSide:
        return MarketSide.NEUTRAL

    def forcast(
        self, ticks: list[float], level: FiboLevels = FiboLevels.LEVEL_618
    ) -> MarketSide:
        factor = 1 if self.end_tick.price > self.start_tick.price else -1
        ticks_array = np.array(ticks)
        trigger = self.give_level_price(level)
        res = (ticks_array - trigger) * factor
        if np.all(res > 0):
            return MarketSide.NEUTRAL
        if factor == 1:
            return MarketSide.BULLISH
        else:
            return MarketSide.BEARISH

    def plot(self, plot: ChartPlot, end_time: datetime | None = None):
        end_time = end_time if end_time else self.end_tick.time
        for level in self.fibonacci_levels:
            end_price = self.data[self.fibonacci_levels.index(level)]
            plot.draw_line(
                self.start_tick.time,
                end_price,
                end_time,
                end_price,
                color=level.color,
                width=3,
            )
