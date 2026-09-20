from ChartModule.models import Chart, ChartData
from ChartModule.plot import (
    SingleChartFigure,
    ChartWithOscillatorFigure,
    SignalPlotter,
    Figure,
)
from ChartModule.Indicators.auto_trendline import AutoTrendlines, AutoTrendlinesPlotter
from Bots.ChochStrategy.choch import ChochQueueFilter, ChochSignal
from Bots.CompositeStrategies.models import MTRSignal
from Bots.DivergenceStrategy.divergence import DivergenceSignal
from Bots.DivergenceStrategy.oscillator_divergence import OscillatorDivergence
from TraderBot.models import ExchangeAgent, Position
from TraderBot.PositionHandlers.manager import TradesManager
from TraderBot.PositionHandlers.plot import PositionPlotter
from TraderBot.trader_bot import TraderBot
import TraderBot.Commands as commands
import logging


logger = logging.getLogger("OscillatorDiverChoch")


class OscillatorDiverChochBot(TraderBot):
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
        same_line_source: bool = True,
        double_diver: bool = False,
        bar_between_signals: int = 2,
        n_candle_check: int = 200,
        n_oscillator_candle_check: int | None = None,
        consider_position: bool = True,
    ):
        if double_diver:
            raise NotImplementedError(
                "double_diver is not supported yet: "
                "oscillator_double_divergence.py still targets the old "
                "Line/Signal API and cannot be imported"
            )

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
        self.same_line_source = same_line_source
        self.double_diver = double_diver
        self.n_oscillator_candle_check = n_oscillator_candle_check or n_candle_check

        self.last_diver_signal: DivergenceSignal | None = None
        self.last_diver_report_id: int | None = None
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
                "same_line_source": self.same_line_source,
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

    async def _report(self, signal, figure: Figure) -> int | None:
        reporter = self._reporter
        if reporter is None:
            return None
        result = await reporter.send_msg(
            reporter.msg_formater.new_signal(signal),
            img_path=figure.save_image(),
        )
        return getattr(result, "message_id", None)

    async def _check_divergence(self, chartdata: ChartData) -> None:
        last_candle = chartdata[-1]
        if self.last_diver_checked_timestamp == last_candle.timestamp:
            return None
        self.last_diver_checked_timestamp = last_candle.timestamp

        signal = self.strategy.check_signal(
            chartdata,
            self.trades_manager.long_trade,
            self.trades_manager.short_trade,
        )
        if signal is None:
            return None

        self.last_diver_signal = signal
        self.last_diver_report_id = None
        logger.info(f"OscillatorDiver Signal:{signal}")

        if self._reporter is None:
            return None
        figure = ChartWithOscillatorFigure(
            chartdata,
            self.strategy.oscillator_indicator.data,
            self.n_oscillator_candle_check,
        )
        self.strategy.plotter(
            figure.main_pane,
            figure.oscillator_pane,
            signal,
            self.strategy.indicators,
        )
        self.last_diver_report_id = await self._report(signal, figure)

    async def _check_mtr(self, chartdata: ChartData) -> None:
        if self.mtr_indicator is None:
            return None
        last_candle = chartdata[-1]
        if self.last_mtr_checked_timestamp == last_candle.timestamp:
            return None

        self.mtr_indicator.set(chartdata)
        self.last_mtr_checked_timestamp = last_candle.timestamp

        events = self.mtr_indicator.mtr_events
        if not events or events[-1].candle.timestamp != last_candle.timestamp:
            return None

        event = events[-1]
        self.last_mtr_signal = MTRSignal(
            chartdata.chart, last_candle, event.side, "MTR", event
        )
        logger.info(f"MTR Signal: {self.last_mtr_signal}")

        if self._reporter is None:
            return None
        figure = SingleChartFigure(chartdata, self.n_candle_check)
        AutoTrendlinesPlotter()(
            figure.main_pane,
            self.mtr_indicator.data,
            mtr_events=events,
            atr=self.mtr_indicator.atr.data,
            keep_archived=self.mtr_indicator.keep_archived,
        )
        SignalPlotter()(figure.main_pane, self.last_mtr_signal)
        await self._report(self.last_mtr_signal, figure)

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

    def _diver_still_valid(self, choch_chartdata: ChartData) -> bool:
        if self.last_diver_signal is None:
            return False
        # measured from the END of the divergence line -- the bar the
        # divergence actually completed on
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

    def _clear_diver(self) -> None:
        self.last_diver_signal = None
        self.last_diver_report_id = None

    def trade(  # type: ignore[override]
        self, signal: ChochSignal, position: Position, plot: Figure
    ) -> Position | None:
        report_command = None
        reporter = self._reporter
        if reporter is not None:
            PositionPlotter()(plot.main_pane, position)
            self.choch_strategy.plotter(
                plot.main_pane,
                signal,
                self.choch_strategy.indicators,
                use_fibo_filter=self.choch_strategy.use_fibo_filter,
            )
            report_command = commands.NewPositionReport(
                plot=plot, reply_id=self.last_diver_report_id
            )
        commands.OpenPosition(report_command).send(
            self.trades_manager.give_command_contex(position)
        )
        return position

    async def find_signal(
        self, oscillator_chartdata: ChartData, choch_chartdata: ChartData
    ) -> ChochSignal | None:
        # the divergence is what arms the setup
        await self._check_divergence(oscillator_chartdata)
        if not self._diver_still_valid(choch_chartdata):
            return None
        assert self.last_diver_signal is not None

        # informational only -- never gates the entry
        await self._check_mtr(choch_chartdata)

        choch_signal = self.check_signal(choch_chartdata)
        if choch_signal is None:
            return None

        if choch_signal.side is not self.last_diver_signal.side:
            logger.warning(
                f"different side for divergence & choch: "
                f"{self.last_diver_signal.side} | {choch_signal.side}"
            )
            return None

        figure = SingleChartFigure(choch_chartdata, self.n_candle_check)
        if self.consider_position:
            position = self.trades_manager.generate_position(
                choch_signal, sl_base_price=choch_signal.choch_model.anchor
            )
            if position is None:
                logger.warning("Position is None")
                return None
            self.trade(choch_signal, position, figure)
            logger.info("Divergence & CHoCH Signal")
            # the setup has been consumed -- a new divergence must arm the next
            self._clear_diver()
            return choch_signal

        self.choch_strategy.plotter(
            figure.main_pane,
            choch_signal,
            self.choch_strategy.indicators,
            use_fibo_filter=self.choch_strategy.use_fibo_filter,
        )
        commands.NewSignalReport(choch_signal, plot=figure).send(
            reporter=self.trades_manager.reporter
        )
        self._clear_diver()
        return choch_signal

    async def task(self):
        oscillator_chartdata = self.get_chartdata(
            n_bar=self.n_oscillator_candle_check, chart=self.oscillator_chart
        ).subdata(end_index=-2)

        choch_chartdata = self.get_chartdata()
        last_timestamp = choch_chartdata.timestamps[-1]
        choch_chartdata = choch_chartdata.subdata(end_index=-2)

        await self.find_signal(oscillator_chartdata, choch_chartdata)
        return self.give_delay(last_timestamp)
