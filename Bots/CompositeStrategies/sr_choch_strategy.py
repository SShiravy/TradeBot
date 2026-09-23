from ChartModule.models import Chart, ChartData, MarketSide
from ChartModule.plot import SingleChartFigure, SignalPlotter, Figure
from ChartModule.Indicators.auto_trendline import AutoTrendlines, TrendlineModel
from ChartModule.Indicators.sr_zone import SRZones, ZoneModel
from Bots.ChochStrategy.choch import ChochQueueFilter, ChochSignal
from Bots.CompositeStrategies.models import DynamicSRSignal, StaticSRSignal
from TraderBot.models import ExchangeAgent, Position
from TraderBot.PositionHandlers.manager import TradesManager
from TraderBot.PositionHandlers.plot import PositionPlotter
from TraderBot.trader_bot import TraderBot
from TraderBot.Commands.report_commands import ReportCommandContext, ReportNewSignal
from TraderBot.Commands.trade_commands import TradeCommandContext
from TraderBot.events import NewPosition, NewSignal
import logging


logger = logging.getLogger("SR_Choch")

SRSignal = StaticSRSignal | DynamicSRSignal


class SRChochBot(TraderBot):
    """
    Two-chart composite bot.

    `sr_chart` (the higher timeframe) is where support/resistance is found,
    both static (SRZones) and dynamic (AutoTrendlines). `chart` (the lower
    timeframe) is where the entry is found, via ChochQueueFilter.

    A trade needs BOTH: price has to touch an S&R level, and then a CHoCH
    -- never a BOS -- has to fire on the entry chart in the SAME direction
    within `n_candle_confirmation` bars. The S&R touch is reported on its
    own as soon as it happens, and the eventual entry report is threaded as
    a reply to it.
    """

    strategy: ChochQueueFilter  # type: ignore[assignment]

    def __init__(
        self,
        chart: Chart,
        sr_chart: Chart,
        agent: ExchangeAgent,
        strategy: ChochQueueFilter,
        trades_manager: TradesManager,
        static_sr_indicator: SRZones,
        dynamic_sr_indicator: AutoTrendlines,
        n_candle_confirmation: int = 100,
        bar_between_signals: int = 2,
        n_candle_check: int = 1000,
        n_sr_candle_check: int | None = None,
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
        self.sr_chart = sr_chart
        self.static_sr_indicator = static_sr_indicator
        self.dynamic_sr_indicator = dynamic_sr_indicator
        self.n_candle_confirmation = n_candle_confirmation
        self.n_sr_candle_check = n_sr_candle_check or n_candle_check

        self.last_sr_signal: SRSignal | None = None
        self._sr_report_command: ReportNewSignal | None = None
        self.last_static_sr_checked_timestamp: int | None = None
        self.last_dynamic_sr_checked_timestamp: int | None = None

    def post_init(self):
        if not self.agent.prepare_chart(self.sr_chart):
            raise ValueError(
                f"Failed to prepare chart for {self.identifier} on sr chart"
            )
        if not self.agent.prepare_chart(self.chart):
            raise ValueError(f"Failed to prepare chart for {self.identifier}")
        logger.info(f"{self.identifier} Bot initialized")

    @property
    def identifier(self):
        return f"{self.chart}_{self.sr_chart}_{self.strategy.name}"

    def export_config(self) -> dict:
        conf_dict = super().export_config()
        conf_dict.update(
            {
                "sr_chart": self.sr_chart.export_config(),
                "static_sr_indicator": self.static_sr_indicator.export_configs(),
                "dynamic_sr_indicator": self.dynamic_sr_indicator.export_configs(),
                "n_candle_confirmation": self.n_candle_confirmation,
                "n_sr_candle_check": self.n_sr_candle_check,
            }
        )
        return conf_dict

    def give_allowed_time(self) -> int:
        """Seconds an S&R touch stays valid while waiting for its CHoCH."""
        return self.n_candle_confirmation * self.chart.timeframe.minutes * 60

    # --- S&R (arms the setup) ------------------------

    def generate_static_sr_figure(
        self, chartdata: ChartData, signal: StaticSRSignal
    ) -> Figure:
        figure = SingleChartFigure(chartdata, self.n_sr_candle_check)
        self.static_sr_indicator.plotter(
            figure.main_pane,
            self.static_sr_indicator.data,
            median_atr=self.static_sr_indicator.last_median_atr,
            live_pivots=self.static_sr_indicator.pivots.live_pivots,
            max_zones_display=None,
        )
        SignalPlotter()(figure.main_pane, signal)
        return figure

    def generate_dynamic_sr_figure(
        self, chartdata: ChartData, signal: DynamicSRSignal
    ) -> Figure:
        figure = SingleChartFigure(chartdata, self.n_sr_candle_check)
        self.dynamic_sr_indicator.plotter(
            figure.main_pane,
            self.dynamic_sr_indicator.data,
            mtr_events=self.dynamic_sr_indicator.mtr_events,
            atr=self.dynamic_sr_indicator.atr.data,
            keep_archived=self.dynamic_sr_indicator.keep_archived,
        )
        SignalPlotter()(figure.main_pane, signal)
        return figure

    def _arm_sr(self, signal: SRSignal) -> None:
        """Record the touch that arms the setup. Reporting is the caller's."""
        self.last_sr_signal = signal
        self._sr_report_command = None
        logger.info(f"S&R Signal:{signal}")

    def _report_sr(self, signal: SRSignal, figure: Figure) -> None:
        # everything that follows replies to this message, and the id only
        # exists on the command itself, so it is built here and handed to
        # the event to be sent instead of being made inside it
        command = ReportNewSignal(
            signal,
            ReportCommandContext(
                self.trades_manager.reporter, figure, reply_id=self._sr_reply_id()
            ),
        )
        NewSignal(signal, extra_commands=[command]).occur()
        self._sr_report_command = command

    def _check_static_sr(self, chartdata: ChartData) -> None:
        last_candle = chartdata[-1]
        if self.last_static_sr_checked_timestamp == last_candle.timestamp:
            return None

        self.static_sr_indicator.set(chartdata)
        if not self.static_sr_indicator.data:
            return None

        self.last_static_sr_checked_timestamp = last_candle.timestamp

        candidates: list[ZoneModel] = []
        for zone in self.static_sr_indicator.data:
            if zone.broken:
                continue
            touched = last_candle.low <= zone.upper and zone.lower <= last_candle.high
            if touched:
                candidates.append(zone)

        if not candidates:
            return None

        best_zone = max(candidates, key=lambda z: z.score_pct)
        if (
            isinstance(self.last_sr_signal, StaticSRSignal)
            and self.last_sr_signal.zone == best_zone
            and (
                self.last_sr_signal.candle.timestamp - last_candle.timestamp
                < self.give_allowed_time()
            )
        ):
            return None

        side = MarketSide.BULLISH if best_zone.is_support else MarketSide.BEARISH
        body_low = min(last_candle.body_top, last_candle.body_bottom)
        body_high = max(last_candle.body_top, last_candle.body_bottom)
        touch_type = (
            "Body"
            if (body_low <= best_zone.upper and best_zone.lower <= body_high)
            else "Shadow"
        )

        signal = StaticSRSignal(
            self.sr_chart,
            last_candle,
            side,
            "Static Support" if best_zone.is_support else "Static Resistance",
            zone=best_zone,
            touch_type=touch_type,
        )

        self._arm_sr(signal)

        self._report_sr(signal, self.generate_static_sr_figure(chartdata, signal))

    def _check_dynamic_sr(self, chartdata: ChartData) -> None:
        last_candle = chartdata[-1]
        if self.last_dynamic_sr_checked_timestamp == last_candle.timestamp:
            return None

        self.dynamic_sr_indicator.set(chartdata)
        if not self.dynamic_sr_indicator.data:
            return None

        self.last_dynamic_sr_checked_timestamp = last_candle.timestamp

        candidates: list[TrendlineModel] = []
        for trendline in self.dynamic_sr_indicator.data:
            if trendline.broken:
                continue
            if trendline.last_touch_candle.timestamp == last_candle.timestamp:
                candidates.append(trendline)

        if not candidates:
            return None

        best_dynamic_sr = max(candidates, key=lambda d: d.score)
        if (
            isinstance(self.last_sr_signal, DynamicSRSignal)
            and self.last_sr_signal.dynamic_sr == best_dynamic_sr
            and (
                self.last_sr_signal.candle.timestamp - last_candle.timestamp
                < self.give_allowed_time()
            )
        ):
            return None

        signal = DynamicSRSignal(
            self.sr_chart,
            last_candle,
            best_dynamic_sr.side,
            "Dynamic Support" if best_dynamic_sr.is_support else "Dynamic Resistance",
            dynamic_sr=best_dynamic_sr,
        )

        self._arm_sr(signal)

        self._report_sr(signal, self.generate_dynamic_sr_figure(chartdata, signal))

    def _sr_still_valid(self, choch_chartdata: ChartData) -> bool:
        if self.last_sr_signal is None:
            return False
        elapsed = choch_chartdata[-1].timestamp - self.last_sr_signal.candle.timestamp
        allowed = self.give_allowed_time()
        if elapsed > allowed:
            logger.info(f"S&R was too old {elapsed=} > {allowed}")
            self._clear_sr()
            return False
        return True

    def _sr_reply_id(self) -> int | None:
        return getattr(self._sr_report_command, "msg_id", None)

    def _clear_sr(self) -> None:
        self.last_sr_signal = None
        self._sr_report_command = None

    # --- ENTRY ---------------------------------------

    def check_signal(  # type: ignore[override]
        self, chartdata: ChartData, *args, **kwargs
    ) -> ChochSignal | None:
        """Only a real CHoCH counts as an entry here -- a BOS never does."""
        signal = self.strategy.check_signal(
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
    ) -> Figure | None:
        if not self.consider_figure:
            return None
        figure = SingleChartFigure(chartdata, self.n_candle_check)
        self.strategy.plotter(
            figure.main_pane,
            signal,
            self.strategy.indicators,
            use_fibo_filter=self.strategy.use_fibo_filter,
        )
        if position:
            PositionPlotter()(figure.main_pane, position)
        return figure

    def trade(self, position: Position, plot: Figure | None) -> Position | None:
        """
        TraderBot.trade, with the position report threaded as a reply to the
        S&R message that armed this trade.
        """
        NewPosition(
            trade_context=TradeCommandContext(position, self.agent),
            report_context=ReportCommandContext(
                self.trades_manager.reporter, figure=plot, reply_id=self._sr_reply_id()
            ),
        ).occur()
        return position

    def find_signal(
        self, sr_chartdata: ChartData, choch_chartdata: ChartData
    ) -> ChochSignal | None:
        # S&R first -- it is what arms the setup
        self._check_static_sr(sr_chartdata)
        self._check_dynamic_sr(sr_chartdata)
        if not self._sr_still_valid(choch_chartdata):
            return None
        assert self.last_sr_signal is not None

        choch_signal = self.check_signal(choch_chartdata)
        if choch_signal is None:
            return None

        if choch_signal.side is not self.last_sr_signal.side:
            logger.info(
                f"different side for SR & choch: "
                f"{self.last_sr_signal.side} | {choch_signal.side}"
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
            logger.info("SR & CHoCH Signal")
        else:
            NewSignal(
                choch_signal,
                report_context=ReportCommandContext(
                    self.trades_manager.reporter,
                    self.generate_figure(choch_chartdata, choch_signal),
                    reply_id=self._sr_reply_id(),
                ),
            ).occur()

        # the setup has been consumed -- a new S&R touch must arm the next
        self._clear_sr()
        return choch_signal

    async def task(self):
        sr_chartdata = self.get_chartdata(
            n_bar=self.n_sr_candle_check, chart=self.sr_chart
        ).subdata(end_index=-2)

        choch_chartdata = self.get_chartdata()
        last_timestamp = choch_chartdata.timestamps[-1]
        choch_chartdata = choch_chartdata.subdata(end_index=-2)

        self.find_signal(sr_chartdata, choch_chartdata)
        return self.give_delay(last_timestamp)
