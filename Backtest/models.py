from ChartModule import ChartData, Chart, Signal
from ChartModule.plot import PlotChart, TwoChartPlot
from TradingModule import TradeConfig, ExchangeAgent, Position
from TradingModule.commands import TradeCommand
from TradingModule.Strategies.divergence import DivergenceTradeConfig, DivergenceSignal
from datetime import datetime, timezone
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

    def get_chartdata_since(self, chart: Chart, time: datetime) -> ChartData | None:
        return self.get_chartdata_since(chart, time)

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
            cls.len_sub_data = len_sub_data if len_sub_data else config.n_candle_check
            config.n_candle_check = n_bar
            cls.config = config
            cls.n_bar = n_bar
            cls.current_price = 0.0
            cls.all_positions: list[Position] = []
            cls.all_signals: list[Signal | DivergenceSignal] = []
            cls._start_time = datetime.now(tz=timezone.utc).replace(microsecond=0)
        return cls._instance

    def diver_backtest(self, show_image=True):
        if not isinstance(self.config, DivergenceTradeConfig):
            return
        base_chartdata, second_chartdata = self.config.get_chartdata()
        for i in range(self.len_sub_data, len(base_chartdata) - 1):
            sub_base_data = ChartData(
                base_chartdata.chart, base_chartdata[:i], base_chartdata.indicators
            )
            sub_seocnd_data = ChartData(
                second_chartdata.chart,
                second_chartdata[:i],
                second_chartdata.indicators,
            )

            self.current_price = base_chartdata[i + 1]

            TradeCommand.execute_pending_commands(self.config.agent)

            res = self.config.find_signal(sub_base_data, sub_seocnd_data)
            if res is None:
                continue
            signal, position = res
            self.all_signals.append(signal)
            self.all_positions.append(position)

        plot = TwoChartPlot(base_chartdata, second_chartdata)
        for signal in self.all_signals:
            self.config.strategy.draw(plot, signal)  # type: ignore
        for indicator in self.config.strategy.confirmation_indicators:
            indicator.plot(plot)
        for pos in self.all_positions:
            pos.draw(plot.base_plot)
        img_path = plot.save_image(
            f"backtest_{str(self.config.chart)}{str(self.config.strategy.name)}",
            path="Backtest/Images/",
        )
        commands_report = TradeCommand.close_records()
        positions_report = self.config.position_handler.report()
        logger.info("Result:\n\n" + commands_report + "\n\n" + positions_report)
        if show_image:
            plot.show()
        return commands_report, positions_report, img_path

    def start_backtest(self, show_image=True):
        if isinstance(self.config, DivergenceTradeConfig):
            return self.diver_backtest(show_image)
        chartdata = self.config.get_chartdata()
        for i in range(self.len_sub_data, len(chartdata) - 1):
            sub_data = chartdata[:i]
            self.current_price = chartdata[i + 1]
            TradeCommand.execute_pending_commands(self.config.agent)

            res = self.config.find_signal(sub_data)
            if res is None:
                continue
            signal, position = res
            self.all_signals.append(signal)
            self.all_positions.append(position)

        plot = PlotChart(chartdata)
        for signal in self.all_signals:
            plot.mark_signal(signal)
        for indicator in self.config.strategy.confirmation_indicators:
            indicator.plot(plot)
        for pos in self.all_positions:
            pos.draw(plot)
        img_path = plot.save_image(
            f"backtest_{str(self.config.chart)}{str(self.config.strategy.name)}",
            path="Backtest/Images/",
        )
        commands_report = TradeCommand.close_records()
        positions_report = self.config.position_handler.report()
        logger.info(commands_report + "\n\n" + positions_report)
        if show_image:
            plot.show()
        return commands_report, positions_report, img_path
