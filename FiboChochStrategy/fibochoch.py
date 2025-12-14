from ChartModule.models import (
    Chart,
    IndicatorBaseModel,
    Signal,
    ChartData,
    MarketSide,
    IndicatorCandleSource,
    Candle,
    TickPrice,
)
from ChartModule.Indicators import (
    FibonacciRetracement,
    FiboLevels,
    SupportConditions,
)
from ChartModule.plot import PlotChart
from TradingModule.trader_bot import TradeConfig, commands
from TradingModule.models import OrderSide, Position, Strategy
from dataclasses import dataclass, field
from copy import copy
import numpy as np
import logging

logger = logging.getLogger("FiboCHoCH")


@dataclass(slots=True)
class FiboChochModel:
    start_pivot_candle: Candle
    start_index: int
    end_pivot_candle: Candle | None = field(default=None)

    fibo: FibonacciRetracement | None = field(default=None, init=False)
    available: bool = field(default=True, init=False)

    def __str__(self) -> str:
        return f"{self.start_pivot_candle}|{self.end_pivot_candle}|{self.available}"


@dataclass(slots=True, frozen=True)
class FiboChochSignal(Signal):
    source: str = field(default="FiboChoch", init=False)
    fibochoch_model: FiboChochModel


class FiboChoch(Strategy):
    def __init__(
        self,
        name="FiboChoch",
        long_support_conditions: SupportConditions = SupportConditions.GREEN_RED,
        short_support_conditions: SupportConditions = SupportConditions.RED_GREEN,
        confirmation_indicators: list[IndicatorBaseModel] = [],
        fibo_level: FiboLevels = FiboLevels.LEVEL_5,
        pivot_left=10,
        pivot_right=5,
    ) -> None:
        super().__init__(
            name,
            long_support_conditions,
            short_support_conditions,
            confirmation_indicators,
        )

        self.chart: Chart

        self.fibo_level = fibo_level

        self.right = pivot_right
        self.left = pivot_left

        self.initilied: bool = False
        self.all_models: list[FiboChochModel] = []

        self.all_checked_candles: list[Candle] = []
        self.all_high_price: list[float] = []
        self.all_low_price: list[float] = []
        self.test_all_down = []
        self.test_all_top = []

    def find_new_down_pivot(self):
        low = self.all_low_price[-self.right]
        all_low = np.array(self.all_low_price[-(self.right + self.left) :])
        res = all_low - low
        if np.any(res < 0):
            return None
        pivot = self.all_checked_candles[-self.right]
        self.all_models.append(
            FiboChochModel(pivot, self.all_checked_candles.index(pivot))
        )
        self.test_all_down.append(pivot)

    def find_new_top_pivot(self, model: FiboChochModel):
        index = self.all_checked_candles.index(model.start_pivot_candle)
        high = max(self.all_high_price[index:-1])
        high_index = self.all_high_price.index(high)
        if high_index - index < self.right:
            return None
        top_pivot = self.all_checked_candles[high_index]
        self.test_all_top.append(top_pivot)
        return top_pivot

    def check_model(self, model: FiboChochModel):
        if not model.available:
            logger.error(f"try to not available {model=}")
            return None

        if self.all_models[-1].start_pivot_candle.low < model.start_pivot_candle.low:
            model.available = False
            logger.debug(f"new lower pivot, {model} is not available any more")
            return None

        top_pivot = self.find_new_top_pivot(model)
        if not top_pivot:
            return None
        top_index = self.all_checked_candles.index(top_pivot)

        if model.end_pivot_candle != top_pivot:
            model.end_pivot_candle = None

        if model.end_pivot_candle is None:
            support_condition = True  # (self.all_checked_candles[top_index].side is MarketSide.BULLISH and self.all_checked_candles[top_index+1].side is MarketSide.BEARISH) or (self.all_checked_candles[top_index].side is MarketSide.BEARISH and self.all_checked_candles[top_index+1].side is MarketSide.BULLISH)
            if not support_condition:
                return None
            for candle in self.all_checked_candles[model.start_index - 1 :: -1]:
                if candle.side is MarketSide.BULLISH:
                    if candle.high > top_pivot.high:
                        return None
                    break
            logger.debug(f"new end candle founded:{top_pivot}")
            model.end_pivot_candle = top_pivot
            model.fibo = FibonacciRetracement(
                TickPrice(model.start_pivot_candle.low, model.start_pivot_candle.time),
                TickPrice(model.end_pivot_candle.high, model.end_pivot_candle.time),
                fibonacci_levels=[
                    FiboLevels.LEVEL_0,
                    FiboLevels.LEVEL_1,
                    FiboLevels.LEVEL_618,
                    FiboLevels.LEVEL_5,
                ],
            )

        if model.fibo:
            fibo_res = model.fibo.forcast(
                self.all_low_price[top_index + 1 :], self.fibo_level
            )
            logger.debug(f"{fibo_res=}")
            if fibo_res != MarketSide.NEUTRAL:
                model.available = False
                for indicator in self.confirmation_indicators:
                    indicator.set(self.all_checked_candles)
                    res = indicator.forcast()
                    if res != MarketSide.BULLISH:
                        logger.debug(f"indicator {indicator} not confirmed the signal")
                        return None
                return FiboChochSignal(
                    self.chart, self.all_checked_candles[-1], fibo_res, model
                )
        return None

    def check_all_models(self):
        if not self.all_models:
            return None
        all_models = copy(self.all_models)
        res = None
        logger.debug(f"start checking {len(all_models)} FiboChoch Models")
        for model in all_models:
            if not model.available:
                self.all_models.remove(model)
                continue
            model_res = self.check_model(model)
            if model_res is None:
                continue
            res = copy(model_res)
        return res

    def init_fibochochs(self, chartdata: ChartData):
        self.chart = chartdata.chart
        for index, candle in enumerate(chartdata.candles):
            self.all_high_price.append(candle.high)
            self.all_low_price.append(candle.low)
            self.all_checked_candles.append(candle)

            if index < self.left + self.right:
                continue
            self.find_new_down_pivot()
            self.check_all_models()

        self.initilied = True

    def check_signal(
        self,
        chartdata: ChartData,
        check_long: bool = True,
        check_short: bool = True,
        *args,
        **kwargs,
    ) -> FiboChochSignal | None:
        if not self.initilied:
            logger.info("start initilizing FiboChochs")
            self.init_fibochochs(chartdata)
        last_checked_candle = self.all_checked_candles[-1]
        if last_checked_candle.time == chartdata[-1].time:
            self.all_checked_candles[-1] = chartdata[-1]
            self.all_low_price[-1] = chartdata[-1].low
            self.all_high_price[-1] = chartdata[-1].high
        else:
            if last_checked_candle in chartdata.candles:
                last_candle_index = chartdata.candles.index(last_checked_candle)
            else:
                last_candle_index = 0
            for candle in chartdata.candles[last_candle_index + 1 :]:
                self.all_checked_candles.append(candle)
                self.all_low_price.append(candle.low)
                self.all_high_price.append(candle.high)

        self.find_new_down_pivot()
        return self.check_all_models()

    def report(self, *args, **kwargs) -> str:
        return ""

    def draw(
        self,
        plot: PlotChart,
        signal: FiboChochSignal,
        draw_indicators: bool = True,
        *args,
        **kwargs,
    ):
        super().draw(plot, signal, draw_indicators)
        for model in self.all_models:
            if model.fibo:
                model.fibo.plot(plot)
            else:
                plot.mark_candle(model.start_pivot_candle, IndicatorCandleSource.Bottom)
        if draw_indicators:
            for indicator in self.confirmation_indicators:
                indicator.plot(plot)
        signal.fibochoch_model.fibo.plot(plot, end_time=signal.candle.time)  # type:ignore
        plot.mark_signal(signal)


class FiboChochConfig(TradeConfig):
    strategy: FiboChoch  # type: ignore[override]
    fibo_stoploss: bool = field(default=True)

    def find_signal(self, chartdata: ChartData) -> None | tuple[Signal, Position]:
        signal = self.strategy.check_signal(
            chartdata, self.long_signal, self.short_signal
        )
        if signal is None or signal.fibochoch_model.fibo is None:
            return None

        position = self.position_handler.generate_position(signal)
        if self.fibo_stoploss:
            sl = self.position_handler.init_stoploss(
                signal.fibochoch_model.fibo.start_tick.price, position.side
            )
            position.stoploss = sl

        if (self.position_handler.long_trade and position.side is OrderSide.BUY) or (
            self.position_handler.short_trade and position.side is OrderSide.SELL
        ):
            commands.OpenPosition(position, self.agent)
        return signal, position
