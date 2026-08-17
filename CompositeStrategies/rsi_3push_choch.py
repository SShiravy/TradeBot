from datetime import timedelta
from ChochQueueStrategy.choch_queue import ChochQueueFilter, ChochSignal
from Forex.agent import ForexAgent
from custom_logger import CustomLogger
from ChartModule.models import (
    Candle,
    Chart,
    ChartData,
)
from ChartModule.plot import ChartPlot, ChartWithOscillatorPlot
from DivergenceStrategy.oscillator_divergence import (
    OscillatorDivergence,
)
from DivergenceStrategy.oscillator_double_divergence import OscillatorDoubleDiverSignal
from TradingModule.reporter import TelegramReporter
from TradingModule.trader_bot import TradeConfig, Position
from dataclasses import dataclass, field
from copy import copy
import logging


logger = CustomLogger(
    log_file=True, file_log_name="RSI_3Push_Choch", consol_log_level=logging.DEBUG
)


@dataclass(kw_only=True)
class Rsi3PushChochConfig(TradeConfig):
    strategy: OscillatorDivergence  # type: ignore[override]
    choch_strategy: ChochQueueFilter  # type: ignore[override]
    rsi_chart: Chart
    same_line_source: bool = True
    n_candle_confirmation: int = 100
    last_3push_signal: OscillatorDoubleDiverSignal | None = field(
        default=None, init=False
    )
    last_3push_signal_msg_id: int | None = field(default=None, init=False)
    last_3push_checked_candle: Candle | None = field(default=None, init=False)

    async def _check_rsi(self, chartdata: ChartData):
        if (
            self.last_3push_checked_candle
            and self.last_3push_checked_candle == chartdata.candles[-1]
        ):
            return None
        self.last_3push_checked_candle = chartdata.candles[-1]
        first_signal = self.strategy.check_signal(
            chartdata, self.long_signal, self.short_signal
        )
        if first_signal is None:
            return None
        left_index = chartdata.candles.index(first_signal.main_chart_line.start_candle)
        second_sub_chart = copy(chartdata)
        second_sub_chart.candles = chartdata.candles[: left_index + 2]
        second_signal = self.strategy.check_signal(
            second_sub_chart, self.long_signal, self.short_signal, shift_candle=True
        )
        if second_signal is None or second_signal.side != first_signal.side:
            return None
        if (
            self.same_line_source
            and first_signal.main_chart_line.source
            != second_signal.main_chart_line.source
        ):
            return None
        double_diver_signal = OscillatorDoubleDiverSignal.generate_signal(
            first_signal, second_signal
        )
        logger.info(f"OscillatorDiver Signal:{double_diver_signal}")
        if self.send_signal:
            self.strategy.oscillator_indicator.set(candles=chartdata.candles)
            plot = ChartWithOscillatorPlot(
                chartdata,
                self.strategy.oscillator_indicator.data,
                plot_n_candles=self.n_candle_check,
            )
            self.strategy.draw(plot, first_signal, draw_indicators=True)
            self.strategy.draw(
                plot, second_signal, draw_indicators=False, mark_signal=False
            )
            self.strategy.oscillator_indicator.plot(plot, plot.oscillator_ax)
            self.last_3push_signal = double_diver_signal
            self.last_3push_signal_msg_id = await TelegramReporter().new_signal(
                double_diver_signal, plot
            )

    def _check_choch(self, chartdata: ChartData):
        signal = self.choch_strategy.check_signal(
            chartdata, self.long_signal, self.short_signal
        )
        if signal is None or not signal.choch_model.is_choch:
            return None
        return signal

    async def find_signal(
        self, chartdata: ChartData, choch_chartdata: ChartData
    ) -> None | ChochSignal | tuple[ChochSignal, Position]:
        # Check for 3-push signal
        await self._check_rsi(chartdata)
        if self.last_3push_signal is None:
            return None

        # Check if the last 3-push signal is too old
        elapsed_time = (
            chartdata.candles[-1].time
            - self.last_3push_signal.main_chart_line.end_candle.time
        ).total_seconds()
        time_condition = (
            self.n_candle_confirmation
            * chartdata.chart.timeframe.time_delta.total_seconds()
        )
        if elapsed_time > time_condition:
            self.last_3push_signal = None
            self.last_3push_signal_msg_id = None
            logging.warning(f"rsi3push was too old {elapsed_time=} > {time_condition}")
            return None

        # Check for CHoCH signal
        choch_signal = self._check_choch(choch_chartdata)
        if choch_signal is None:
            return None

        # Check if the CHoCH signal is in the same direction as the last 3-push signal
        if choch_signal.side != self.last_3push_signal.side:
            logging.warning(
                f"different side for rsi3push & choch: {self.last_3push_signal.side} | {choch_signal.side}"
            )
            return None

        # Generate position based on the combined signals
        plot = None
        if self.send_signal:
            plot = ChartPlot(choch_chartdata)
            self.choch_strategy.draw(plot, choch_signal, draw_indicators=True)
        if not self.consider_position:
            if self.send_signal:
                await TelegramReporter().new_signal(
                    choch_signal, plot, self.last_3push_signal_msg_id
                )
            return choch_signal

        position = await self.position_handler.generate_position(
            choch_signal, sl_base_price=choch_signal.choch_model.anchor, plot=plot
        )
        if not position:
            logger.warning("Position is None")
            return None
        logger.info("RSI 3push & CHoCH Signal")
        position.reply_msg_id = self.last_3push_signal_msg_id
        self.last_3push_signal = None
        self.last_3push_signal_msg_id = None
        return choch_signal, position

    def get_chartdata(
        self,
        chart: Chart,
        n_bar: int | None = None,
    ) -> ChartData:
        chartdata = self.agent.get_chartdata(
            chart, n_bars=n_bar if n_bar else self.n_candle_check
        )
        if chartdata is None:
            raise ValueError(f"chart data is None from {self.agent.__class__.__name__}")
        if self.heikingashi_chartdata:
            chartdata = chartdata.give_heikingashi_chartdata()
        return chartdata

    def give_delay(self, last_candle: Candle, jump=False) -> timedelta:
        delay = self.chart.timeframe.time_delta
        if jump:
            delay *= self.bar_between_signals
        last_candle_time = (
            ForexAgent().get_chartdata(self.chart, n_bars=1).candles[0]  # type: ignore
        )
        next_timestamp = int(round(last_candle_time.timestamp) + delay.total_seconds())
        sleep_time_based_on_timestamp = (
            next_timestamp - ForexAgent().give_current_timestamp(self.chart)
        )

        return timedelta(seconds=sleep_time_based_on_timestamp + 1)

    async def task(self):
        # RSI 3-push chart data
        rsi_chartdata = self.get_chartdata(self.rsi_chart)
        rsi_sub_chartdata = copy(rsi_chartdata)
        rsi_sub_chartdata.candles = rsi_sub_chartdata.candles[:-1]

        # Get CHoCH chart data
        choch_chartdata = self.get_chartdata(self.chart)
        choch_sub_chartdata = copy(choch_chartdata)
        choch_sub_chartdata.candles = choch_chartdata.candles[:-1]

        res = await self.find_signal(rsi_sub_chartdata, choch_chartdata)
        if res is None:
            return self.give_delay(choch_chartdata[-1])
        if isinstance(res, tuple):
            signal, position = res
        else:
            signal = res
            position = None
        return self.give_delay(choch_sub_chartdata[-1], jump=True), signal, position
