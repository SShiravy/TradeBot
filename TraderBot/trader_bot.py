import hashlib
import json
from Settings import TimeHandler
from TraderBot import ExchangeAgent, Position
from TraderBot.Commands.db_commands import DatabaseCommandContext
from TraderBot.Commands.report_commands import ReportCommandContext
from TraderBot.Commands.trade_commands import TradeCommandContext
from TraderBot.PositionHandlers.manager import TradesManager
from ChartModule.models import Chart, Signal, ChartData
from TraderBot.PositionHandlers.plot import PositionPlotter
from TraderBot.events import NewPosition, NewSignal
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
        self.consider_figure = True

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
        if getattr(self, "_hash", None) is None:
            raw = json.dumps(
                self.export_config(),
                sort_keys=True,
            ).encode()
            self._hash = int(hashlib.sha256(raw).hexdigest(), 16)
        return self._hash

    @property
    def config_hash(self) -> str:
        """
        The hash this bot is recorded under in the db, the one every row of
        it hangs on. Database imports this module, so it is imported here.
        """
        if getattr(self, "_config_hash", None) is None:
            from Database import TraderBotRow

            self._config_hash = TraderBotRow.give_config_hash(self)
        return self._config_hash

    def give_record_context(self) -> DatabaseCommandContext:
        """The context the db commands of this bot run on."""
        return DatabaseCommandContext(bot_hash=self.config_hash)

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
        if last_candle_timestamp == getattr(self, "last_candle_timestamp", None):
            return 5
        self.last_candle_timestamp = last_candle_timestamp
        bar_seconds = self.chart.timeframe.minutes * 60 * jump
        next_timestamp = last_candle_timestamp + bar_seconds
        delay = next_timestamp - TimeHandler.now()
        logging.debug(
            f"{bar_seconds=}|{jump=}|{next_timestamp=}|{TimeHandler.now()}|{last_candle_timestamp}|{delay=}"
        )
        if delay <= 0:
            delay = 4

        return delay + 1

    def check_signal(self, chartdata: ChartData, *args, **kwargs) -> None | Signal:
        signal = self.strategy.check_signal(
            chartdata, self.trades_manager.long_trade, self.trades_manager.short_trade
        )
        if not signal:
            return None
        return signal

    def generate_figure(
        self,
        chartdata: ChartData,
        signal: Signal,
        position: Position | None = None,
        *args,
        **kwargs,
    ) -> Figure | None:
        if not self.consider_figure:
            return None
        figure = SingleChartFigure(
            chartdata,
            self.n_candle_check,
        )
        self.strategy.plotter(figure.main_pane, signal, self.strategy.indicators)
        if position:
            PositionPlotter()(figure.main_pane, position)
        return figure

    def trade(self, position: Position, plot: Figure | None) -> Position | None:
        NewPosition(
            trade_context=TradeCommandContext(position, self.agent),
            report_context=ReportCommandContext(
                self.trades_manager.reporter, figure=plot
            ),
        ).occur()
        return position

    async def task(self):
        chartdata = self.get_chartdata()
        last_timestamp = chartdata.timestamps[-1]
        chartdata = chartdata.subdata(end_index=-2)
        signal = self.check_signal(chartdata)
        if signal:
            if self.consider_position:
                position = self.trades_manager.generate_position(signal)
                if position:
                    figure = self.generate_figure(chartdata, signal, position)
                    self.trade(position, figure)
            else:
                figure = self.generate_figure(chartdata, signal)
                NewSignal(
                    signal,
                    report_context=ReportCommandContext(
                        self.trades_manager.reporter, figure
                    ),
                    record_context=self.give_record_context(),
                ).occur()

        return self.give_delay(last_timestamp)
