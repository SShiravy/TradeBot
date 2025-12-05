from TradingModule import ExchangeAgent, Position, OrderSide, commands, PositionsReport
from TradingModule.reporter import TelegramReporter
from TradingModule.position_handlers import PositionHandler
from ChartModule.models import Chart, Candle, Signal, ChartData
from TradingModule.models import Strategy
from ChartModule.plot import PlotChart
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
import tracemalloc
import asyncio
import logging


@dataclass
class TradeConfig:
    chart: Chart
    agent: ExchangeAgent
    strategy: Strategy
    position_handler: PositionHandler

    long_signal: bool = field(default=True)
    short_signal: bool = field(default=True)

    bar_between_signals: int = field(default=2)
    send_signal: bool = field(default=True)

    n_candle_check: int = field(default=100)

    heikingashi_chartdata: bool = field(default=False)

    def give_delay(self, last_candle: Candle, jump=False) -> timedelta:
        delay = self.chart.timeframe.time_delta
        if jump:
            delay *= self.bar_between_signals

        logging.debug(
            f"{delay=}\n{last_candle}\n{last_candle.time=}\n{last_candle.time.astimezone(timezone.utc)=}\nnow={datetime.now(timezone.utc)}"
        )
        logging.debug(f"delay + lastcandl.time: {delay + last_candle.time}")
        logging.debug(
            f"delay + lastcandl.time - now: {(delay + last_candle.time) - datetime.now(timezone.utc)}"
        )

        return (
            (delay + last_candle.time)
            - datetime.now(timezone.utc)
            + timedelta(seconds=1)
        )

    def get_chartdata(self) -> ChartData:
        chartdata = self.agent.get_chartdata(self.chart, n_bars=self.n_candle_check)
        if chartdata is None:
            raise ValueError(f"chart data is None from {self.agent.__class__.__name__}")
        if self.heikingashi_chartdata:
            chartdata = chartdata.give_heikingashi_chartdata()
        return chartdata

    def find_signal(
        self, chartdata: ChartData, *args, **kwargs
    ) -> None | tuple[Signal, Position]:
        signal = self.strategy.check_signal(
            chartdata, self.long_signal, self.short_signal
        )
        if signal is None:
            return None

        position = self.position_handler.generate_position(signal)

        if (self.position_handler.long_trade and position.side is OrderSide.BUY) or (
            self.position_handler.short_trade and position.side is OrderSide.SELL
        ):
            commands.OpenPosition(position, self.agent)
        return signal, position

    async def task(self) -> timedelta | tuple[timedelta, Signal, Position]:
        chartdata = self.get_chartdata()
        res = self.find_signal(chartdata)
        if res is None:
            return self.give_delay(chartdata[-1])
        signal, position = res
        if self.send_signal:
            plot = PlotChart(chartdata)
            self.strategy.draw(plot, signal, draw_indicators=True)
            await TelegramReporter().new_position(position, plot)
        return self.give_delay(chartdata[-1], jump=True), signal, position

    def save_as_json(self, name: str):
        # TODO: merge all sub obj attr in a single dict
        pass

    def load_from_json(self, path: str):
        pass

    def __str__(self) -> str:
        msg_list = [
            str(self.chart),
            self.agent.__class__.__name__,
            self.strategy.name,
            self.position_handler.__class__.__name__,
        ]
        return "|".join(msg_list)


class TraderBot:
    def __new__(
        cls,
        name: str = "",
        configs: list[TradeConfig] = [],
        report_period=timedelta(hours=24),
    ):
        if not hasattr(cls, "_instance"):
            cls._instance = object.__new__(cls)
            cls.name = name
            cls.configs = configs
            cls.report_period = report_period
            cls._start_time = datetime.now(tz=timezone.utc).replace(microsecond=0)
        return cls._instance

    async def manage(self):
        while True:
            try:
                for config in self.configs:
                    config.position_handler.manage_positions()
                await commands.TradeCommand.execute_pending_commands()
                await asyncio.sleep(5)
            except Exception as e:
                logging.error(f"Manage Failed: {e}")
                await asyncio.sleep(10)

    async def trade_task(self, config: TradeConfig):
        logging.debug(f"Task with config:{str(config)} initilized")
        error_number = 0
        while True:
            try:
                logging.info(f"Checking {config.strategy.name} on {config.chart}")
                res = await config.task()
                if isinstance(res, timedelta):
                    sleep_time = res
                else:
                    sleep_time = res[0]
                logging.debug(f"{config.chart.timeframe} sleep: {sleep_time}")
                await asyncio.sleep(sleep_time.total_seconds())
                error_number = 0

            except Exception as e:
                error_number += 1
                logging.error(f"{error_number} Times Task failed :{e}\n{config}")
                if error_number == 3:
                    await TelegramReporter().log_report(
                        f"3 Times Error:{e}\non {config}"
                    )
                # Delay for half candle
                await asyncio.sleep(
                    int(config.chart.timeframe.time_delta.total_seconds() / 2)
                )

                if error_number > 6:
                    await TelegramReporter().log_report(
                        f"Error:{e}\non {config}\nMore Than 6 Times\nTask removed"
                    )
                    break
                continue

    async def heartbeat(self):
        while True:
            await asyncio.sleep(7200)
            current, peak = tracemalloc.get_traced_memory()
            elapsed_time = str(
                datetime.now(tz=timezone.utc).replace(microsecond=0) - self._start_time
            )
            msg = [
                f"{self.name}",
                f"👋🤖\nLifespan⌛:\n{elapsed_time}",
                f"Memory📝:\n{current / 1024 / 1024:.2f} MB\npeak: {peak / 1024 / 1024:.2f} MB",
            ]
            await TelegramReporter().log_report("\n".join(msg))

    async def report(self):
        while True:
            await asyncio.sleep(self.report_period.total_seconds())
            commands_report = commands.TradeCommand.close_records()
            await TelegramReporter().log_report(f"{self.name}\n{commands_report}")
            overall_report = []
            for config in self.configs:
                all_reports = config.position_handler.report()
                for report in all_reports:
                    await TelegramReporter().log_report(str(report))
                overall_report.append(PositionsReport.give_overall_report(all_reports))

            overall_report = sum(overall_report)
            if overall_report:
                await TelegramReporter().public_report(str(overall_report))

    async def start(self):
        tracemalloc.start()
        await TelegramReporter().log_report(
            f"--{self.name}--\n⚡⚡\nStart at\n{self._start_time} utc\n⚡⚡"
        )
        tasks = [self.trade_task(config) for config in self.configs]
        tasks.append(self.heartbeat())
        tasks.append(self.report())
        tasks.append(self.manage())
        await asyncio.gather(*tasks)
