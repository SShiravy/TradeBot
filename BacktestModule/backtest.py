from ChartModule import ChartData, Chart, Signal
from ChartModule.plot import PlotChart, TwoChartPlot
from TradingModule import TradeConfig, ExchangeAgent, Position, PositionsReport
from TradingModule import commands
from TradingModule.Strategies.divergence import DivergenceTradeConfig, DivergenceSignal
from datetime import datetime
from copy import copy
import logging

logger = logging.getLogger("Backtest")


class DummyAgent(ExchangeAgent):
    def __init__(self, real_agent: ExchangeAgent) -> None:
        self.real_agent = real_agent
        logger.info("dummy agent initilized")

    def check_chart(self, chart: Chart) -> bool:
        return self.real_agent.check_chart(chart)

    def get_chartdata(self, chart: Chart, n_bars=100) -> ChartData | None:
        return self.real_agent.get_chartdata(chart, n_bars)

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
    def __new__(cls, config: TradeConfig, n_bar=500, len_sub_data: int | None = None):
        if not hasattr(cls, "_instance"):
            cls._instance = object.__new__(cls)
            dummy_agent = DummyAgent(config.agent)
            config.agent = dummy_agent
            config.position_handler.exchange_agent = dummy_agent
            cls.len_sub_data = len_sub_data if len_sub_data else config.n_candle_check
            config.n_candle_check = n_bar
            config.position_handler.long_trade = False
            config.position_handler.short_trade = False
            config.send_signal = False
            cls.config = config
            cls.n_bar = n_bar
            cls.current_price = 0.0
            cls.all_positions: list[Position] = []
            cls.all_signals: list[Signal | DivergenceSignal] = []
        return cls._instance

    async def diver_backtest(self, show_image=True):
        if not isinstance(self.config, DivergenceTradeConfig):
            return
        jump = 0
        base_chartdata, second_chartdata = self.config.get_chartdata()
        for i in range(self.len_sub_data, len(base_chartdata) - 2):
            base_sub_data = ChartData(
                base_chartdata.chart, base_chartdata[:i], base_chartdata.indicators
            )
            seocnd_sub_data = ChartData(
                second_chartdata.chart,
                second_chartdata[:i],
                second_chartdata.indicators,
            )

            candle = base_chartdata[i]
            self.current_price = candle.open
            all_pos = copy(self.config.position_handler.open_positions)
            for pos in all_pos:
                if pos.closed:
                    self.config.position_handler.closed_positions.append(pos)
                    self.config.position_handler.open_positions.remove(pos)
                    continue
                self.config.position_handler.handler(
                    pos, [candle.open, candle.low, candle.high, candle.close]
                )
            await commands.TradeCommand.execute_pending_commands(candle.time, False)

            if jump > 0:
                jump -= 1
                continue
            res = self.config.find_signal(base_sub_data, seocnd_sub_data)
            if res is None:
                continue
            jump = self.config.bar_between_signals
            signal, position = res
            self.all_signals.append(signal)
            self.all_positions.append(position)
            open = commands.OpenPosition(position, self.config.agent)
            await open.execute(candle.time)

        plot = TwoChartPlot(base_chartdata, second_chartdata)
        for signal in self.all_signals:
            self.config.strategy.draw(plot, signal)  # type: ignore
        for pos in self.all_positions:
            if not pos.closed:
                continue
            pos.draw(plot.base_plot)
        img_path = plot.save_image(
            f"backtest_{str(self.config.chart)}{str(self.config.strategy.name)}",
            path="Backtest/Images/",
        )
        commands_report = commands.TradeCommand.close_records()
        all_reports = self.config.position_handler.report()
        logger.info("Result:\n\n" + commands_report)
        for poses_report in all_reports:
            logger.info("\n" + str(poses_report))
        overal_report = PositionsReport.give_overall_report(all_reports)
        logger.info("\n" + str(overal_report))

        if show_image:
            plot.show()
        return commands_report, img_path

    async def start_backtest(self, show_image=True):
        if isinstance(self.config, DivergenceTradeConfig):
            return self.diver_backtest(show_image)
        jump = 0
        chartdata = self.config.get_chartdata()
        for i in range(self.len_sub_data, len(chartdata) - 2):
            sub_data = ChartData(chartdata.chart, chartdata[:i], chartdata.indicators)
            candle = chartdata[i]
            self.current_price = candle.open
            all_pos = copy(self.config.position_handler.open_positions)
            for pos in all_pos:
                if pos.closed:
                    self.config.position_handler.closed_positions.append(pos)
                    self.config.position_handler.open_positions.remove(pos)
                    continue
                self.config.position_handler.handler(
                    pos, [candle.open, candle.low, candle.high, candle.close]
                )
            await commands.TradeCommand.execute_pending_commands(candle.time, False)

            if jump > 0:
                jump -= 1
                continue
            res = self.config.find_signal(sub_data)
            if res is None:
                continue
            jump = self.config.bar_between_signals
            signal, position = res
            self.all_signals.append(signal)
            self.all_positions.append(position)
            open = commands.OpenPosition(position, self.config.agent)
            await open.execute(candle.time)

        plot = PlotChart(chartdata)
        for signal in self.all_signals:
            self.config.strategy.draw(plot, signal)  # type: ignore
        for pos in self.all_positions:
            if not pos.closed:
                continue
            pos.draw(plot)
        img_path = plot.save_image(
            f"backtest_{str(self.config.chart)}{str(self.config.strategy.name)}",
            path="Backtest/Images/",
        )
        commands_report = commands.TradeCommand.close_records()
        all_reports = self.config.position_handler.report()
        logger.info("Result:\n\n" + commands_report)
        for poses_report in all_reports:
            logger.info("\n" + str(poses_report))
        overal_report = PositionsReport.give_overall_report(all_reports)
        logger.info("\n" + str(overal_report))

        if show_image:
            plot.show()
        return commands_report, img_path
