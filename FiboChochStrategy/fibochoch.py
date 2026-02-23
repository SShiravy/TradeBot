from ChartModule.models import (
    Chart,
    IndicatorBaseModel,
    Signal,
    ChartData,
    MarketSide,
    Candle,
    TickPrice,
)
from ChartModule.Indicators import (
    FibonacciRetracement,
    FiboLevels,
    SupportConditions,
)
from ChartModule.plot import ChartPlot
from TradingModule.trader_bot import TradeConfig
from TradingModule.models import Position, Strategy
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
        long_fibo_level: FiboLevels = FiboLevels.LEVEL_5,
        short_fibo_level: FiboLevels = FiboLevels.LEVEL_5,
        long_pivot_left=10,
        long_pivot_right=5,
        short_pivot_left=10,
        short_pivot_right=5,
    ) -> None:
        super().__init__(
            name,
            long_support_conditions,
            short_support_conditions,
            confirmation_indicators,
        )

        self.chart: Chart

        self.long_fibo_level = long_fibo_level
        self.short_fibo_level = short_fibo_level

        self.long_right = long_pivot_right
        self.long_left = long_pivot_left

        self.short_right = short_pivot_right
        self.short_left = short_pivot_left

        self.initilied: bool = False
        self.long_all_models: list[FiboChochModel] = []
        self.short_all_models: list[FiboChochModel] = []

        self.all_checked_candles: list[Candle] = []
        self.all_high_price: list[float] = []
        self.all_low_price: list[float] = []

    def long_find_start_pivot(self):
        low = self.all_low_price[-self.long_right]
        all_low = np.array(self.all_low_price[-(self.long_right + self.long_left) :])
        res = all_low - low
        if np.any(res < 0):
            return None
        pivot = self.all_checked_candles[-self.long_right]
        self.long_all_models.append(
            FiboChochModel(pivot, self.all_checked_candles.index(pivot))
        )

    def short_find_start_pivot(self):
        high = self.all_high_price[-self.short_right]
        all_high = np.array(
            self.all_high_price[-(self.short_right + self.short_left) :]
        )
        res = all_high - high
        if np.any(res > 0):
            return None
        pivot = self.all_checked_candles[-self.short_right]
        self.short_all_models.append(
            FiboChochModel(pivot, self.all_checked_candles.index(pivot))
        )

    def long_find_end_pivot(self, model: FiboChochModel):
        index = self.all_checked_candles.index(model.start_pivot_candle)
        high = max(self.all_high_price[index:])
        high_index = self.all_high_price.index(high)
        if high_index - index < self.long_right:
            return None
        top_pivot = self.all_checked_candles[high_index]
        return top_pivot

    def short_find_end_pivot(self, model: FiboChochModel):
        index = self.all_checked_candles.index(model.start_pivot_candle)
        low = min(self.all_low_price[index:])
        low_index = self.all_low_price.index(low)
        if low_index - index < self.short_right:
            return None
        down_pivot = self.all_checked_candles[low_index]
        return down_pivot

    def long_check_model(self, model: FiboChochModel):
        if not model.available:
            logger.error(f"long: not available {model=}")
            return None

        if (
            self.long_all_models[-1].start_pivot_candle.low
            < model.start_pivot_candle.low
        ):
            model.available = False
            logger.debug(f"long: new lower pivot, {model} is not available any more")
            return None

        top_pivot = self.long_find_end_pivot(model)
        if not top_pivot:
            return None
        top_index = self.all_checked_candles.index(top_pivot)

        if model.end_pivot_candle != top_pivot:
            model.end_pivot_candle = None

        if model.end_pivot_candle is None:
            support_condition = True  # TODO: (self.all_checked_candles[top_index].side is MarketSide.BULLISH and self.all_checked_candles[top_index+1].side is MarketSide.BEARISH) or (self.all_checked_candles[top_index].side is MarketSide.BEARISH and self.all_checked_candles[top_index+1].side is MarketSide.BULLISH)
            if not support_condition:
                return None
            for index, candle in enumerate(
                self.all_checked_candles[model.start_index - 1 :: -1]
            ):
                if candle.side is MarketSide.BULLISH:
                    buyers_high = max(
                        self.all_checked_candles[index + 1].high, candle.high
                    )
                    if buyers_high > top_pivot.high:
                        return None
                    break
            logger.debug(f"long: new end candle founded:{top_pivot}")
            model.end_pivot_candle = top_pivot
            model.fibo = FibonacciRetracement(
                TickPrice(model.start_pivot_candle.low, model.start_pivot_candle.time),
                TickPrice(model.end_pivot_candle.high, model.end_pivot_candle.time),
                fibonacci_levels=list(
                    {
                        FiboLevels.LEVEL_0,
                        FiboLevels.LEVEL_1,
                        FiboLevels.LEVEL_618,
                        FiboLevels.LEVEL_5,
                        self.long_fibo_level,
                    }
                ),
            )

        if model.fibo:
            fibo_res = model.fibo.forcast(
                self.all_low_price[top_index + 1 :], self.long_fibo_level
            )
            logger.debug(f"long: {fibo_res=}")
            if fibo_res == MarketSide.BULLISH:
                model.available = False
                for indicator in self.confirmation_indicators:
                    indicator.set(self.all_checked_candles)
                    res = indicator.forcast()
                    if res != MarketSide.BULLISH:
                        logger.debug(
                            f"long: indicator {indicator} not confirmed the signal"
                        )
                        return None
                return FiboChochSignal(
                    self.chart, self.all_checked_candles[-1], fibo_res, model
                )
        return None

    def short_check_model(self, model: FiboChochModel):
        if not model.available:
            logger.error(f"short: model not available {model=}")
            return None

        if (
            self.short_all_models[-1].start_pivot_candle.high
            > model.start_pivot_candle.high
        ):
            model.available = False
            logger.debug(f"short: new higher pivot, {model} is not available any more")
            return None

        down_pivot = self.short_find_end_pivot(model)
        if not down_pivot:
            return None
        down_index = self.all_checked_candles.index(down_pivot)

        if model.end_pivot_candle != down_pivot:
            model.end_pivot_candle = None

        if model.end_pivot_candle is None:
            support_condition = True  # TODO: Implement Here
            if not support_condition:
                return None
            for index, candle in enumerate(
                self.all_checked_candles[model.start_index - 1 :: -1]
            ):
                if candle.side is MarketSide.BEARISH:
                    sellers_low = min(
                        self.all_checked_candles[index + 1].low, candle.low
                    )
                    if sellers_low < down_pivot.low:
                        return None
                    break
            logger.debug(f"short: new end candle founded:{down_pivot}")
            model.end_pivot_candle = down_pivot
            model.fibo = FibonacciRetracement(
                TickPrice(model.start_pivot_candle.high, model.start_pivot_candle.time),
                TickPrice(model.end_pivot_candle.low, model.end_pivot_candle.time),
                fibonacci_levels=list(
                    {
                        FiboLevels.LEVEL_0,
                        FiboLevels.LEVEL_1,
                        FiboLevels.LEVEL_618,
                        FiboLevels.LEVEL_5,
                        self.short_fibo_level,
                    }
                ),
            )

        if model.fibo:
            fibo_res = model.fibo.forcast(
                self.all_high_price[down_index + 1 :], self.short_fibo_level
            )
            if fibo_res == MarketSide.BEARISH:
                model.available = False
                for indicator in self.confirmation_indicators:
                    indicator.set(self.all_checked_candles)
                    res = indicator.forcast()
                    if res != MarketSide.BEARISH:
                        logger.debug(
                            f"short: indicator {indicator} not confirmed the signal"
                        )
                        return None
                return FiboChochSignal(
                    self.chart, self.all_checked_candles[-1], fibo_res, model
                )
        return None

    def check_all_long_models(self):
        if not self.long_all_models:
            return None
        all_models = copy(self.long_all_models)
        res = None
        logger.debug(f"start checking {len(all_models)} Long FiboChoch Models")
        for model in all_models:
            if not model.available:
                self.long_all_models.remove(model)
                continue
            model_res = self.long_check_model(model)
            if model_res is None:
                continue
            res = copy(model_res)
        return res

    def check_all_short_models(self):
        if not self.short_all_models:
            return None
        all_models = copy(self.short_all_models)
        res = None
        logger.info(f"start checking {len(all_models)} Short FiboChoch Models")
        for model in all_models:
            if not model.available:
                self.short_all_models.remove(model)
                continue
            model_res = self.short_check_model(model)
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

            if index >= self.long_left + self.long_right:
                self.long_find_start_pivot()
                self.check_all_long_models()

            if index >= self.short_left + self.short_right:
                self.short_find_start_pivot()
                self.check_all_short_models()

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
        long_signal = None
        short_signal = None
        if check_long:
            self.long_find_start_pivot()
            long_signal = self.check_all_long_models()
        if check_short:
            self.short_find_start_pivot()
            short_signal = self.check_all_short_models()

        if long_signal and short_signal:
            return None
        if long_signal:
            return long_signal
        if short_signal:
            return short_signal
        return None

    def report(self, *args, **kwargs) -> str:
        return ""

    def draw(
        self,
        plot: ChartPlot,
        signal: FiboChochSignal,
        draw_indicators: bool = True,
        *args,
        **kwargs,
    ):
        super().draw(plot, signal, draw_indicators)
        signal.fibochoch_model.fibo.plot(plot, end_time=signal.candle.time)  # type:ignore
        plot.mark_signal(signal)


class FiboChochConfig(TradeConfig):
    strategy: FiboChoch  # type: ignore[override]
    modify_positions_sl: bool = field(default=True)

    async def find_signal(
        self, chartdata: ChartData
    ) -> None | tuple[FiboChochSignal, Position]:
        signal = self.strategy.check_signal(
            chartdata, self.long_signal, self.short_signal
        )
        if signal is None or signal.fibochoch_model.fibo is None:
            return None

        plot = None
        if self.send_signal:
            plot = ChartPlot(chartdata)
            self.strategy.draw(plot, signal, draw_indicators=True)
        position = await self.position_handler.generate_position(
            signal,
            sl_base_price=signal.fibochoch_model.fibo.start_tick.price,
            plot=plot,
        )
        return signal, position
