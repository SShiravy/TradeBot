from ChartModule.models import (
    Chart,
    Signal,
    ChartData,
    MarketSide,
    Candle,
    CandlesSource,
)
from ChartModule.Indicators import Indicator, SupportCandlesPattern
from ChartModule.Indicators.swing_pivots import SwingPivots, PivotPoint
from ChartModule.Indicators.moving_avg import EMA
from ChartModule.Indicators.atr import ATR
from ChartModule.plot import ChartPane, DoubleChartFigure, SignalPlotter, Figure
from Bots.ChochStrategy.choch import ChochQueueFilter, ChochSignal, ChochPlotter
from TraderBot.models import ExchangeAgent, Position, Strategy, StrategyPlotter
from TraderBot.PositionHandlers.manager import TradesManager
from TraderBot.PositionHandlers.plot import PositionPlotter
from TraderBot.trader_bot import TraderBot
from TraderBot.Commands.report_commands import ReportCommandContext
from TraderBot.Commands.trade_commands import TradeCommandContext
from TraderBot.events import NewPosition, NewSignal
from dataclasses import dataclass
import pandas as pd
import numpy as np
import colorsys
import logging

logger = logging.getLogger("EmaPivotChoch")

TouchEvent = tuple[PivotPoint, tuple["EmaTouch", ...], Candle]


@dataclass(slots=True, frozen=True)
class EmaTouch:
    ema_period: int
    ema_value: float

    def __str__(self) -> str:
        return f"EMA{self.ema_period}@{self.ema_value:.5f}"


@dataclass(slots=True, frozen=True)
class EmaPivotChochSignal(Signal):
    pivot: PivotPoint
    touches: tuple[EmaTouch, ...]
    inner_signal: ChochSignal

    def __str__(self) -> str:
        touches_str = ",".join((str(t) for t in self.touches))
        return (
            f"EmaPivotChoch|{self.side}|{self.candle.timestamp}|pivot={self.pivot}"
            f"|touches=[{touches_str}]|inner={self.inner_signal.choch_model}"
        )


class EmaPivotChochPlotter(StrategyPlotter):
    """
    Two-pane plotter: the LTF pane carries the inner CHoCH model and the
    signal, the HTF pane carries the EMAs and the pivot that set the setup
    up. Mirrors DivergencePlotter's (pane, second_pane, signal, ...) shape.
    """

    BULLISH_COLOR = "#26a69a"
    BEARISH_COLOR = "#ef5350"
    TOUCH_COLOR = "#ffb300"

    def __init__(self) -> None:
        self.choch_plotter = ChochPlotter()

    @staticmethod
    def ema_colors(periods: list[int]) -> dict[int, str]:
        colors = {}
        for i, period in enumerate(periods):
            hue = i / len(periods)
            r, g, b = colorsys.hsv_to_rgb(hue, 0.65, 0.85)
            colors[period] = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
        return colors

    def draw_emas(self, pane: ChartPane, emas: dict[int, pd.Series]) -> None:
        """
        Every configured EMA on the HTF pane, with the color-to-EMA mapping
        in one legend row.

        The mapping deliberately does NOT go through `legend=` on each
        line: this pane already carries a candlestick datasource, and a
        second legend *item* on such a pane collapses its x-range, which
        squeezes every EMA into a few pixels. See ChartPane.add_legend.
        """
        if not emas:
            return
        colors = self.ema_colors(list(emas))
        for period, ema_values in emas.items():
            pane.linear_plot(
                ema_values.index.to_numpy(),
                ema_values.to_numpy(),
                color=colors[period],
            )
            if ema_values.notna().any():
                pane.extend_y_range(float(ema_values.min()), float(ema_values.max()))
        pane.add_legend(
            " ".join(
                f"<span style='color:{colors[period]}'>EMA{period}</span>"
                for period in emas
            ),
            font_size="7pt",
        )

    def __call__(
        self,
        pane: ChartPane,
        second_pane: ChartPane,
        signal: EmaPivotChochSignal,
        indicators: list[Indicator] = [],
        emas: dict[int, pd.Series] | None = None,
        *args,
        use_fibo_filter: bool = True,
        **kwargs,
    ):
        if emas:
            self.draw_emas(second_pane, emas)

        pivot_color = (
            self.BEARISH_COLOR
            if signal.side is MarketSide.BEARISH
            else self.BULLISH_COLOR
        )
        pivot_index = self.choch_plotter._candle_index(second_pane, signal.pivot.candle)
        if pivot_index is not None:
            pivot_source = (
                CandlesSource.High if signal.pivot.is_high else CandlesSource.Low
            )
            second_pane.mark_candle(pivot_index, source=pivot_source, color=pivot_color)

        self.choch_plotter.draw_model(
            pane, signal.inner_signal.choch_model, use_fibo_filter
        )
        SignalPlotter()(pane, signal.inner_signal)

        for indicator in indicators:
            if indicator.data is not None:
                indicator.plotter(pane, indicator.data)

    def draw_touches(
        self,
        pane: ChartPane,
        second_pane: ChartPane,
        touch_events: dict[tuple, TouchEvent],
        touch_keys: list[tuple] | None = None,
        color: str = TOUCH_COLOR,
    ) -> None:
        # touch_events accumulates forever and is never pruned, but the panes
        # are built from the current rolling window only - a touch recorded on
        # a candle that has since scrolled out of that window cannot be placed
        # on this chart, so skip it rather than drawing at the wrong x.
        #
        # touch_keys restricts drawing to a subset (e.g. only the touch(es)
        # just registered by the latest check_signal call) instead of the
        # whole accumulated history - pass None to draw everything.
        if pane.chartdata is None or second_pane.chartdata is None:
            return
        ltf_times = set(pane.chartdata.timestamps.tolist())
        htf_times = set(second_pane.chartdata.timestamps.tolist())

        events = (
            touch_events.values()
            if touch_keys is None
            else (touch_events[key] for key in touch_keys if key in touch_events)
        )

        ltf_points: list[tuple[int, float]] = []
        htf_bullish_points: list[tuple[int, float]] = []
        htf_bearish_points: list[tuple[int, float]] = []
        for pivot, _touches, ltf_touch_candle in events:
            if (
                ltf_touch_candle.timestamp not in ltf_times
                or pivot.candle.timestamp not in htf_times
            ):
                continue
            source = CandlesSource.High if pivot.is_high else CandlesSource.Low
            ltf_points.append((ltf_touch_candle.timestamp, source(ltf_touch_candle)))
            htf_point = (pivot.candle.timestamp, source(pivot.candle))
            (htf_bearish_points if pivot.is_high else htf_bullish_points).append(
                htf_point
            )

        pane.mark_points(ltf_points, color=color)
        second_pane.mark_points(htf_bullish_points, color=self.BULLISH_COLOR)
        second_pane.mark_points(htf_bearish_points, color=self.BEARISH_COLOR)

    def draw_all(
        self,
        pane: ChartPane,
        second_pane: ChartPane,
        signals: list[EmaPivotChochSignal],
        indicators: list[Indicator] = [],
        emas: dict[int, pd.Series] | None = None,
        use_fibo_filter: bool = True,
    ) -> None:
        if not signals:
            return
        if emas:
            self.draw_emas(second_pane, emas)

        retrace_points: dict[MarketSide, list[tuple[int, float]]] = {
            MarketSide.BULLISH: [],
            MarketSide.BEARISH: [],
        }
        for signal in signals:
            model = signal.inner_signal.choch_model
            self.choch_plotter.draw_model(pane, model, use_fibo_filter)
            if (
                use_fibo_filter
                and model.retrace_level is not None
                and model.touch_candle is not None
            ):
                retrace_points[model.side].append(
                    (model.touch_candle.timestamp, model.retrace_level)
                )

        for side, points in retrace_points.items():
            if not points:
                continue
            pane.mark_points(
                points, color="#1DBD1D" if side is MarketSide.BULLISH else "#BD1D1D"
            )

        signal_plotter = SignalPlotter()
        for signal in signals:
            signal_plotter(pane, signal.inner_signal)

        for indicator in indicators:
            if indicator.data is not None:
                indicator.plotter(pane, indicator.data)


class EmaPivotChochFilter(Strategy):
    def __init__(
        self,
        ema_periods: list[int],
        htf_pivot_length: int = 50,
        htf_backstep: int = 2,
        atr_period: int = 14,
        atr_multiplier: float = 1.0,
        max_bars_after_pivot: int = 100,
        choch_pivot_length: int = 12,
        choch_backstep: int = 2,
        retrace_fib: float = 0.5,
        use_fibo_filter: bool = True,
        use_bos: bool = True,
        use_choch: bool = True,
        min_choch_candles: int = 3,
        indicators: list[Indicator] = [],
        long_support_conditions=SupportCandlesPattern.RAW,
        short_support_conditions=SupportCandlesPattern.RAW,
        name="EmaPivotChoch",
    ) -> None:
        super().__init__(
            name,
            EmaPivotChochPlotter(),
            long_support_conditions,
            short_support_conditions,
            indicators,
        )
        if len(ema_periods) < 1:
            raise ValueError("ema_periods must contain at least 1 EMA length")
        self.ema_periods = ema_periods
        self.htf_pivot_length = htf_pivot_length
        self.htf_backstep = htf_backstep
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.max_bars_after_pivot = max_bars_after_pivot
        self.choch_pivot_length = choch_pivot_length
        self.choch_backstep = choch_backstep
        self.retrace_fib = retrace_fib
        self.use_fibo_filter = use_fibo_filter
        self.use_bos = use_bos
        self.use_choch = use_choch
        self.min_choch_candles = min_choch_candles
        self.ltf_chart: Chart
        self.htf_chart: Chart
        self.last_reported_timestamp: int | None = None
        self._pivots: list[PivotPoint] = []
        # keyed by timestamp, because the EMAs may be computed over a LONGER
        # htf window than the pivots/ATR, so their indices do not line up
        self._emas: dict[int, pd.Series] = {}
        # index-aligned with the htf chartdata, NaN until warmed up
        self._atr: np.ndarray = np.array([])
        self._htf_chartdata: ChartData | None = None
        self.debug_counters: dict[str, int] = {
            "pivots_in_window": 0,
            "touched_by_ema": 0,
            "ltf_window_ok": 0,
            "inner_choch_called": 0,
            "inner_choch_fresh_match": 0,
        }
        self.debug_last_call: dict = {}
        self._touch_events: dict[tuple, TouchEvent] = {}
        # touch_key(s) newly registered by the most recent check_signal() call
        # only - used so a touch-report send reflects that fresh touch alone,
        # not the whole accumulated history in _touch_events.
        self._new_touch_keys: list[tuple] = []
        # the very first check_signal() call registers every touch already
        # sitting in the fetched window as pre-existing, not "new" - without
        # this a freshly (re)started bot would immediately spam a touch
        # report for every old pivot touch still inside its LTF window.
        self._warming = True

    def export_config(self):
        conf_dict = super().export_config()
        conf_dict.update(
            {
                "ema_periods": self.ema_periods,
                "htf_pivot_length": self.htf_pivot_length,
                "htf_backstep": self.htf_backstep,
                "atr_period": self.atr_period,
                "atr_multiplier": self.atr_multiplier,
                "max_bars_after_pivot": self.max_bars_after_pivot,
                "choch_pivot_length": self.choch_pivot_length,
                "choch_backstep": self.choch_backstep,
                "retrace_fib": self.retrace_fib,
                "use_fibo_filter": self.use_fibo_filter,
                "use_bos": self.use_bos,
                "use_choch": self.use_choch,
                "min_choch_candles": self.min_choch_candles,
            }
        )
        return conf_dict

    @property
    def emas(self) -> dict[int, pd.Series]:
        """The EMA series from the last check_signal call -- what the plotter draws."""
        return self._emas

    def _make_inner_filter(self) -> ChochQueueFilter:
        return ChochQueueFilter(
            pivot_length=self.choch_pivot_length,
            backstep=self.choch_backstep,
            retrace_fib=self.retrace_fib,
            use_fibo_filter=self.use_fibo_filter,
            use_bos=self.use_bos,
            min_choch_candles=self.min_choch_candles,
            choch_mode=2,
            name=f"{self.name}_inner",
        )

    @staticmethod
    def _find_start_index(timestamps: np.ndarray, from_timestamp: int) -> int:
        """First index at or after `from_timestamp` (was a hand-rolled bisect)."""
        return int(np.searchsorted(timestamps, from_timestamp, side="left"))

    def _atr_at(self, index: int) -> float | None:
        if index < 0 or index >= len(self._atr):
            return None
        value = float(self._atr[index])
        return None if np.isnan(value) else value

    def _touching_emas(self, pivot: PivotPoint, pivot_index: int) -> list[EmaTouch]:
        atr_value = self._atr_at(pivot.index)
        max_distance = (
            (atr_value * self.atr_multiplier) if atr_value is not None else 0.0
        )
        if pivot.is_high:
            zone_low = pivot.candle.low
            zone_high = pivot.candle.high + max_distance
        else:
            zone_low = pivot.candle.low - max_distance
            zone_high = pivot.candle.high

        touches: list[EmaTouch] = []
        for period in self.ema_periods:
            ema_value = self._emas[period].get(pivot.candle.timestamp)
            if ema_value is None or pd.isna(ema_value):
                continue
            ema_value = float(ema_value)
            if zone_low <= ema_value <= zone_high:
                if self._ema_broken_before_pivot(pivot, pivot_index, period):
                    continue
                touches.append(EmaTouch(period, ema_value))
        return touches

    def _ema_broken_before_pivot(
        self, pivot: PivotPoint, pivot_index: int, period: int
    ) -> bool:
        """True if, between the previous pivot (either type) and this
        pivot's own candle, price already broke this EMA the "wrong" way
        on a same-colored candle - a close-based cross, confirmed by the
        candle's own direction, not just a wick poking through.

        For a low pivot (a BUY setup), that means a bearish candle closing
        below the EMA after the prior candle's close was still at/above
        it - i.e. the EMA was already broken down before this pivot, so
        this touch is a retest of a broken level, not a fresh bounce.
        The high-pivot (SELL) case is the mirror image.
        """
        if pivot_index == 0 or self._htf_chartdata is None:
            return False  # no earlier pivot to anchor the lookback on
        prev_pivot = self._pivots[pivot_index - 1]
        chartdata = self._htf_chartdata
        ema_values = self._emas[period]

        start = max(0, prev_pivot.index)
        stop = min(pivot.index, len(chartdata))
        prev_close: float | None = None
        prev_ema: float | None = None
        for i in range(start, stop):
            timestamp = int(chartdata.timestamps[i])
            ema_value = ema_values.get(timestamp)
            if ema_value is None or pd.isna(ema_value):
                continue
            ema_value = float(ema_value)
            close = float(chartdata.close[i])
            bullish = close > float(chartdata.open[i])
            if prev_close is not None and prev_ema is not None:
                if pivot.is_high:
                    if prev_close <= prev_ema and close > ema_value and bullish:
                        return True
                else:
                    if prev_close >= prev_ema and close < ema_value and not bullish:
                        return True
            prev_close, prev_ema = close, ema_value
        return False

    def check_signal(
        self,
        ltf_chartdata: ChartData,
        htf_chartdata: ChartData,
        check_long: bool = True,
        check_short: bool = True,
        ema_htf_chartdata: ChartData | None = None,
        *args,
        **kwargs,
    ) -> EmaPivotChochSignal | None:
        self.ltf_chart = ltf_chartdata.chart
        self.htf_chart = htf_chartdata.chart
        self._new_touch_keys = []

        pivot_detector = SwingPivots(
            depth=self.htf_pivot_length, backstep=self.htf_backstep
        )
        pivot_detector.set(htf_chartdata)
        # confirmed pivots PLUS the current still-forming (repainting) one(s)
        # - without this the newest swing point stays invisible for
        # `htf_pivot_length` bars after it actually happened, since it only
        # becomes "confirmed" that much later.
        self._pivots = [*pivot_detector.data, *pivot_detector.live_pivots]

        ema_source = (
            ema_htf_chartdata if ema_htf_chartdata is not None else htf_chartdata
        )
        self._emas = {}
        for period in self.ema_periods:
            self._emas[period] = EMA(period).set(ema_source)
        self._atr = ATR(self.atr_period).set(htf_chartdata)
        self._htf_chartdata = htf_chartdata

        ltf_timestamps = ltf_chartdata.timestamps
        last_ltf_candle = ltf_chartdata[-1]
        self.debug_last_call = {
            "ltf_candle_count": len(ltf_chartdata),
            "ltf_first_time": int(ltf_timestamps[0]),
            "ltf_last_time": last_ltf_candle.timestamp,
            "htf_candle_count": len(htf_chartdata),
            "htf_first_time": (
                int(htf_chartdata.timestamps[0]) if len(htf_chartdata) else None
            ),
            "htf_last_time": (
                int(htf_chartdata.timestamps[-1]) if len(htf_chartdata) else None
            ),
            "pivots_found": len(self._pivots),
            "pivots_time_range": (
                (self._pivots[0].candle.timestamp, self._pivots[-1].candle.timestamp)
                if self._pivots
                else None
            ),
        }

        best_signal: EmaPivotChochSignal | None = None
        for pivot_index in range(len(self._pivots) - 1, -1, -1):
            pivot = self._pivots[pivot_index]
            if last_ltf_candle.timestamp < pivot.candle.timestamp:
                continue
            required_side = MarketSide.BEARISH if pivot.is_high else MarketSide.BULLISH
            if required_side is MarketSide.BEARISH and (not check_short):
                continue
            if required_side is MarketSide.BULLISH and (not check_long):
                continue
            touches = self._touching_emas(pivot, pivot_index)
            if not touches:
                continue
            self.debug_counters["touched_by_ema"] += 1
            start_index = self._find_start_index(ltf_timestamps, pivot.candle.timestamp)
            # Only register (and later report) a touch whose pivot candle
            # actually falls inside the fetched LTF window - the HTF window
            # covers far more history than the LTF one, so an older pivot
            # would otherwise get pinned to index 0 by _find_start_index and
            # get reported as "new" even though it cannot be meaningfully
            # shown on the chart being sent.
            if start_index < len(ltf_chartdata) and pivot.candle.timestamp >= int(
                ltf_timestamps[0]
            ):
                touch_key = (pivot.candle.timestamp, pivot.is_high)
                if touch_key not in self._touch_events:
                    self._touch_events[touch_key] = (
                        pivot,
                        tuple(touches),
                        ltf_chartdata.candle(start_index),
                    )
                    self._new_touch_keys.append(touch_key)
            if not self.use_choch:
                continue
            if start_index >= len(ltf_chartdata):
                continue
            window_length = len(ltf_chartdata) - start_index
            if window_length > self.max_bars_after_pivot + 1:
                continue
            if window_length < 3:
                continue
            self.debug_counters["pivots_in_window"] += 1
            self.debug_counters["ltf_window_ok"] += 1
            window_chartdata = ltf_chartdata.subdata(start_index=start_index)
            self.debug_counters["inner_choch_called"] += 1
            inner_signal = self._make_inner_filter().check_signal(
                window_chartdata,
                check_long=required_side is MarketSide.BULLISH,
                check_short=required_side is MarketSide.BEARISH,
            )
            if (
                inner_signal is None
                or inner_signal.candle.timestamp != last_ltf_candle.timestamp
            ):
                continue
            if not self.use_bos and (not inner_signal.choch_model.is_choch):
                continue
            self.debug_counters["inner_choch_fresh_match"] += 1
            best_signal = EmaPivotChochSignal(
                self.ltf_chart,
                inner_signal.candle,
                required_side,
                self.name,
                pivot,
                tuple(touches),
                inner_signal,
            )
            break

        if self._warming:
            # touches that already existed before this bot (re)started are
            # registered silently, not reported as new
            self._warming = False
            self._new_touch_keys = []

        if best_signal is None:
            return None
        if (
            self.last_reported_timestamp is not None
            and best_signal.candle.timestamp <= self.last_reported_timestamp
        ):
            return None
        confirmations = self.get_indicators_confirmation(ltf_chartdata)
        if (
            best_signal.side is MarketSide.BULLISH
            and MarketSide.BEARISH in confirmations
        ):
            logger.debug(f"indicators rejected the signal: {best_signal}")
            return None
        if (
            best_signal.side is MarketSide.BEARISH
            and MarketSide.BULLISH in confirmations
        ):
            logger.debug(f"indicators rejected the signal: {best_signal}")
            return None
        self.last_reported_timestamp = best_signal.candle.timestamp
        logger.info(f"Signal: {best_signal}")
        return best_signal

    def describe_touches(self) -> list[dict]:
        htf_span = (
            self.htf_chart.timeframe.minutes * 60
            if hasattr(self, "htf_chart")
            else None
        )
        ltf_first_time = self.debug_last_call.get("ltf_first_time")
        out = []
        for pivot, _touches, ltf_touch_candle in self._touch_events.values():
            delta = ltf_touch_candle.timestamp - pivot.candle.timestamp
            out_of_range = (
                ltf_first_time is not None and pivot.candle.timestamp < ltf_first_time
            )
            out.append(
                {
                    "pivot_time": pivot.candle.timestamp,
                    "pivot_is_high": pivot.is_high,
                    "ltf_marker_time": ltf_touch_candle.timestamp,
                    "delta": delta,
                    "out_of_ltf_range": out_of_range,
                    "suspicious": not out_of_range
                    and htf_span is not None
                    and (delta >= htf_span),
                }
            )
        return sorted(out, key=lambda d: d["pivot_time"])


class EmaPivotChochBot(TraderBot):
    """
    Two-timeframe bot: pivots/EMAs come from the HTF chart, the CHoCH entry
    is found on the LTF chart. Same shape as DivergenceBot, which is the
    other two-chart bot in the codebase.

    n_ema_htf_candle_check lets the EMAs be computed over a LONGER HTF
    history than the pivots use, so a long EMA is already warmed up at the
    left edge of the pivot window instead of being NaN there. When it is
    None the EMAs just use the same HTF window as everything else.
    """

    strategy: EmaPivotChochFilter  # type: ignore[assignment]

    def __init__(
        self,
        chart: Chart,
        htf_chart: Chart,
        agent: ExchangeAgent,
        strategy: EmaPivotChochFilter,
        trades_manager: TradesManager,
        bar_between_signals: int = 2,
        n_candle_check: int = 1500,
        n_htf_candle_check: int = 500,
        n_ema_htf_candle_check: int | None = None,
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
        self.htf_chart = htf_chart
        self.n_htf_candle_check = n_htf_candle_check
        self.n_ema_htf_candle_check = n_ema_htf_candle_check

    def post_init(self):
        if not self.agent.prepare_chart(self.htf_chart):
            raise ValueError(
                f"Failed to prepare chart for {self.identifier} on htf chart"
            )
        if not self.agent.prepare_chart(self.chart):
            raise ValueError(f"Failed to prepare chart for {self.identifier}")
        logger.info(f"{self.identifier} Bot initialized")

    @property
    def identifier(self):
        return f"{self.chart}_{self.htf_chart}_{self.strategy.name}"

    def export_config(self) -> dict:
        conf_dict = super().export_config()
        conf_dict.update(
            {
                "htf_chart": self.htf_chart.export_config(),
                "n_htf_candle_check": self.n_htf_candle_check,
                "n_ema_htf_candle_check": self.n_ema_htf_candle_check,
            }
        )
        return conf_dict

    def get_ema_htf_chartdata(self) -> ChartData | None:
        if not self.n_ema_htf_candle_check:
            return None
        return self.get_chartdata(
            n_bar=self.n_ema_htf_candle_check, chart=self.htf_chart
        ).subdata(end_index=-2)

    # candles shown in the Telegram image (both panes) - independent of
    # n_candle_check/n_htf_candle_check, which control how much history is
    # FETCHED for the strategy to compute on
    PLOT_N_CANDLES = 150
    LEGEND_FONT_SIZE = "7pt"

    def _make_figure(
        self, ltf_chartdata: ChartData, htf_chartdata: ChartData
    ) -> DoubleChartFigure:
        return DoubleChartFigure(
            ltf_chartdata,
            htf_chartdata,
            self.PLOT_N_CANDLES,
            legend_font_size=self.LEGEND_FONT_SIZE,
        )

    def generate_figure(  # type: ignore[override]
        self,
        chartdata: ChartData,
        signal: EmaPivotChochSignal,
        position: Position | None = None,
        htf_chartdata: ChartData | None = None,
        *args,
        **kwargs,
    ) -> DoubleChartFigure | None:
        """
        The base builds a SingleChartFigure and calls the plotter as
        `plotter(main_pane, signal, indicators)`. This plotter is the
        two-pane `(pane, second_pane, signal, ...)` shape, so `signal`
        would bind to `second_pane` -- hence the override. `htf_chartdata`
        comes after `position` so the base's positional order still holds.
        """
        if not self.consider_figure:
            return None
        if htf_chartdata is None:
            raise ValueError("EmaPivotChochBot.generate_figure needs htf_chartdata")
        figure = self._make_figure(chartdata, htf_chartdata)
        self.strategy.plotter(
            figure.main_pane,
            figure.second_pane,
            signal,
            self.strategy.indicators,
            self.strategy.emas,
            use_fibo_filter=self.strategy.use_fibo_filter,
        )
        if position:
            PositionPlotter()(figure.main_pane, position)
        return figure

    def generate_touch_figure(
        self, ltf_chartdata: ChartData, htf_chartdata: ChartData
    ) -> DoubleChartFigure:
        figure = self._make_figure(ltf_chartdata, htf_chartdata)
        self.strategy.plotter.draw_emas(figure.second_pane, self.strategy.emas)
        self.strategy.plotter.draw_touches(
            figure.main_pane,
            figure.second_pane,
            self.strategy._touch_events,
            touch_keys=self.strategy._new_touch_keys,
        )
        return figure

    def _touch_report_name(self, ltf_chartdata: ChartData) -> str:
        """
        Named after the touch it is reporting, the way NewSignalReport
        names a signal image after its candle. A fixed name would have
        every touch overwrite the previous one in the same file.
        """
        keys = self.strategy._new_touch_keys
        if keys:
            _pivot, _touches, touch_candle = self.strategy._touch_events[keys[-1]]
            return str(touch_candle.timestamp)
        return str(ltf_chartdata[-1].timestamp)

    async def send_touch_report(
        self, ltf_chartdata: ChartData, htf_chartdata: ChartData
    ) -> None:
        """
        Not a Signal, so it cannot go through NewSignalReport -- this stays
        a direct send. The image still lands under the reporter's save_path
        the way every queued report does.
        """
        figure = self.generate_touch_figure(ltf_chartdata, htf_chartdata)
        image_path = figure.save_image(
            name=self._touch_report_name(ltf_chartdata),
            path=self.trades_manager.reporter.save_path or "Records/",
        )
        await reporter.send_msg(
            f"{self.strategy.name}\n📈 {self.chart}\nEMA-pivot touch report",
            img_path=image_path,
        )

    def trade(self, position: Position, plot: Figure | None) -> Position | None:
        NewPosition(
            trade_context=TradeCommandContext(position, self.agent),
            report_context=ReportCommandContext(
                self.trades_manager.reporter, figure=plot
            ),
        ).occur()
        return position

    def check_signal(  # type: ignore[override]
        self,
        chartdata: ChartData,
        htf_chartdata: ChartData,
        ema_htf_chartdata: ChartData | None = None,
        *args,
        **kwargs,
    ) -> EmaPivotChochSignal | None:
        return self.strategy.check_signal(
            chartdata,
            htf_chartdata,
            self.trades_manager.long_trade,
            self.trades_manager.short_trade,
            ema_htf_chartdata,
        )

    def find_signal(
        self,
        chartdata: ChartData,
        htf_chartdata: ChartData,
        ema_htf_chartdata: ChartData | None = None,
    ) -> EmaPivotChochSignal | None:
        signal = self.check_signal(chartdata, htf_chartdata, ema_htf_chartdata)
        if signal is None:
            return None

        if self.consider_position:
            position = self.trades_manager.generate_position(
                signal, sl_base_price=signal.inner_signal.choch_model.anchor
            )
            if position is None:
                logger.warning("Position is None")
                return None
            self.trade(
                position,
                self.generate_figure(chartdata, signal, position, htf_chartdata),
            )
            NewSignal(signal, record_context=self.give_record_context()).occur()
        else:
            NewSignal(
                signal,
                report_context=ReportCommandContext(
                    self.trades_manager.reporter,
                    self.generate_figure(chartdata, signal, None, htf_chartdata),
                ),
                record_context=self.give_record_context(),
            ).occur()
        return signal

    async def task(self):
        chartdata = self.get_chartdata()
        last_timestamp = chartdata.timestamps[-1]
        chartdata = chartdata.subdata(end_index=-2)
        htf_chartdata = self.get_chartdata(
            n_bar=self.n_htf_candle_check, chart=self.htf_chart
        ).subdata(end_index=-2)
        ema_htf_chartdata = self.get_ema_htf_chartdata()

        self.find_signal(chartdata, htf_chartdata, ema_htf_chartdata)

        # populated fresh by strategy.check_signal() above with only the
        # touch(es) registered THIS call
        if (
            self.strategy._new_touch_keys
            and not self.strategy.use_bos
            and not self.strategy.use_choch
        ):
            await self.send_touch_report(chartdata, htf_chartdata)

        return self.give_delay(last_timestamp)
