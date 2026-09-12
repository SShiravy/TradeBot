from BitUnix import BitUnixAgent
from ChartModule import Chart, ChartData, Candle
from DivergenceStrategy.divergence import Divergence, DivergenceTradeConfig
from ChochQueueStrategy.choch_queue import ChochQueueFilter, ChochQueueTradeConfig
from EmaPivotChochStrategy.ema_pivot_choch import (
    EmaPivotChochFilter,
    EmaPivotChochTradeConfig,
)
from EmaTouchStrategy.ema_touch import EmaTouchFilter, EmaTouchTradeConfig
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
import logging


@dataclass(kw_only=True)
class BitUnixDiverTradeConfig(DivergenceTradeConfig):
    second_chart: Chart
    agent: BitUnixAgent  # type: ignore[override]
    strategy: Divergence  # type: ignore[override]

    def give_delay(self, last_candle: Candle, jump=False) -> timedelta:
        delay = (
            self.chart.timeframe.time_delta * 2
        )  # *2 , because bitunix does'nt give the current not closed candle
        if jump:
            delay *= self.bar_between_signals
        next_timestamp = int(
            round(last_candle.time.astimezone(tz=timezone.utc).timestamp())
            + delay.total_seconds()
        )
        now_timestamp = round(datetime.now(tz=timezone.utc).timestamp())
        sleep_time_based_on_timestamp = next_timestamp - now_timestamp
        logging.debug(
            f"{next_timestamp=} | {last_candle.time.astimezone(tz=timezone.utc).timestamp()} | {now_timestamp} | {sleep_time_based_on_timestamp=}"
        )
        return timedelta(seconds=sleep_time_based_on_timestamp + 1)

    def get_chartdata(self, n_bar: int | None = None) -> tuple[ChartData, ChartData]:  # type: ignore[override]
        base_chartdata = self.agent.get_chartdata(
            self.chart, n_bar if n_bar else self.n_candle_check
        )
        other_chartdata = self.agent.get_chartdata(
            self.second_chart, n_bar if n_bar else self.n_candle_check
        )

        if base_chartdata is None or other_chartdata is None:
            raise ValueError(f"chart data is None from {self.agent.__class__.__name__}")

        crosspair_chart = Chart(
            symbol=base_chartdata.chart.symbol.replace("USDT", "")
            + other_chartdata.chart.symbol.replace("USDT", ""),
            timeframe=base_chartdata.chart.timeframe,
            precision=base_chartdata.chart.precision,
        )
        second_chartdata = ChartData.generate_crosspair(
            base_chartdata, other_chartdata, crosspair_chart
        )
        if self.heikingashi_chartdata:
            base_chartdata = base_chartdata.give_heikingashi_chartdata()
            second_chartdata = second_chartdata.give_heikingashi_chartdata()
        return base_chartdata, second_chartdata

    async def task(self):
        # bitunix does'nt give the current candle
        base_chartdata, second_chartdata = self.get_chartdata()
        res = await self.find_signal(base_chartdata, second_chartdata)
        if res is None:
            return self.give_delay(base_chartdata[-1])
        signal, position = res
        return self.give_delay(base_chartdata[-1], jump=True), signal, position


@dataclass(kw_only=True)
class BitUnixChochQueueTradeConfig(ChochQueueTradeConfig):
    agent: BitUnixAgent  # type: ignore[override]
    strategy: ChochQueueFilter  # type: ignore[override]

    def give_delay(self, last_candle: Candle, jump=False) -> timedelta:
        delay = (
            self.chart.timeframe.time_delta * 2
        )  # bitunix does'nt give the current not closed candle
        if jump:
            delay *= self.bar_between_signals
        next_timestamp = int(
            round(last_candle.time.astimezone(tz=timezone.utc).timestamp())
            + delay.total_seconds()
        )
        now_timestamp = round(datetime.now(tz=timezone.utc).timestamp())
        sleep_time_based_on_timestamp = next_timestamp - now_timestamp
        logging.debug(
            f"{next_timestamp=} | {last_candle.time.astimezone(tz=timezone.utc).timestamp()} | {now_timestamp} | {sleep_time_based_on_timestamp=}"
        )
        return timedelta(seconds=sleep_time_based_on_timestamp + 1)


@dataclass(kw_only=True)
class BitUnixEmaPivotChochTradeConfig(EmaPivotChochTradeConfig):
    agent: BitUnixAgent  # type: ignore[override]
    strategy: EmaPivotChochFilter  # type: ignore[override]

    def give_delay(self, last_candle: Candle, jump=False) -> timedelta:
        delay = (
            self.chart.timeframe.time_delta * 2
        )  # bitunix does'nt give the current not closed candle
        if jump:
            delay *= self.bar_between_signals
        next_timestamp = int(
            round(last_candle.time.astimezone(tz=timezone.utc).timestamp())
            + delay.total_seconds()
        )
        now_timestamp = round(datetime.now(tz=timezone.utc).timestamp())
        sleep_time_based_on_timestamp = next_timestamp - now_timestamp
        logging.debug(
            f"{next_timestamp=} | {last_candle.time.astimezone(tz=timezone.utc).timestamp()} | {now_timestamp} | {sleep_time_based_on_timestamp=}"
        )
        return timedelta(seconds=sleep_time_based_on_timestamp + 1)


@dataclass(kw_only=True)
class BitUnixEmaTouchTradeConfig(EmaTouchTradeConfig):
    agent: BitUnixAgent  # type: ignore[override]
    strategy: EmaTouchFilter  # type: ignore[override]

    def give_delay(self, last_candle: Candle, jump=False) -> timedelta:
        delay = (
            self.chart.timeframe.time_delta * 2
        )  # bitunix does'nt give the current not closed candle
        if jump:
            delay *= self.bar_between_signals
        next_timestamp = int(
            round(last_candle.time.astimezone(tz=timezone.utc).timestamp())
            + delay.total_seconds()
        )
        now_timestamp = round(datetime.now(tz=timezone.utc).timestamp())
        sleep_time_based_on_timestamp = next_timestamp - now_timestamp
        logging.debug(
            f"{next_timestamp=} | {last_candle.time.astimezone(tz=timezone.utc).timestamp()} | {now_timestamp} | {sleep_time_based_on_timestamp=}"
        )
        return timedelta(seconds=sleep_time_based_on_timestamp + 1)
