from TraderBot import ExchangeAgent, Position, commands, PositionsReport
from TraderBot.reporter import TelegramReporter
from BacktestModule.dummy_models import DummyAgent, DummyPositionHanler
from TraderBot.PositionHandlers.manager import PositionGenerator, TradesManager
from ChartModule.models import Chart, Candle, Signal, ChartData
from TraderBot.models import Strategy
from ChartModule.plot import ChartPlot
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from copy import copy
import logging


@dataclass(kw_only=True)
class TraderBot:
    chart: Chart
    agent: ExchangeAgent
    strategy: Strategy
    position_generator: PositionGenerator
    position_manager: TradesManager

    bar_between_signals: int = field(default=2)
    signal_msg_sender: bool = field(default=True)

    n_candle_check: int = field(default=1000)

    max_long_lose: int = field(default=3)
    max_short_lose: int = field(default=3)

    _n_losed_long: int = field(default=0, init=False)
    _n_losed_short: int = field(default=0, init=False)

    consider_position: bool = field(default=True)

    def export_config(self) -> dict:
        return {
            "chart": self.chart.export_config(),
            "bar_between_signals": self.bar_between_signals,
        }

    def give_delay(self, last_candle: Candle, jump=False) -> timedelta:
        delay = self.chart.timeframe.time_delta
        if jump:
            delay *= self.bar_between_signals
        next_timestamp = int(round(last_candle.timestamp) + delay.total_seconds())
        now_timestamp = round(datetime.now(tz=timezone.utc).timestamp())
        sleep_time_based_on_timestamp = next_timestamp - now_timestamp
        logging.debug(
            f"{next_timestamp=} | {last_candle.timestamp} | {now_timestamp} | {sleep_time_based_on_timestamp=}"
        )
        return timedelta(seconds=sleep_time_based_on_timestamp + 1)

    def get_chartdata(self, n_bar: int | None = None) -> ChartData:
        chartdata = self.agent.get_chartdata(
            self.chart, n_bars=n_bar if n_bar else self.n_candle_check
        )
        if chartdata is None:
            raise ValueError(f"chart data is None from {self.agent.__class__.__name__}")
        return chartdata

    async def find_signal(
        self, chartdata: ChartData, *args, **kwargs
    ) -> None | tuple[Signal, Position] | Signal:
        signal = self.strategy.check_signal(
            chartdata, self.long_signal, self.short_signal
        )
        if signal is None:
            return None

        plot = None
        if self.send_signal_msg:
            plot = ChartPlot(chartdata)
            self.strategy.draw(plot, signal, draw_indicators=True)
        if not self.consider_position:
            if self.send_signal_msg:
                await TelegramReporter().new_signal(signal, plot)
            return signal
        position = await self.position_generator.generate(signal)
        if not position:
            return None
        return signal, position

    async def task(self) -> timedelta | tuple[timedelta, Signal, Position | None]:
        chartdata = self.get_chartdata()
        res = await self.find_signal(chartdata)
        if res is None:
            return self.give_delay(chartdata[-1])
        if isinstance(res, tuple):
            signal, position = res
        else:
            signal = res
            position = None
        return self.give_delay(chartdata[-1], jump=True), signal, position

    async def backtest(
        self,
        n_bar=500,
        show_image=True,
        len_sub_data=100,
        *args,
        **kwargs,
    ):
        logger = logging.getLogger(f"{self.__class__.__name__} Backtest")

        if self.consider_position:
            position_handler = copy(self.position_generator)
        else:
            position_handler = DummyPositionHanler()
            self.position_generator = position_handler

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
        self.send_signal_msg = False

        all_positions: list[Position] = []
        all_signals: list[Signal] = []

        while agent.index < len(agent.chartdata.candles) - 1:  # type: ignore
            if self.consider_position:
                position_handler.manage_positions()
                await commands.Command.execute_pending_commands(
                    time=agent.get_chartdata(self.chart)[-1].time,  # type: ignore
                    report=False,
                )
            res = await self.task()
            if isinstance(res, timedelta):
                candle_delay = 1
            else:
                all_signals.append(res[1])
                if self.consider_position:
                    all_positions.append(res[2])  # type: ignore
                candle_delay = self.bar_between_signals + 1
            agent.index += candle_delay

            logger.debug(f"{candle_delay} Candle next")
        plot = ChartPlot(agent.chartdata)  # type: ignore
        for signal in all_signals:
            self.strategy.draw(plot, signal)
        for pos in all_positions:
            if not pos.closed_timestamp:
                continue
            pos.plot = plot
            pos.draw()
        commands_report = commands.Command.close_records()
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
            self.position_generator.__class__.__name__,
        ]
        return "|".join(msg_list)
