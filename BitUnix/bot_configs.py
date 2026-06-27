from BitUnix import BitUnixAgent
from ChartModule import Chart, ChartData, Candle
from DivergenceStrategy.divergence import Divergence, DivergenceTradeConfig
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
        )  # just because bitunix do not give the current not closed candle
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
