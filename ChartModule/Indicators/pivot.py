from ChartModule.models import (
    MarketSide,
    Candle,
    CandlesSource,
)
from ChartModule.plot import ChartPlot
from ChartModule.Indicators.models import Indicator, SupportCandlesPattern
import numpy as np


class Pivot(Indicator):
    """
    Find All Pivot Candles
    values: list[Candle]
    """

    def __init__(
        self,
        source: CandlesSource,
        left: int = 3,
        right: int = 3,
        down_pivot=True,
        support_conditions: SupportCandlesPattern = SupportCandlesPattern.RAW,
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

    def check_candle_is_pivot(
        self,
        candle_index: int,
        candles: list[Candle],
    ) -> bool:
        self.update(candles)
        if self.candles[candle_index] in self.data:
            return True
        return False

    def _forcast(self) -> MarketSide:
        return MarketSide.NEUTRAL

    def plot(self, plot: ChartPlot, all=False):
        if all:
            for candle in self.data:
                plot.mark_candle(candle, self.source)
        else:
            plot.mark_candle(self.data[-1], self.source)

    @property
    def major_pivot(self) -> Candle:
        if self._biggest_pivot:
            return self._biggest_pivot
        factor = -1 if self.down_pivot else 1
        self._biggest_pivot = self.data[0]
        for pivot in self.data[1:]:
            if (self.source(pivot) - self.source(self._biggest_pivot)) * factor > 0:
                self._biggest_pivot = pivot
        return self._biggest_pivot
