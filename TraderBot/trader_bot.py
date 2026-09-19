import hashlib
import json
from Settings import TimeHandler
from TraderBot import ExchangeAgent, Position
import TraderBot.Commands as commands
from TraderBot.PositionHandlers.manager import TradesManager
from ChartModule.models import Chart, Signal, ChartData
from TraderBot.PositionHandlers.plot import PositionPlotter
from TraderBot.models import Strategy
from ChartModule.plot import SingleChartFigure, Figure
import logging


class TraderBot:
    def __init__(
        self,
        chart: Chart,
        agent: ExchangeAgent,
        strategy: Strategy,
        trades_manager: TradesManager,
        bar_between_signals: int = 2,
        n_candle_check: int = 1000,
        consider_position: bool = True,
    ):
        self.chart = chart
        self.agent = agent
        self.strategy = strategy
        self.trades_manager = trades_manager
        self.bar_between_signals = bar_between_signals
        self.n_candle_check = n_candle_check
        self.consider_position = consider_position

    def post_init(self):
        if not self.agent.prepare_chart(self.chart):
            raise ValueError(f"Failed to prepare chart for {self.identifier}")
        logging.info(f"{self.identifier} Bot initialized")

    @property
    def identifier(self):
        return f"{self.chart}_{self.strategy.name}"

    def export_config(self) -> dict:
        return {
            "chart": self.chart.export_config(),
            "strategy": self.strategy.export_config(),
            "trades_manager": self.trades_manager.export_config(),
            "bar_between_signals": self.bar_between_signals,
            "n_candle_check": self.n_candle_check,
        }

    def __hash__(self):
        raw = json.dumps(
            self.export_config(),
            sort_keys=True,
        ).encode()
        return int(hashlib.sha256(raw).hexdigest(), 16)

    def get_chartdata(
        self, n_bar: int | None = None, chart: Chart | None = None
    ) -> ChartData:
        chartdata = self.agent.get_chartdata(
            chart=chart if chart else self.chart,
            n_bars=n_bar if n_bar else self.n_candle_check,
        )
        if chartdata is None:
            raise ValueError(f"chart data is None from {self.agent.__class__.__name__}")
        return chartdata

    def give_delay(self, last_candle_timestamp: int, jump: int = 1) -> int:
        """
        return seconds of delay
        """
        bar_seconds = self.chart.timeframe.minutes * 60 * jump
        next_timestamp = last_candle_timestamp + bar_seconds
        delay = next_timestamp - TimeHandler.now()
        logging.debug(
            f"{bar_seconds=}|{jump=}|{next_timestamp=}|{TimeHandler.now()}|{last_candle_timestamp}|{delay=}"
        )
        return delay + 1

    def check_signal(self, chartdata: ChartData, *args, **kwargs) -> None | Signal:
        signal = self.strategy.check_signal(
            chartdata, self.trades_manager.long_trade, self.trades_manager.short_trade
        )
        if not signal:
            return None
        return signal

    def trade(
        self, signal: Signal, position: Position, plot: Figure
    ) -> Position | None:
        report_command = None
        if self.trades_manager.reporter and self.trades_manager.reporter.enable:
            PositionPlotter()(plot.main_pane, position)
            self.strategy.plotter(
                plot.main_pane,
                signal,
                self.strategy.indicators,
                self.strategy.indicators,
            )
            report_command = commands.NewPositionReport(plot=plot)
        commands.OpenPosition(report_command).send(
            self.trades_manager.give_command_contex(position)
        )
        return position

    async def task(self):
        chartdata = self.get_chartdata()
        last_timestamp = chartdata.timestamps[-1]
        chartdata = chartdata.subdata(end_index=-1)
        signal = self.check_signal(chartdata)
        if signal:
            if self.consider_position:
                position = self.trades_manager.generate_position(signal)
                if position:
                    plot = SingleChartFigure(chartdata)
                    self.trade(signal, position, plot)
            else:
                plot = SingleChartFigure(chartdata)
                self.strategy.plotter(plot.main_pane, signal, self.strategy.indicators)
                commands.NewSignalReport(signal, plot=plot).send(
                    reporter=self.trades_manager.reporter
                )

        return self.give_delay(last_timestamp)


# async def backtest(
#     self,
#     n_bar=500,
#     show_image=True,
#     len_sub_data=100,
#     *args,
#     **kwargs,
# ):
#     logger = logging.getLogger(f"{self.__class__.__name__} Backtest")

#     if self.consider_position:
#         position_handler = copy(self.position_generator)
#     else:
#         position_handler = DummyPositionHanler()
#         self.position_generator = position_handler

#     chartdata = self.get_chartdata(n_bar)
#     if chartdata is None:
#         raise ValueError(f"{chartdata=}")

#     agent = DummyAgent(
#         self.agent,
#         chartdata=chartdata,
#         open_positions=position_handler.open_positions,
#         start_index=len_sub_data,
#     )

#     position_handler.exchange_agent = agent
#     position_handler.long_trade = False
#     position_handler.short_trade = False
#     self.agent = agent
#     self.send_signal_msg = False

#     all_positions: list[Position] = []
#     all_signals: list[Signal] = []

#     while agent.index < len(agent.chartdata.candles) - 1:  # type: ignore
#         if self.consider_position:
#             position_handler.manage_positions()
#             await commands.Command.execute_pending_commands(
#                 time=agent.get_chartdata(self.chart)[-1].time,  # type: ignore
#                 report=False,
#             )
#         res = await self.task()
#         if isinstance(res, timedelta):
#             candle_delay = 1
#         else:
#             all_signals.append(res[1])
#             if self.consider_position:
#                 all_positions.append(res[2])  # type: ignore
#             candle_delay = self.bar_between_signals + 1
#         agent.index += candle_delay

#         logger.debug(f"{candle_delay} Candle next")
#     plot = ChartPlot(agent.chartdata)  # type: ignore
#     for signal in all_signals:
#         self.strategy.draw(plot, signal)
#     for pos in all_positions:
#         if not pos.closed_timestamp:
#             continue
#         pos.plot = plot
#         pos.draw()
#     commands_report = commands.Command.close_records()
#     all_reports = position_handler.report()
#     logger.info("Result:\n\n" + commands_report)
#     for poses_report in all_reports:
#         logger.info("\n" + str(poses_report))
#     overal_report = PositionsReport.give_overall_report(copy(all_reports))
#     logger.info("\n" + str(overal_report))
#     logger.info(
#         f"total time: {agent.chartdata[-1].time - agent.chartdata[0].time} with {len(agent.chartdata.candles)} candles"  # type: ignore
#     )
#     if show_image:
#         plot.show()

#     return all_signals, all_positions, plot, all_reports, commands_report
