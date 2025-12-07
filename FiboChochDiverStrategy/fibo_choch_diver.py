from FiboChochStrategy.fibochoch import FiboChochSignal
from TradingModule import Position, OrderSide, commands
from TradingModule.trader_bot import TradeConfig
from TradingModule.reporter import TelegramReporter
from ChartModule.models import Chart, Candle, Signal, ChartData
from TradingModule.models import Strategy
from ChartModule.plot import PlotChart
from FiboChochStrategy import FiboChoch
from DivergenceStrategy import Divergence, DivergenceSignal
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from copy import deepcopy
import logging


logger = logging.getLogger("FiChDiverStrategy")


@dataclass
class FiboChochDiver(TradeConfig):
    diver_base_chart: Chart  # type: ignore
    diver_second_chart: Chart  # type: ignore

    fibochoch_strategy: FiboChoch  # type: ignore
    diver_strategy: Divergence  # type: ignore

    diver_heikingashi_chartdata: bool = field(default=False)
    fibo_stoploss: bool = field(default=True)

    strategy: Strategy | None = field(default=None, init=False)  # type: ignore[override]

    _init_called: bool = field(default=False, init=False)
    _diver_last_signal: DivergenceSignal | None = field(default=None, init=False)
    _diver_next_check: datetime = field(
        default=datetime.now(tz=timezone.utc), init=False
    )

    def give_delay(self, last_candle: Candle, jump=False) -> timedelta:
        delay = self.chart.timeframe.time_delta
        if jump:
            delay *= self.bar_between_signals

        logging.debug(f"delay + lastcandl.time: {delay + last_candle.time}")

        return (
            (delay + last_candle.time)
            - datetime.now(timezone.utc)
            + timedelta(seconds=1)
        )

    def set_diver_next_check(self, last_candle: Candle):
        delay = self.diver_base_chart.timeframe.time_delta
        self._diver_next_check = delay + last_candle.time + timedelta(seconds=1)

    def get_diver_chartdata(self):
        base_chartdata = self.agent.get_chartdata(
            self.diver_base_chart, self.n_candle_check
        )
        second_chartdata = self.agent.get_chartdata(
            self.diver_second_chart, self.n_candle_check
        )
        if base_chartdata is None or second_chartdata is None:
            raise ValueError(f"chart data is None from {self.agent.__class__.__name__}")
        if self.heikingashi_chartdata:
            base_chartdata = base_chartdata.give_heikingashi_chartdata()
            second_chartdata = second_chartdata.give_heikingashi_chartdata()
        return base_chartdata, second_chartdata

    def diver_find_signal(
        self, chartdata: ChartData, second_chartdata: ChartData
    ) -> DivergenceSignal | None:
        signal = self.diver_strategy.check_signal(
            chartdata, second_chartdata, self.long_signal, self.short_signal
        )
        return signal

    def diver_init(self):
        base_chartdata, second_chartdata = self.get_diver_chartdata()
        self.set_diver_next_check(base_chartdata[-2])

        base_data = deepcopy(base_chartdata)
        second_data = deepcopy(second_chartdata)
        for i in range(1, len(base_chartdata) - self.diver_strategy.min_step - 1):
            base_data.candles = base_chartdata[:-i]
            second_data.candles = second_chartdata[:-i]
            signal = self.diver_find_signal(base_data, second_data)
            if signal:
                self._diver_last_signal = signal
                return

    def fibochoch_init(self):
        self.fibochoch_strategy.init_fibochochs(self.get_chartdata())

    def find_signal(
        self,
        chartdata: ChartData,
    ) -> None | tuple[FiboChochSignal, Position]:
        if self._diver_last_signal is None:
            return None

        signal = self.fibochoch_strategy.check_signal(
            chartdata, self.long_signal, self.short_signal
        )
        if signal is None or signal.fibochoch_model.fibo is None:
            return None

        if signal.side != self._diver_last_signal.side:
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

    async def task(self) -> timedelta | tuple[timedelta, Signal, Position]:
        if self._init_called is False:
            self.fibochoch_init()
            self.diver_init()
            self._init_called = True

        chartdata = self.get_chartdata()

        if chartdata[-1].time > self._diver_next_check:
            base_chartdata, second_chartdata = self.get_diver_chartdata()
            signal = self.diver_find_signal(base_chartdata, second_chartdata)
            if signal:
                self._diver_last_signal = signal
            self.set_diver_next_check(base_chartdata[-1])

        res = self.find_signal(chartdata)
        if res is None:
            return self.give_delay(chartdata[-1])
        signal, position = res
        if self.send_signal:
            plot = PlotChart(chartdata)
            self.fibochoch_strategy.draw(plot, signal, draw_indicators=True)
            await TelegramReporter().new_position(position, plot)
        return self.give_delay(chartdata[-1], jump=True), signal, position

    def __str__(self) -> str:
        msg_list = [
            str(self.chart),
            str(self.diver_base_chart),
            str(self.diver_second_chart),
            self.agent.__class__.__name__,
            self.fibochoch_strategy.name,
            self.diver_strategy.name,
            self.position_handler.__class__.__name__,
        ]
        return "|".join(msg_list)
