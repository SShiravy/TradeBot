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
    confirmed: bool = True

    def __str__(self) -> str:
        side = "High" if self.is_high else "Low"
        tag = "" if self.confirmed else "*"
        return f"Pivot{side}{tag}|{self.candle.time}|{self.price}"


class SwingPivots(IndicatorBaseModel):
    def __init__(self, depth: int = 12, backstep: int = 2) -> None:
        super().__init__()
        self.data: list[PivotPoint] = []
        self.live_pivots: list[PivotPoint] = []
        self.depth = depth
        self.backstep = backstep

        # running state, so `update()` can resume exactly where
        # `_calculate()`/the previous `update()` left off
        self._raw_pivots: list[PivotPoint] = []
        self._direction = 0  # 0 = tracking both, 1 = tracking a high, -1 = a low
        self._high_idx = 0
        self._high_last_update = 0
        self._high_price = 0.0
        self._low_idx = 0
        self._low_last_update = 0
        self._low_price = 0.0

    def export_configs(self) -> dict:
        configs = super().export_configs()
        configs.update({"depth": self.depth, "backstep": self.backstep})
        return configs

    def _apply_backstep(
        self, pivots: list[PivotPoint], is_high: bool
    ) -> list[PivotPoint]:
        """
        Drop the weaker of two same-type pivots that are closer than
        `backstep` bars apart, keeping only the stronger extreme.
        """
        if self.backstep <= 0 or not pivots:
            return pivots

        factor = 1 if is_high else -1
        result: list[PivotPoint] = []
        for pivot in pivots:
            if result and pivot.index - result[-1].index < self.backstep:
                if (pivot.price - result[-1].price) * factor > 0:
                    result[-1] = pivot
                # else: new pivot is weaker -> discard it
            else:
                result.append(pivot)
        return result

    def _scan(self, start: int, end: int):
        candles = self.candles
        for i in range(start, end):
            candle = candles[i]

            if self._direction <= 0:
                if candle.low < self._low_price:
                    self._low_price = candle.low
                    self._low_idx = i
                    self._low_last_update = i
                if i - self._low_last_update >= self.depth:
                    self._raw_pivots.append(
                        PivotPoint(
                            self._low_idx,
                            candles[self._low_idx],
                            self._low_price,
                            False,
                            i,
                            True,
                        )
                    )
                    self._direction = 1
                    self._high_price = candle.high
                    self._high_idx = i
                    self._high_last_update = i

            if self._direction >= 0:
                if candle.high > self._high_price:
                    self._high_price = candle.high
                    self._high_idx = i
                    self._high_last_update = i
                if i - self._high_last_update >= self.depth:
                    self._raw_pivots.append(
                        PivotPoint(
                            self._high_idx,
                            candles[self._high_idx],
                            self._high_price,
                            True,
                            i,
                            True,
                        )
                    )
                    self._direction = -1
                    self._low_price = candle.low
                    self._low_idx = i
                    self._low_last_update = i

    def _finalize(self) -> list[PivotPoint]:
        highs = self._apply_backstep([p for p in self._raw_pivots if p.is_high], True)
        lows = self._apply_backstep(
            [p for p in self._raw_pivots if not p.is_high], False
        )
        confirmed = sorted(highs + lows, key=lambda pivot: pivot.confirmed_index)

        candles = self.candles
        last_index = len(candles) - 1
        self.live_pivots = []
        if self._direction <= 0:
            self.live_pivots.append(
                PivotPoint(
                    self._low_idx,
                    candles[self._low_idx],
                    self._low_price,
                    False,
                    last_index,
                    False,
                )
            )
        if self._direction >= 0:
            self.live_pivots.append(
                PivotPoint(
                    self._high_idx,
                    candles[self._high_idx],
                    self._high_price,
                    True,
                    last_index,
                    False,
                )
            )
        return confirmed

    def _calculate(self) -> list[PivotPoint]:
        candles = self.candles
        self.live_pivots = []
        self._raw_pivots = []

        if len(candles) < 2:
            return []

        self._direction = 0
        self._high_idx = self._high_last_update = 0
        self._high_price = candles[0].high
        self._low_idx = self._low_last_update = 0
        self._low_price = candles[0].low

        self._scan(1, len(candles))
        return self._finalize()

    def update(self, candles: list[Candle], *args, **kwargs) -> list[PivotPoint]:
        if self.last_checked_candle is None:
            raise ValueError("last_checked_candle is None")

        start_index = self.find_new_candle_index(candles)
        if start_index >= len(candles):
            return self.data

        self.candles = candles
        self._scan(max(start_index, 1), len(candles))
        self.data = self._finalize()
        self.last_checked_candle = candles[-1]
        return self.data

    def _forcast(self) -> MarketSide:
        return MarketSide.NEUTRAL

    def plot(self, plot: ChartPlot, show_live: bool = True):
        for pivot in self.data:
            plot.mark_candle(
                pivot.candle,
                CandlesSource.High if pivot.is_high else CandlesSource.Low,
            )
        if show_live:
            for pivot in self.live_pivots:
                plot.mark_candle(
                    pivot.candle,
                    CandlesSource.High if pivot.is_high else CandlesSource.Low,
                )
