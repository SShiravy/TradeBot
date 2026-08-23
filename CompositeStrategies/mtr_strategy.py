from datetime import timedelta
from AutoTrendlineModule.auto_trendline import AutoTrendlines
from ChochQueueStrategy.choch_queue import ChochQueueFilter
from CompositeStrategies.models import DummyStrategy, MTRSignal
from Forex.agent import ForexAgent
from TradingModule.models import ExchangeAgent
from custom_logger import CustomLogger
from ChartModule.models import (
    Candle,
    Chart,
    ChartData,
)
from ChartModule.plot import ChartPlot
from TradingModule.reporter import TelegramReporter
from TradingModule.trader_bot import TradeConfig
from dataclasses import dataclass, field
from copy import copy
import logging


logger = CustomLogger(
    log_file=True, file_log_name="MTR_Signal", consol_log_level=logging.DEBUG
)


@dataclass(kw_only=True)
class MTRConfig(TradeConfig):
    strategy: DummyStrategy = field(default=DummyStrategy("MTR"))  # type: ignore[override]
    agent: ExchangeAgent = field(default=ForexAgent(), init=False)
    mtr_indicator: AutoTrendlines
    last_signal_msg_id: int | None = field(default=None, init=False)
    last_checked_candle: Candle | None = field(default=None, init=False)
    last_mtr_signal: MTRSignal | None = field(default=None, init=False)

    async def find_signal(self, chartdata: ChartData) -> None | MTRSignal:
        # Check for MTR Signal
        if (
            self.last_checked_candle
            and self.last_checked_candle == chartdata.candles[-1]
        ):
            return None

        self.mtr_indicator.set(chartdata.candles)
        self.last_checked_candle = chartdata.candles[-1]
        if (
            self.mtr_indicator.mtr_events
            and self.mtr_indicator.mtr_events[-1].candle == chartdata.candles[-1]
        ):
            mtr = self.mtr_indicator.mtr_events[-1]
            self.last_mtr_signal = MTRSignal(
                chartdata.chart, chartdata.candles[-1], mtr.side, "MTR", mtr
            )
            if self.send_signal:
                plot = ChartPlot(chartdata, self.n_candle_check)
                self.mtr_indicator.plot(plot)
                plot.mark_signal(
                    self.last_mtr_signal,
                )
                self.last_mtr_signal_msg_id = await TelegramReporter().new_signal(
                    self.last_mtr_signal, plot, self.last_signal_msg_id
                )
            return self.last_mtr_signal

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
        chartdata = self.get_chartdata(self.chart)
        sub_chartdata = copy(chartdata)
        sub_chartdata.candles = chartdata.candles[:-1]

        res = await self.find_signal(sub_chartdata)
        if res is None:
            return self.give_delay(chartdata[-1])
        if isinstance(res, tuple):
            signal, position = res
        else:
            signal = res
            position = None
        return self.give_delay(sub_chartdata[-1], jump=True), signal, position
