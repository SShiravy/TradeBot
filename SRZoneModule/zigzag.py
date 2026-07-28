from ChartModule.models import Candle, MarketSide, CandlesSource
from ChartModule.Indicators.models import IndicatorBaseModel
from ChartModule.plot import ChartPlot
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class PivotPoint:

    index: int
    candle: Candle
    price: float
    is_high: bool
    confirmed_index: int

    def __str__(self) -> str:
        side = "High" if self.is_high else "Low"
        return f"ZigZag{side}|{self.candle.time}|{self.price}"


class ZigZagPivot(IndicatorBaseModel):
    """
    ZigZag Pivot Detector (Depth / Deviation / Backstep)

    values: list[PivotPoint]
    """

    def __init__(
        self,
        depth: int = 12,
        deviation: int = 5,
        backstep: int = 2,
    ) -> None:
        super().__init__()
        self.data: list[PivotPoint]
        self.depth = depth
        self.deviation = deviation
        self.backstep = backstep

    def export_configs(self) -> dict:
        configs = super().export_configs()
        configs.update(
            {
                "depth": self.depth,
                "deviation": self.deviation,
                "backstep": self.backstep,
            }
        )
        return configs

    def _deviation_price(self, precision: int) -> float:
        return self.deviation * (10**-precision)

    def _calculate(self, precision: int = 3) -> list[PivotPoint]:
        candles = self.candles
        pivots: list[PivotPoint] = []

        if len(candles) < self.depth + 2:
            return pivots

        deviation_price = self._deviation_price(precision)

        direction = 0  # 0 = undefined, 1 = up leg, -1 = down leg
        high_idx = 0
        high_price = candles[0].high
        low_idx = 0
        low_price = candles[0].low
        last_pivot_idx = 0

        for i in range(1, len(candles)):
            candle = candles[i]

            if direction <= 0:
                if candle.low < low_price:
                    low_price = candle.low
                    low_idx = i
                if (
                    candle.high - low_price >= deviation_price
                    and i - low_idx >= self.backstep
                    and low_idx - last_pivot_idx >= self.depth
                ):
                    pivots.append(
                        PivotPoint(low_idx, candles[low_idx], low_price, False, i)
                    )
                    direction = 1
                    last_pivot_idx = low_idx
                    high_price = candle.high
                    high_idx = i

            if direction >= 0:
                if candle.high > high_price:
                    high_price = candle.high
                    high_idx = i
                if (
                    high_price - candle.low >= deviation_price
                    and i - high_idx >= self.backstep
                    and high_idx - last_pivot_idx >= self.depth
                ):
                    pivots.append(
                        PivotPoint(high_idx, candles[high_idx], high_price, True, i)
                    )
                    direction = -1
                    last_pivot_idx = high_idx
                    low_price = candle.low
                    low_idx = i

        return pivots

    def _forcast(self) -> MarketSide:
        return MarketSide.NEUTRAL

    def plot(self, plot: ChartPlot, all: bool = True):
        pivots = self.data if all else self.data[-1:]
        for pivot in pivots:
            plot.mark_candle(
                pivot.candle,
                CandlesSource.High if pivot.is_high else CandlesSource.Low,
            )

    def update(self, candles: list[Candle], *args, **kwargs):
        pass
