from ChartModule.models import MarketSide
from ChartModule.Indicators.models import Indicator
import finplot as fplt


class MovingColor(Indicator):
    """
    Sum on number of (Red - Green), 0 is the same number of red green on previous n bar
    """

    def __init__(self, n_bar: int) -> None:
        super().__init__()
        self.n_bar = n_bar

    def _calculate(self) -> dict:
        if len(self.candles) < self.n_bar:
            return {}
        values = {}
        self.length_values = {}
        color_number = []  # -1 for red and 1 for green
        for i, candle in enumerate(self.candles):
            color_number.append(candle.side.number)
            if i < self.n_bar - 1:
                continue
            values[candle.time] = sum(color_number)
            color_number.pop(0)

        return values

    def _forcast(self) -> MarketSide:
        last_value = self.data[-1]
        if last_value > 0:
            return MarketSide.BULLISH
        if last_value > 0:
            return MarketSide.BEARISH
        return MarketSide.NEUTRAL

    def plot(self, plot=None):
        times = list(self.data.keys())
        values = list(self.data.values())
        fplt.plot(times, values, style="-", ax=plot, color="#F8C600")
        fplt.add_line(
            (times[0], 0),
            (times[-1], 0),
            color="#696969",
            width=1,
            interactive=False,
            ax=plot,
        )


class MovingCandleLength(Indicator):
    """
    Sum on number of (Red - Green), 0 is the same number of red green on previous n bar
    """

    def __init__(self, n_bar: int) -> None:
        super().__init__()
        self.n_bar = n_bar

    def _calculate(self) -> dict:
        if len(self.candles) < self.n_bar:
            return {}
        values = {}
        self.length_values = {}
        length_number = []  # - for red and + for green
        for i, candle in enumerate(self.candles):
            length_number.append(candle.side.number * candle.body_length)
            if i < self.n_bar - 1:
                continue
            values[candle.time] = sum(length_number)
            length_number.pop(0)

        return values

    def _forcast(self) -> MarketSide:
        last_value = self.data[-1]
        if last_value > 0:
            return MarketSide.BULLISH
        if last_value > 0:
            return MarketSide.BEARISH
        return MarketSide.NEUTRAL

    def plot(self, plot=None):
        times = list(self.data.keys())
        values = list(self.data.values())
        fplt.plot(times, values, style="-", ax=plot, color="#E63D00")
        fplt.add_line(
            (times[0], 0),
            (times[-1], 0),
            color="#696969",
            width=1,
            interactive=False,
            ax=plot,
        )
