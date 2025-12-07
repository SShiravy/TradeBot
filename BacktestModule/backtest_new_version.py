from ChartModule import ChartData, Chart, Signal
from ChartModule.plot import PlotChart
from TradingModule import TradeConfig, ExchangeAgent, Position, PositionsReport
from TradingModule import commands
from datetime import datetime, timedelta
from copy import deepcopy
import logging


logger = logging.getLogger("Backtest")


class DummyAgent(ExchangeAgent):
    def __init__(
        self,
        real_agent: ExchangeAgent,
        chart: Chart,
        total_candles=500,
        start_index=101,
    ) -> None:
        self.real_agent = real_agent
        chartdata = real_agent.get_chartdata(chart, total_candles)
        if chartdata is None:
            raise ValueError("chartdata is None in DummyAgent")
        self.chartdata = chartdata
        self.index = start_index
        logger.info("dummy agent initilized")

    def check_chart(self, chart: Chart) -> bool:
        return True

    def get_chartdata(self, chart: Chart, n_bars=100) -> ChartData:
        if chart.symbol != self.chartdata.chart.symbol:
            raise ValueError(f"{chart} != chartdata.chart:{self.chartdata.chart}")
        candles = deepcopy(self.chartdata[: self.index])
        data = ChartData(self.chartdata.chart, candles, self.chartdata.indicators)
        logger.debug(f"agent get chartdata: {len(data)=}")
        return data

    def get_candles_since(self, chart: Chart, time: datetime):
        return self.real_agent.get_candles_since(chart, time)

    def open_position(self, position: Position) -> float | None:
        return position.entry_price

    def get_open_positions(self, chart: Chart):
        return Backtest.config.position_handler.open_positions

    def change_stoploss(self, position: Position, price: float) -> bool:
        return True

    def change_takeprofit(self, position: Position, price: float) -> bool:
        return True

    def partial_close(self, position: Position, volume: float) -> float | None:
        logger.info(f"partial close {volume} on {Backtest.current_price}")
        return Backtest.current_price

    def close_position(self, position: Position) -> float | None:
        logger.info(f"close position on {Backtest.current_price}")
        return Backtest.current_price


class Backtest:
    def __new__(
        cls,
        config: TradeConfig,
        n_bar=500,
        len_sub_data: int | None = None,
        show_image=True,
    ):
        if not hasattr(cls, "_instance"):
            cls._instance = object.__new__(cls)
            cls.len_sub_data = len_sub_data if len_sub_data else config.n_candle_check
            cls.show_image = show_image
            cls.n_bar = n_bar
            cls.dummy_agent = DummyAgent(
                config.agent, config.chart, n_bar, config.n_candle_check
            )
            config.position_handler.long_trade = False
            config.position_handler.short_trade = False
            config.send_signal = False
            cls.config = config
            cls.n_bar = n_bar
            cls.current_price = 0.0
            cls.all_positions: list[Position] = []
            cls.all_signals: list[Signal] = []
        return cls._instance

    async def start_task_backtest(self):
        self.config.position_handler.exchange_agent = self.dummy_agent
        self.config.agent = self.dummy_agent
        while self.dummy_agent.index < len(self.dummy_agent.chartdata.candles) - 1:
            res = await self.config.task()
            if isinstance(res, timedelta):
                candle_delay = 1
            else:
                self.all_signals.append(res[1])
                self.all_positions.append(res[2])
                candle_delay = self.config.bar_between_signals + 1
            self.dummy_agent.index += candle_delay
            self.config.position_handler.manage_positions()
            await commands.TradeCommand.execute_pending_commands(
                time=self.config.agent.get_chartdata(self.config.chart)[-1].time,
                report=False,
            )
            logger.debug(f"{candle_delay} Candle next")

        plot = PlotChart(self.config.agent.chartdata)
        for signal in self.all_signals:
            self.config.strategy.draw(plot, signal)
        for pos in self.all_positions:
            pos.draw(plot)

        commands_report = commands.TradeCommand.close_records()
        all_reports = self.config.position_handler.report()
        logger.info("Result:\n\n" + commands_report)
        for poses_report in all_reports:
            logger.info("\n" + str(poses_report))
        overal_report = PositionsReport.give_overall_report(all_reports)
        logger.info("\n" + str(overal_report))
        logger.info(
            f"total time: {self.config.agent.chartdata[-1].time - self.config.agent.chartdata[0].time} with {len(self.config.agent.chartdata)} candles"
        )
        plot.show()
