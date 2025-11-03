from ChartModule.models import IndicatorBaseModel, MarketSide, Candle
from ChartModule.Indicators.models import IndicatorCandleSource
import numpy as np


class Pivot(IndicatorBaseModel):
    """
    Find All Pivot Candles
    values: list[Candle]
    """

    def __init__(
        self, source: IndicatorCandleSource, right: int = 3, left: int = 3
    ) -> None:
        self.source = source
        self.right = right
        self.left = left

    def check_candle_is_pivot(
        self,
        candle: Candle,
    ) -> bool:
        if not self.values:
            return False
        if candle in self.values:
            return True
        else:
            return False

    def _calculate(self) -> list[Candle]:
        all_source = []
        all_pivots = []
        n_candle_jump = 0
        for index in range(0, len(self.candles)):
            all_source.append(self.source(self.candles[index]))
            if index < self.left + self.right:
                continue
            if n_candle_jump > 0:
                n_candle_jump -= 1
                continue
            candle_index = index - self.right
            candle_source = all_source[candle_index]
            res = np.array(all_source[candle_index - self.left : index]) - candle_source
            if np.all(res <= 0):
                all_pivots.append(self.candles[candle_index])
                n_candle_jump += self.left
        return all_pivots

    def _forcast(self) -> MarketSide:
        return MarketSide.NEUTRAL
