from ChartModule.models import (
    IndicatorBaseModel,
    MarketSide,
    Candle,
    IndicatorCandleSource,
)
from ChartModule.plot import PlotChart
from ChartModule.Indicators.models import SupportConditions
import numpy as np


class Pivot(IndicatorBaseModel):
    """
    Find All Pivot Candles
    values: list[Candle]
    """

    def __init__(
        self,
        source: IndicatorCandleSource,
        left: int = 3,
        right: int = 3,
        down_pivot=True,
        support_conditions: SupportConditions = SupportConditions.RAW,
    ) -> None:
        super().__init__()
        self.source = source
        self.right = right
        self.left = left
        self.down_pivot = down_pivot
        self.support_conditions = support_conditions
        self._biggest_pivot = None

    def _calculate(self) -> list[Candle]:
        all_source = []
        all_pivots = []
        n_candle_jump = 0
        factor = -1 if self.down_pivot else 1
        for index in range(0, len(self.candles)):
            all_source.append(self.source(self.candles[index]))
            if index < self.left + self.right:
                continue
            if n_candle_jump > 0:
                n_candle_jump -= 1
                continue
            candle_index = index - self.right
            candle_source = all_source[candle_index]
            res = (
                np.array(all_source[candle_index - self.left : index]) - candle_source
            ) * factor
            if np.all(res <= 0):
                if not self.support_conditions.check(self.candles[: candle_index + 2]):
                    continue
                all_pivots.append(self.candles[candle_index])
                n_candle_jump += self.left
        return all_pivots

    # def update(self, candles: list[Candle], *args, **kwargs):
    #     self.candles
    #     self.values = self._calculate()
    # TODO: Optimize calculation for new candles only

    def check_candle_is_pivot(
        self,
        candle_index: int,
        candles: list[Candle],
    ) -> bool:
        self.update(candles)
        if self.candles[candle_index] in self.values:
            return True
        return False

    def _forcast(self) -> MarketSide:
        return MarketSide.NEUTRAL

    def plot(self, plot: PlotChart, all=False):
        if all:
            for candle in self.values:
                plot.mark_candle(candle, self.source)
        else:
            plot.mark_candle(self.values[-1], self.source)

    @property
    def major_pivot(self) -> Candle:
        if self._biggest_pivot:
            return self._biggest_pivot
        factor = -1 if self.down_pivot else 1
        self._biggest_pivot = self.values[0]
        for pivot in self.values[1:]:
            if (self.source(pivot) - self.source(self._biggest_pivot)) * factor > 0:
                self._biggest_pivot = pivot
        return self._biggest_pivot
