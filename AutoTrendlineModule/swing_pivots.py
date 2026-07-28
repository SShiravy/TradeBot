from ChartModule.models import Candle, MarketSide, CandlesSource
from ChartModule.Indicators.models import IndicatorBaseModel
from ChartModule.plot import ChartPlot
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class PivotPoint:
    """
    A single swing pivot (confirmed or live/tentative).

    index: bar index of the pivot itself (the extreme candle)
    confirmed_index: bar index at which the pivot got confirmed
                      (i.e. once `depth` candles passed without a new,
                      more extreme value). For a live/unconfirmed pivot
                      this is simply the most recent processed bar index.
    confirmed: False for the currently-running, not-yet-locked-in extreme
               (mirrors the repainting z2 point of the original ZigZag).
    """

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
    """
    Causal, repainting swing pivot detector (Depth / Backstep).

    Mirrors the behaviour of the MT4-style ZigZag: the running high/low is
    tracked bar by bar (this is the *live*, repainting point, exposed via
    `live_pivots`) and only *confirmed* once `depth` bars pass without a
    new, more extreme value replacing it. Highs and lows strictly
    alternate, exactly like a real ZigZag. `backstep` then drops the
    weaker of two same-type confirmed pivots that ended up closer than
    `backstep` bars apart.

    values: list[PivotPoint]           (confirmed pivots only)
    live_pivots: list[PivotPoint]      (0-2 currently running, unconfirmed)
    """

    def __init__(self, depth: int = 12, backstep: int = 2) -> None:
        super().__init__()
        self.data: list[PivotPoint]
        self.live_pivots: list[PivotPoint] = []
        self.depth = depth
        self.backstep = backstep

    def export_configs(self) -> dict:
        configs = super().export_configs()
        configs.update({"depth": self.depth, "backstep": self.backstep})
        return configs

    def _apply_backstep(self, pivots: list[PivotPoint], is_high: bool) -> list[PivotPoint]:
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

    def _calculate(self) -> list[PivotPoint]:
        candles = self.candles
        self.live_pivots = []

        if len(candles) < 2:
            return []

        pivots: list[PivotPoint] = []

        direction = 0  # 0 = tracking both (not decided yet), 1 = tracking a high, -1 = a low
        high_idx = high_last_update = 0
        high_price = candles[0].high
        low_idx = low_last_update = 0
        low_price = candles[0].low

        for i in range(1, len(candles)):
            candle = candles[i]

            if direction <= 0:
                if candle.low < low_price:
                    low_price = candle.low
                    low_idx = i
                    low_last_update = i
                if i - low_last_update >= self.depth:
                    pivots.append(
                        PivotPoint(low_idx, candles[low_idx], low_price, False, i, True)
                    )
                    direction = 1
                    high_price = candle.high
                    high_idx = i
                    high_last_update = i

            if direction >= 0:
                if candle.high > high_price:
                    high_price = candle.high
                    high_idx = i
                    high_last_update = i
                if i - high_last_update >= self.depth:
                    pivots.append(
                        PivotPoint(high_idx, candles[high_idx], high_price, True, i, True)
                    )
                    direction = -1
                    low_price = candle.low
                    low_idx = i
                    low_last_update = i

        highs = self._apply_backstep([p for p in pivots if p.is_high], True)
        lows = self._apply_backstep([p for p in pivots if not p.is_high], False)
        confirmed = sorted(highs + lows, key=lambda pivot: pivot.confirmed_index)

        last_index = len(candles) - 1
        if direction <= 0:
            self.live_pivots.append(
                PivotPoint(low_idx, candles[low_idx], low_price, False, last_index, False)
            )
        if direction >= 0:
            self.live_pivots.append(
                PivotPoint(high_idx, candles[high_idx], high_price, True, last_index, False)
            )

        return confirmed

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

    def update(self, candles: list[Candle], *args, **kwargs):
        pass
