from ChartModule.models import Chart, ChartData
from ChartModule.plot import SingleChartFigure, SignalPlotter, Figure
from ChartModule.Indicators.auto_trendline import AutoTrendlines
from Bots.ChochStrategy.choch import ChochQueueFilter, ChochSignal
from Bots.CompositeStrategies.models import MTRSignal
from Bots.DivergenceStrategy.divergence import DivergenceSignal
from Bots.DivergenceStrategy.oscillator_divergence import (
    OscillatorDiverBot,
    OscillatorDivergence,
)
from Bots.DivergenceStrategy.oscillator_double_divergence import (
    OscillatorDoubleDiverBot,
    OscillatorDoubleDiverSignal,
)
from TraderBot.models import ExchangeAgent, Position
from TraderBot.PositionHandlers.manager import TradesManager
from TraderBot.PositionHandlers.plot import PositionPlotter
from TraderBot.trader_bot import TraderBot
import TraderBot.Commands as commands
from typing import cast
import logging


logger = logging.getLogger("OscillatorDiverChoch")

DiverSignal = DivergenceSignal | OscillatorDoubleDiverSignal


class OscillatorDiverChochBot(TraderBot):
    """
    Two-chart composite bot.

    `oscillator_chart` (usually the higher timeframe) is where the
    divergence is found. `chart` (the lower timeframe) is where the entry
    is found, via ChochQueueFilter.

    A trade needs BOTH: a divergence has to fire on the oscillator chart,
    and then a CHoCH -- never a BOS -- has to fire on the entry chart in
    the SAME direction within `n_candle_confirmation` bars. The divergence
    is reported on its own as soon as it happens, and the eventual entry
    report is threaded as a reply to it.

    The divergence leg is delegated to a real OscillatorDiverBot (or to an
    OscillatorDoubleDiverBot when `double_diver` is set) rather than
    re-implemented, so the search and the two-pane figure stay identical
    to the standalone divergence bots. That delegate only ever produces a
    signal and a figure -- this bot owns all chart fetching and reporting.
    """

    strategy: OscillatorDivergence  # type: ignore[assignment]

    def __init__(
        self,
        chart: Chart,
        oscillator_chart: Chart,
        agent: ExchangeAgent,
        strategy: OscillatorDivergence,
        choch_strategy: ChochQueueFilter,
        trades_manager: TradesManager,
        mtr_indicator: AutoTrendlines | None = None,
        n_candle_confirmation: int = 100,
        double_diver: bool = False,
        bar_between_signals: int = 2,
        n_candle_check: int = 200,
        n_oscillator_candle_check: int | None = None,
        consider_position: bool = True,
    ):
        super().__init__(
            chart,
            agent,
            strategy,
            trades_manager,
            bar_between_signals,
            n_candle_check,
            consider_position,
        )
        self.oscillator_chart = oscillator_chart
        self.choch_strategy = choch_strategy
        self.mtr_indicator = mtr_indicator
        self.n_candle_confirmation = n_candle_confirmation
        self.double_diver = double_diver
        self.n_oscillator_candle_check = n_oscillator_candle_check or n_candle_check

        diver_bot_class = (
            OscillatorDoubleDiverBot if double_diver else OscillatorDiverBot
        )
        self.diver_bot = diver_bot_class(
            oscillator_chart,
            agent,
            strategy,
            trades_manager,
            bar_between_signals,
            self.n_oscillator_candle_check,
            consider_position=False,
        )

        self.last_diver_signal: DiverSignal | None = None
        self.last_diver_report_id: int | None = None
        self._diver_report_command: commands.NewSignalReport | None = None
        self.last_diver_checked_timestamp: int | None = None
        self.last_mtr_checked_timestamp: int | None = None
        self.last_mtr_signal: MTRSignal | None = None

    def post_init(self):
        if not self.agent.prepare_chart(self.oscillator_chart):
            raise ValueError(
                f"Failed to prepare chart for {self.identifier} on oscillator chart"
            )
        if not self.agent.prepare_chart(self.chart):
            raise ValueError(f"Failed to prepare chart for {self.identifier}")
        logger.info(f"{self.identifier} Bot initialized")

    @property
    def identifier(self):
        return (
            f"{self.chart}_{self.oscillator_chart}"
            f"_{self.strategy.name}_{self.choch_strategy.name}"
        )

    def export_config(self) -> dict:
        conf_dict = super().export_config()
        conf_dict.update(
            {
                "oscillator_chart": self.oscillator_chart.export_config(),
                "choch_strategy": self.choch_strategy.export_config(),
                "mtr_indicator": (
                    self.mtr_indicator.export_configs() if self.mtr_indicator else None
                ),
                "n_candle_confirmation": self.n_candle_confirmation,
                "double_diver": self.double_diver,
                "n_oscillator_candle_check": self.n_oscillator_candle_check,
            }
        )
        return conf_dict

    def give_allowed_time(self) -> int:
        """Seconds a divergence stays valid while waiting for its CHoCH."""
        return self.n_candle_confirmation * self.chart.timeframe.minutes * 60

    @property
    def _reporter(self):
        reporter = self.trades_manager.reporter
        return reporter if reporter and reporter.enable else None

    def _sync_diver_bot(self) -> None:
        """
        The delegate is handed the same objects at construction, but `agent`
        gets swapped out from under a bot after the fact (BackTest does it),
        so mirror the mutable wiring before every use. `trades_manager` is
        the same instance, so its flags and reporter follow on their own.
        """
        self.diver_bot.agent = self.agent
        self.diver_bot.chart = self.oscillator_chart
        self.diver_bot.n_candle_check = self.n_oscillator_candle_check

    # --- DIVERGENCE (arms the setup) -----------------

    def check_diver_signal(self, oscillator_chartdata: ChartData) -> DiverSignal | None:
        # OscillatorDiverBot inherits TraderBot's wider `Signal | None`, but
        # its strategy only ever returns a DivergenceSignal
        return cast(
            DiverSignal | None, self.diver_bot.check_signal(oscillator_chartdata)
        )

    def _check_divergence(self, oscillator_chartdata: ChartData) -> None:
        last_candle = oscillator_chartdata[-1]
        if self.last_diver_checked_timestamp == last_candle.timestamp:
            return None
        self.last_diver_checked_timestamp = last_candle.timestamp

        signal = self.check_diver_signal(oscillator_chartdata)
        if signal is None:
            return None

        self.last_diver_signal = signal
        self.last_diver_report_id = None
        self._diver_report_command = None
        logger.info(f"OscillatorDiver Signal:{signal}")

        if self._reporter is None:
            return None
        figure = self.diver_bot.generate_figure(oscillator_chartdata, signal)  # type: ignore
        command = commands.NewSignalReport(signal, plot=figure)

        command.send(reporter=self.trades_manager.reporter)
        self._diver_report_command = command

    def _diver_still_valid(self, choch_chartdata: ChartData) -> bool:
        if self.last_diver_signal is None:
            return False
        elapsed = (
            choch_chartdata[-1].timestamp
            - self.last_diver_signal.main_chart_line.end_timestamp
        )
        allowed = self.give_allowed_time()
        if elapsed > allowed:
            logger.warning(f"divergence was too old {elapsed=} > {allowed}")
            self._clear_diver()
            return False
        return True

    def _diver_reply_id(self) -> int | None:
        # send() only queues the report -- the id exists once it has run
        if self.last_diver_report_id is not None:
            return self.last_diver_report_id
        return getattr(self._diver_report_command, "msg_id", None)

    def _clear_diver(self) -> None:
        self.last_diver_signal = None
        self.last_diver_report_id = None
        self._diver_report_command = None

    # --- MTR (informational only) --------------------

    def generate_mtr_figure(self, chartdata: ChartData, signal: MTRSignal) -> Figure:
        assert self.mtr_indicator is not None
        figure = SingleChartFigure(chartdata, self.n_candle_check)
        self.mtr_indicator.plotter(
            figure.main_pane,
            self.mtr_indicator.data,
            mtr_events=self.mtr_indicator.mtr_events,
            atr=self.mtr_indicator.atr.data,
            keep_archived=self.mtr_indicator.keep_archived,
        )
        SignalPlotter()(figure.main_pane, signal)
        return figure

    def _check_mtr(self, choch_chartdata: ChartData) -> None:
        if self.mtr_indicator is None:
            return None
        last_candle = choch_chartdata[-1]
        if self.last_mtr_checked_timestamp == last_candle.timestamp:
            return None

        self.mtr_indicator.set(choch_chartdata)
        self.last_mtr_checked_timestamp = last_candle.timestamp

        events = self.mtr_indicator.mtr_events
        if not events or events[-1].candle.timestamp != last_candle.timestamp:
            return None

        event = events[-1]
        self.last_mtr_signal = MTRSignal(
            choch_chartdata.chart, last_candle, event.side, "MTR", event
        )
        logger.info(f"MTR Signal: {self.last_mtr_signal}")

        if self._reporter is None:
            return None
        commands.NewSignalReport(
            self.last_mtr_signal,
            plot=self.generate_mtr_figure(choch_chartdata, self.last_mtr_signal),
        ).send(reporter=self.trades_manager.reporter)

    # --- ENTRY ---------------------------------------

    def check_signal(  # type: ignore[override]
        self, chartdata: ChartData, *args, **kwargs
    ) -> ChochSignal | None:
        """Only a real CHoCH counts as an entry here -- a BOS never does."""
        signal = self.choch_strategy.check_signal(
            chartdata,
            self.trades_manager.long_trade,
            self.trades_manager.short_trade,
        )
        if signal is None or not signal.choch_model.is_choch:
            return None
        return signal

    def generate_figure(  # type: ignore[override]
        self,
        chartdata: ChartData,
        signal: ChochSignal,
        position: Position | None = None,
        *args,
        **kwargs,
    ) -> Figure|None:
        if not self.consider_figure:
            return None
        figure = SingleChartFigure(chartdata, self.n_candle_check)
        self.choch_strategy.plotter(
            figure.main_pane,
            signal,
            self.choch_strategy.indicators,
            use_fibo_filter=self.choch_strategy.use_fibo_filter,
        )
        if position:
            PositionPlotter()(figure.main_pane, position)
        return figure

    def trade(self, position: Position, plot: Figure|None) -> Position | None:
        """
        TraderBot.trade, with the position report threaded as a reply to the
        divergence message that armed this trade.
        """
        report_command = None
        if self._reporter is not None:
            report_command = commands.NewPositionReport(
                plot=plot, reply_id=self._diver_reply_id()
            )
        commands.OpenPosition(report_command).send(
            self.trades_manager.give_command_contex(position)
        )
        return position

    def find_signal(
        self, oscillator_chartdata: ChartData, choch_chartdata: ChartData
    ) -> ChochSignal | None:
        # the divergence is what arms the setup
        self._check_divergence(oscillator_chartdata)
        if not self._diver_still_valid(choch_chartdata):
            return None
        assert self.last_diver_signal is not None

        # informational only -- never gates the entry
        self._check_mtr(choch_chartdata)

        choch_signal = self.check_signal(choch_chartdata)
        if choch_signal is None:
            return None

        if choch_signal.side is not self.last_diver_signal.side:
            logger.debug(
                f"different side for divergence & choch: "
                f"{self.last_diver_signal.side} | {choch_signal.side}"
            )
            return None

        if self.consider_position:
            position = self.trades_manager.generate_position(
                choch_signal, sl_base_price=choch_signal.choch_model.anchor
            )
            if position is None:
                logger.warning("Position is None")
                return None
            self.trade(
                position,
                self.generate_figure(choch_chartdata, choch_signal, position),
            )
            logger.info("Divergence & CHoCH Signal")
        else:
            commands.NewSignalReport(
                choch_signal,
                plot=self.generate_figure(choch_chartdata, choch_signal),
            ).send(reporter=self.trades_manager.reporter)

        # the setup has been consumed -- a new divergence must arm the next
        self._clear_diver()
        return choch_signal

    async def task(self):
        self._sync_diver_bot()
        oscillator_chartdata = self.get_chartdata(
            n_bar=self.n_oscillator_candle_check, chart=self.oscillator_chart
        ).subdata(end_index=-2)

        choch_chartdata = self.get_chartdata()
        last_timestamp = choch_chartdata.timestamps[-1]
        choch_chartdata = choch_chartdata.subdata(end_index=-2)

        self.find_signal(oscillator_chartdata, choch_chartdata)
        return self.give_delay(last_timestamp)
