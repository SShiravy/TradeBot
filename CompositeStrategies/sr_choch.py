from datetime import timedelta
from ChochQueueStrategy.choch_queue import ChochQueueFilter, ChochSignal
from Forex.agent import ForexAgent
from SRZoneModule.sr_zone import SRZones, ZoneModel
from custom_logger import CustomLogger
from ChartModule.models import (
    Candle,
    Chart,
    ChartData,
    MarketSide,
    Signal,
)
from ChartModule.plot import ChartPlot
from TradingModule.reporter import TelegramReporter
from TradingModule.trader_bot import TradeConfig, Position
from dataclasses import dataclass, field
from typing import Literal
from copy import copy
import logging


logger = CustomLogger(
    log_file=True, file_log_name="SR_Choch", consol_log_level=logging.DEBUG
)


@dataclass(slots=True, frozen=True)
class SRSignal(Signal):
    zone: ZoneModel
    touch_type: Literal["Shadow", "Body"]


@dataclass(kw_only=True)
class SR_ChochConfig(TradeConfig):
    strategy: ChochQueueFilter  # type: ignore[override]
    sr_indicator: SRZones
    sr_chart: Chart
    n_candle_confirmation: int = 10
    last_sr_signal: SRSignal | None = field(default=None, init=False)
    last_sr_signal_msg_id: int | None = field(default=None, init=False)
    last_sr_checked_candle: Candle | None = field(default=None, init=False)

    async def _check_sr(self, chartdata: ChartData):
        self.sr_indicator.set(chartdata.candles)  # or however you feed candles into it
        if not self.sr_indicator.candles or not self.sr_indicator.data:
            return None

        candle = self.sr_indicator.candles[-1]
        self.last_sr_checked_candle = candle

        candidates: list[ZoneModel] = []
        for zone in self.sr_indicator.data:
            if zone.broken:
                continue
            else:
                touched = candle.low <= zone.upper and zone.lower <= candle.high

            if touched:
                candidates.append(zone)

        if not candidates:
            return None

        best_zone = max(candidates, key=lambda z: z.score_pct)

        side = MarketSide.BULLISH if best_zone.is_support else MarketSide.BEARISH
        body_low = min(candle.body_top, candle.body_bottom)
        body_high = max(candle.body_top, candle.body_bottom)
        touch_type = (
            "Body"
            if (body_low <= best_zone.upper and best_zone.lower <= body_high)
            else "Shadow"
        )

        self.last_sr_signal = SRSignal(
            self.sr_chart,
            candle,
            side,
            source="S&R",
            zone=best_zone,
            touch_type=touch_type,
        )
        logger.info(f"S&R Signal:{self.last_sr_signal}")
        if self.send_signal:
            plot = ChartPlot(
                chartdata,
                plot_n_candles=self.n_candle_check,
            )

            self.sr_indicator.plot(plot)
            plot.mark_signal(
                self.last_sr_signal,
            )
            self.last_sr_signal_msg_id = await TelegramReporter().new_signal(
                self.last_sr_signal, plot
            )

    def _check_choch(self, chartdata: ChartData):
        signal = self.strategy.check_signal(
            chartdata, self.long_signal, self.short_signal
        )
        if signal is None or not signal.choch_model.is_choch:
            return None
        return signal

    async def find_signal(
        self, chartdata: ChartData, choch_chartdata: ChartData
    ) -> None | ChochSignal | tuple[ChochSignal, Position]:
        # Check for S&R
        await self._check_sr(chartdata)
        if self.last_sr_signal is None:
            return None

        # Check if the last signal is too old
        elapsed_time = (
            chartdata.candles[-1].time - self.last_sr_signal.candle.time
        ).total_seconds()
        time_condition = (
            self.n_candle_confirmation
            * chartdata.chart.timeframe.time_delta.total_seconds()
        )
        if elapsed_time > time_condition:
            self.last_sr_signal = None
            self.last_sr_signal_msg_id = None
            logging.warning(f"S&R was too old {elapsed_time=} > {time_condition}")
            return None

        # Check for CHoCH signal
        choch_signal = self._check_choch(choch_chartdata)
        if choch_signal is None:
            return None

        # Check if the CHoCH signal is in the same direction as the last SR signal
        if choch_signal.side != self.last_sr_signal.side:
            logging.warning(
                f"different side for SR & choch: {self.last_sr_signal.side} | {choch_signal.side}"
            )
            return None

        # Generate position based on the combined signals
        plot = None
        if self.send_signal:
            plot = ChartPlot(choch_chartdata)
            self.strategy.draw(plot, choch_signal, draw_indicators=True)
        if not self.consider_position:
            if self.send_signal:
                await TelegramReporter().new_signal(
                    choch_signal, plot, self.last_sr_signal_msg_id
                )
            return choch_signal

        position = await self.position_handler.generate_position(
            choch_signal, sl_base_price=choch_signal.choch_model.anchor, plot=plot
        )
        if not position:
            logger.warning("Position is None")
            return None
        logger.info("SR & CHoCH Signal")
        position.reply_msg_id = self.last_sr_signal_msg_id
        self.last_sr_signal = None
        self.last_sr_signal_msg_id = None
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
        # SR chart data
        sr_chartdata = self.get_chartdata(self.sr_chart)
        sr_sub_chartdata = copy(sr_chartdata)
        sr_sub_chartdata.candles = sr_sub_chartdata.candles[:-1]

        # Get CHoCH chart data
        choch_chartdata = self.get_chartdata(self.chart)
        choch_sub_chartdata = copy(choch_chartdata)
        choch_sub_chartdata.candles = choch_chartdata.candles[:-1]

        res = await self.find_signal(sr_sub_chartdata, choch_chartdata)
        if res is None:
            return self.give_delay(choch_chartdata[-1])
        if isinstance(res, tuple):
            signal, position = res
        else:
            signal = res
            position = None
        return self.give_delay(choch_sub_chartdata[-1], jump=True), signal, position
