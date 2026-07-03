from TradingModule import ExchangeAgent, Position, commands, PositionsReport
from TradingModule.reporter import TelegramReporter
from BacktestModule.dummy_models import DummyAgent, DummyPositionHanler
from TradingModule.PositionHandlers.model import PositionHandler
from ChartModule.models import Chart, Candle, Signal, ChartData
from TradingModule.models import Strategy
from ChartModule.plot import ChartPlot
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from copy import copy
import tracemalloc
import asyncio
import logging


@dataclass(kw_only=True)
class TradeConfig:
    chart: Chart
    agent: ExchangeAgent
    strategy: Strategy
    position_handler: PositionHandler

    long_signal: bool = field(default=True)
    short_signal: bool = field(default=True)

    bar_between_signals: int = field(default=2)
    send_signal: bool = field(default=True)

    n_candle_check: int = field(default=1000)

    heikingashi_chartdata: bool = field(default=False)

    max_long_lose: int = field(default=3)
    max_short_lose: int = field(default=3)

    _n_losed_long: int = field(default=0, init=False)
    _n_losed_short: int = field(default=0, init=False)

    def export_config(self) -> dict:
        return {
            "chart": self.chart.export_config(),
            "bar_between_signals": self.bar_between_signals,
            "heikingashi_chartdata": self.heikingashi_chartdata,
        }

    def give_delay(self, last_candle: Candle, jump=False) -> timedelta:
        delay = self.chart.timeframe.time_delta
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

    def get_chartdata(self, n_bar: int | None = None) -> ChartData:
        chartdata = self.agent.get_chartdata(
            self.chart, n_bars=n_bar if n_bar else self.n_candle_check
        )
        if chartdata is None:
            raise ValueError(f"chart data is None from {self.agent.__class__.__name__}")
        if self.heikingashi_chartdata:
            chartdata = chartdata.give_heikingashi_chartdata()
        return chartdata

    async def find_signal(
        self, chartdata: ChartData, consider_position: bool = True, *args, **kwargs
    ) -> None | tuple[Signal, Position] | Signal:
        signal = self.strategy.check_signal(
            chartdata, self.long_signal, self.short_signal
        )
        if signal is None:
            return None

        plot = None
        if self.send_signal:
            plot = ChartPlot(chartdata)
            self.strategy.draw(plot, signal, draw_indicators=True)
        if not consider_position:
            return signal
        position = await self.position_handler.generate_position(signal)
        if not position:
            return None
        return signal, position

    async def task(self) -> timedelta | tuple[timedelta, Signal, Position]:
        chartdata = self.get_chartdata()
        res = await self.find_signal(chartdata, consider_position=True)
        if res is None:
            return self.give_delay(chartdata[-1])
        signal, position = res  # type: ignore
        return self.give_delay(chartdata[-1], jump=True), signal, position

    async def backtest(
        self,
        n_bar=500,
        show_image=True,
        len_sub_data=100,
        consider_positions=True,
        *args,
        **kwargs,
    ):
        logger = logging.getLogger(f"{self.__class__.__name__} Backtest")

        if consider_positions:
            position_handler = copy(self.position_handler)
        else:
            position_handler = DummyPositionHanler()
            self.position_handler = position_handler

        chartdata = self.get_chartdata(n_bar)
        if chartdata is None:
            raise ValueError(f"{chartdata=}")

        agent = DummyAgent(
            self.agent,
            chartdata=chartdata,
            open_positions=position_handler.open_positions,
            start_index=len_sub_data,
        )

        position_handler.exchange_agent = agent
        position_handler.long_trade = False
        position_handler.short_trade = False
        self.agent = agent
        self.send_signal = False

        all_positions: list[Position] = []
        all_signals: list[Signal] = []

        while agent.index < len(agent.chartdata.candles) - 1:  # type: ignore
            if consider_positions:
                position_handler.manage_positions()
                await commands.TradeCommand.execute_pending_commands(
                    time=agent.get_chartdata(self.chart)[-1].time,  # type: ignore
                    report=False,
                )
            res = await self.task()
            if isinstance(res, timedelta):
                candle_delay = 1
            else:
                all_signals.append(res[1])
                if consider_positions:
                    all_positions.append(res[2])
                candle_delay = self.bar_between_signals + 1
            agent.index += candle_delay

            logger.debug(f"{candle_delay} Candle next")
        plot = ChartPlot(agent.chartdata)  # type: ignore
        for signal in all_signals:
            self.strategy.draw(plot, signal)
        for pos in all_positions:
            if not pos.closed:
                continue
            pos.plot = plot
            pos.draw()
        commands_report = commands.TradeCommand.close_records()
        all_reports = position_handler.report()
        logger.info("Result:\n\n" + commands_report)
        for poses_report in all_reports:
            logger.info("\n" + str(poses_report))
        overal_report = PositionsReport.give_overall_report(copy(all_reports))
        logger.info("\n" + str(overal_report))
        logger.info(
            f"total time: {agent.chartdata[-1].time - agent.chartdata[0].time} with {len(agent.chartdata.candles)} candles"  # type: ignore
        )
        if show_image:
            plot.show()

        return all_signals, all_positions, plot, all_reports, commands_report

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
        report_time: dict = {"h": 23, "m": 50},
    ):
        if not hasattr(cls, "_instance"):
            cls._instance = object.__new__(cls)
            cls.name = name
            cls.configs = configs
            cls.report_time = report_time
            cls._start_time = datetime.now(tz=timezone.utc).replace(microsecond=0)
        return cls._instance

    async def manage(self):
        while True:
            try:
                for config in self.configs:
                    config.position_handler.manage_positions()
                await commands.TradeCommand.execute_pending_commands()
                await asyncio.sleep(2)
            except Exception as e:
                logging.exception(f"Manage Failed: {e}")
                await asyncio.sleep(10)

    async def trade_task(self, config: TradeConfig):
        logging.info(f"Task with config:{str(config)} initilized")
        error_number = 0
        while True:
            try:
                res = await config.task()
                if isinstance(res, timedelta):
                    sleep_time = res
                else:
                    sleep_time = res[0]
                logging.info(
                    f"{config.chart.timeframe} Checked on {config.chart}. sleep for {sleep_time}"
                )

                if sleep_time.total_seconds() < 0:
                    raise ValueError(f"Negative sleep time: {sleep_time}, 1m sleep")

                await asyncio.sleep(sleep_time.total_seconds())
                error_number = 0

            except Exception as e:
                error_number += 1
                logging.exception(f"{error_number} Times Task failed :{e}\n{config}")
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
            await asyncio.sleep(3600)
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
        now = datetime.now(tz=timezone.utc)
        report_time = now.replace(
            hour=self.report_time["h"],
            minute=self.report_time["m"],
            second=0,
            microsecond=0,
        )
        if report_time < now:
            report_time += timedelta(days=1)
        sleep_time = report_time - now
        while True:
            logging.info(f"Next daily report in {sleep_time}")
            await asyncio.sleep(sleep_time.total_seconds())
            commands_report = commands.TradeCommand.close_records()
            await TelegramReporter().log_report(f"{self.name}\n{commands_report}")
            overall_report = []
            for config in self.configs:
                all_reports = config.position_handler.report()
                for report in all_reports:
                    await TelegramReporter().log_report(str(report))
                overall_report.append(PositionsReport.give_overall_report(all_reports))

            overall_report = sum(overall_report)
            await TelegramReporter().public_report(
                self.name + "\n" + str(overall_report)
            )

            now = datetime.now(tz=timezone.utc)
            report_time = (now + timedelta(days=1)).replace(
                hour=self.report_time["h"], minute=self.report_time["m"], microsecond=0
            )
            sleep_time = report_time - now

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
