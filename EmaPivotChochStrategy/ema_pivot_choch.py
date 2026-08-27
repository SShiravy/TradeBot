"""
EMA-Pivot-CHoCH strategy.

Idea
----
On a higher timeframe (HTF) chosen by the user, we watch 3 user-supplied EMAs.
Whenever at least one of those EMAs "touches" a swing pivot candle on the HTF
(i.e. the EMA value sits between the pivot candle's high/low, or is within
`x * ATR` beyond the pivot's high/low), that pivot becomes a confluence zone:

    - EMA touching a Pivot HIGH  -> we expect a bearish reversal
    - EMA touching a Pivot LOW   -> we expect a bullish reversal

From the moment of that touch, we drop down to a lower timeframe (LTF) and,
for up to `max_bars_after_pivot` LTF candles (default 100), watch for a
CHoCH/BOS in the expected direction using the exact same engine as
`ChochQueueStrategy.ChochQueueFilter`. If `use_fibo_filter` is on (inherited
by the inner filter), the entry only fires once price retraces back into the
CHoCH/BOS leg's fibonacci zone; if it's off, the entry fires the moment the
CHoCH/BOS candle closes.

Nothing here reimplements swing-pivot detection, EMA/ATR calculation or
CHoCH/BOS detection: `SwingPivots`, `EMA`, `ATR` and `ChochQueueFilter` are
reused as-is from the rest of the project.
"""

from ChartModule.models import (
    Chart,
    Signal,
    ChartData,
    MarketSide,
    Candle,
    CandlesSource,
)
from ChartModule.Indicators import IndicatorBaseModel, SupportCandleConditions
from ChartModule.Indicators.swing_pivots import SwingPivots, PivotPoint
from ChartModule.Indicators.moving_avg import EMA
from AutoTrendlineModule.atr import ATR
from ChartModule.plot import DoubleChartPlot
from TradingModule.trader_bot import TradeConfig
from TradingModule.reporter import TelegramReporter
from TradingModule.models import Position, Strategy
from ChochQueueStrategy.choch_queue import ChochQueueFilter, ChochSignal
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from copy import copy
import logging


logger = logging.getLogger("EmaPivotChoch")


@dataclass(slots=True, frozen=True)
class EmaTouch:
    ema_period: int
    ema_value: float

    def __str__(self) -> str:
        return f"EMA{self.ema_period}@{self.ema_value:.5f}"


@dataclass(slots=True, frozen=True)
class EmaPivotChochSignal(Signal):
    source: str = field(default="EmaPivotChoch", init=False)
    pivot: PivotPoint
    touches: tuple[EmaTouch, ...]
    inner_signal: ChochSignal

    def __str__(self) -> str:
        touches_str = ",".join(str(t) for t in self.touches)
        return (
            f"EmaPivotChoch|{self.side}|{self.candle.time}|pivot={self.pivot}"
            f"|touches=[{touches_str}]|inner={self.inner_signal.choch_model}"
        )


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
        confirmation_indicators: list[IndicatorBaseModel] = [],
        long_support_conditions=SupportCandleConditions.RAW,
        short_support_conditions=SupportCandleConditions.RAW,
        name="EmaPivotChoch",
    ) -> None:
        super().__init__(
            name,
            long_support_conditions,
            short_support_conditions,
            confirmation_indicators,
        )
        if len(ema_periods) != 3:
            raise ValueError("ema_periods must contain exactly 3 EMA lengths")

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
        # True (default): accept both CHoCH (real character change) and BOS
        # (break of structure, continuation) as valid entry triggers.
        # False: only take genuine CHoCH breaks, ignore BOS ones.
        self.use_bos = use_bos

        self.ltf_chart: Chart
        self.htf_chart: Chart
        self.last_reported_time: datetime | None = None

        # kept around after every check_signal() call, only used by draw()
        self._pivots: list[PivotPoint] = []
        self._emas: dict[int, dict[int, float]] = {}
        self._atr: dict[int, float] = {}

        # cumulative diagnostics across every check_signal() call on this
        # instance - useful to see exactly where candidates get dropped
        # (e.g. call this in a loop, then inspect strategy.debug_counters)
        self.debug_counters: dict[str, int] = {
            "pivots_in_window": 0,   # recent enough + right side enabled
            "touched_by_ema": 0,     # + at least one EMA touch
            "ltf_window_ok": 0,      # + a usable LTF slice exists
            "inner_choch_called": 0,
            "inner_choch_fresh_match": 0,  # CHoCH landed exactly on the last candle
        }
        # snapshot of the *last* check_signal() call only, to spot data/overlap
        # problems (e.g. HTF and LTF chartdata not covering the same period)
        self.debug_last_call: dict = {}

        # every EMA-pivot touch ever seen (regardless of whether a CHoCH/BOS
        # ever followed it), keyed by the pivot's own identity so repeated
        # check_signal() calls across a walk-forward don't duplicate it.
        # value: (pivot, touches, ltf_touch_candle)
        self._touch_events: dict[tuple, tuple[PivotPoint, tuple["EmaTouch", ...], Candle]] = {}

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
            }
        )
        return conf_dict

    def _make_inner_filter(self) -> ChochQueueFilter:
        return ChochQueueFilter(
            pivot_length=self.choch_pivot_length,
            backstep=self.choch_backstep,
            retrace_fib=self.retrace_fib,
            use_fibo_filter=self.use_fibo_filter,
            name=f"{self.name}_inner",
        )

    @staticmethod
    def _find_start_index(candles: list[Candle], from_time: datetime) -> int:
        """
        Index of the first candle whose time is >= from_time (bisect_left on
        an ascending-sorted candle list).
        """
        lo, hi = 0, len(candles)
        while lo < hi:
            mid = (lo + hi) // 2
            if candles[mid].time < from_time:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def _touching_emas(self, pivot: PivotPoint) -> list[EmaTouch]:
        """
        Which of the 3 EMAs (evaluated on the HTF, at the pivot candle's own
        timestamp) are touching this pivot: either sitting inside the
        candle's high/low range, or within `atr_multiplier * ATR` beyond it.
        """
        atr_value = self._atr.get(pivot.candle.timestamp)
        touches: list[EmaTouch] = []
        for period in self.ema_periods:
            ema_value = self._emas[period].get(pivot.candle.timestamp)
            if ema_value is None:
                continue

            if pivot.candle.low <= ema_value <= pivot.candle.high:
                touches.append(EmaTouch(period, ema_value))
                continue

            if atr_value is None:
                continue
            max_distance = atr_value * self.atr_multiplier

            if ema_value > pivot.candle.high and (ema_value - pivot.candle.high) <= max_distance:
                touches.append(EmaTouch(period, ema_value))
            elif ema_value < pivot.candle.low and (pivot.candle.low - ema_value) <= max_distance:
                touches.append(EmaTouch(period, ema_value))

        return touches

    def check_signal(
        self,
        ltf_chartdata: ChartData,
        htf_chartdata: ChartData,
        check_long: bool = True,
        check_short: bool = True,
        *args,
        **kwargs,
    ) -> EmaPivotChochSignal | None:
        self.ltf_chart = ltf_chartdata.chart
        self.htf_chart = htf_chartdata.chart

        pivot_detector = SwingPivots(depth=self.htf_pivot_length, backstep=self.htf_backstep)
        pivot_detector.set(htf_chartdata.candles)
        self._pivots = pivot_detector.data  # confirmed pivots only, oldest -> newest

        self._emas = {}
        for period in self.ema_periods:
            self._emas[period] = EMA(period).set(htf_chartdata.candles)

        self._atr = ATR(self.atr_period).set(htf_chartdata.candles) or {}

        ltf_candles = ltf_chartdata.candles
        last_ltf_candle = ltf_candles[-1]

        self.debug_last_call = {
            "ltf_candle_count": len(ltf_candles),
            "ltf_first_time": ltf_candles[0].time,
            "ltf_last_time": last_ltf_candle.time,
            "htf_candle_count": len(htf_chartdata.candles),
            "htf_first_time": htf_chartdata.candles[0].time if htf_chartdata.candles else None,
            "htf_last_time": htf_chartdata.candles[-1].time if htf_chartdata.candles else None,
            "pivots_found": len(self._pivots),
            "pivots_time_range": (
                (self._pivots[0].candle.time, self._pivots[-1].candle.time)
                if self._pivots
                else None
            ),
        }

        best_signal: EmaPivotChochSignal | None = None

        for pivot in reversed(self._pivots):
            # pivots are oldest -> newest, so scanning in reverse we hit the
            # newest (most relevant) ones first
            if last_ltf_candle.time < pivot.candle.time:
                continue

            required_side = MarketSide.BEARISH if pivot.is_high else MarketSide.BULLISH
            if required_side is MarketSide.BEARISH and not check_short:
                continue
            if required_side is MarketSide.BULLISH and not check_long:
                continue

            # Touch detection is intentionally independent of
            # max_bars_after_pivot: we want every EMA-pivot touch recorded,
            # whether or not a CHoCH/BOS ever follows it. Only the *signal
            # search* below is limited to the max_bars_after_pivot window.
            touches = self._touching_emas(pivot)
            if not touches:
                continue
            self.debug_counters["touched_by_ema"] += 1

            start_index = self._find_start_index(ltf_candles, pivot.candle.time)
            if start_index < len(ltf_candles):
                touch_key = (pivot.candle.time, pivot.is_high)
                if touch_key not in self._touch_events:
                    self._touch_events[touch_key] = (pivot, tuple(touches), ltf_candles[start_index])

            # NOTE: gate on actual LTF candle count, not calendar time. Real
            # feeds are not gap-free (weekends, closed sessions, thin
            # liquidity), so "N candles" and "N * timeframe" of calendar time
            # can differ hugely - using calendar time here would wrongly
            # expire pivots that are still well within the intended
            # `max_bars_after_pivot` candle window.
            if start_index >= len(ltf_candles):
                continue
            window_candles = ltf_candles[start_index:]
            if len(window_candles) > self.max_bars_after_pivot + 1:
                # too old for a fresh signal search - but its touch was
                # already recorded above, and we keep scanning older pivots
                # too (they may still be touched and worth marking, even
                # though none of them can produce a signal anymore either).
                continue
            if len(window_candles) < 3:
                continue

            self.debug_counters["pivots_in_window"] += 1
            self.debug_counters["ltf_window_ok"] += 1

            window_chartdata = ltf_chartdata.give_sub_chartdata(window_candles)
            self.debug_counters["inner_choch_called"] += 1
            inner_signal = self._make_inner_filter().check_signal(
                window_chartdata,
                check_long=required_side is MarketSide.BULLISH,
                check_short=required_side is MarketSide.BEARISH,
            )
            if inner_signal is None or inner_signal.candle.time != last_ltf_candle.time:
                continue
            if not self.use_bos and not inner_signal.choch_model.is_choch:
                # this was a BOS (continuation), not a genuine CHoCH
                # (character change) - skip it since use_bos is off
                continue
            self.debug_counters["inner_choch_fresh_match"] += 1

            best_signal = EmaPivotChochSignal(
                self.ltf_chart,
                inner_signal.candle,
                required_side,
                pivot,
                tuple(touches),
                inner_signal,
            )
            break  # the newest matching pivot wins

        if best_signal is None:
            return None
        if (
            self.last_reported_time is not None
            and best_signal.candle.time <= self.last_reported_time
        ):
            return None

        confirmations = self.get_indicators_confirmation(ltf_chartdata)
        if best_signal.side is MarketSide.BULLISH and MarketSide.BEARISH in confirmations:
            logger.debug(f"indicators rejected the signal: {best_signal}")
            return None
        if best_signal.side is MarketSide.BEARISH and MarketSide.BULLISH in confirmations:
            logger.debug(f"indicators rejected the signal: {best_signal}")
            return None

        self.last_reported_time = best_signal.candle.time
        logger.info(f"Signal: {best_signal}")
        return best_signal

    def report(self, *args, **kwargs) -> str:
        return ""

    def describe_touches(self) -> list[dict]:
        """
        Diagnostic helper: for every recorded EMA-pivot touch, report the
        HTF pivot's own candle time next to the LTF candle it got marked at
        on the chart, and how far apart they are. In a correct mapping this
        delta should always be between 0 and one HTF-timeframe duration
        (e.g. under 1h if htf_chart is 1h) - since the LTF marker is simply
        the first LTF candle inside that same HTF bar. A bigger delta means
        the LTF marker landed in a later HTF bar than the one the pivot
        actually belongs to.

        Pivots whose own candle predates the fetched LTF window are a known,
        separate case (there's no LTF data that far back, so they get
        pinned to the first available LTF candle) - these are reported as
        `out_of_ltf_range`, not `suspicious`, so they don't drown out real
        misalignments in the log.
        """
        htf_span = self.htf_chart.timeframe.time_delta if hasattr(self, "htf_chart") else None
        ltf_first_time = self.debug_last_call.get("ltf_first_time")
        out = []
        for pivot, touches, ltf_touch_candle in self._touch_events.values():
            delta = ltf_touch_candle.time - pivot.candle.time
            out_of_range = ltf_first_time is not None and pivot.candle.time < ltf_first_time
            out.append(
                {
                    "pivot_time": pivot.candle.time,
                    "pivot_is_high": pivot.is_high,
                    "ltf_marker_time": ltf_touch_candle.time,
                    "delta": delta,
                    "out_of_ltf_range": out_of_range,
                    "suspicious": (not out_of_range) and htf_span is not None and delta >= htf_span,
                }
            )
        return sorted(out, key=lambda d: d["pivot_time"])

    def draw_touches(self, plot: DoubleChartPlot, color: str = "#ffb300"):
        """
        Mark every EMA-pivot touch ever recorded (via check_signal calls on
        this instance) on the LTF pane, regardless of whether a CHoCH/BOS
        ever followed it, AND mark the corresponding pivot on the HTF pane
        too (so every LTF touch marker has a matching HTF pivot marker -
        draw_all() only marks HTF pivots for signals that actually fired,
        which is a smaller set than every recorded touch).
        Call this after your check_signal() walk so self._touch_events is
        fully populated.
        """
        ltf_points = []
        htf_bullish_points = []
        htf_bearish_points = []
        for pivot, touches, ltf_touch_candle in self._touch_events.values():
            ltf_source = CandlesSource.High if pivot.is_high else CandlesSource.Low
            ltf_points.append((ltf_touch_candle.time, ltf_source(ltf_touch_candle)))

            htf_source = CandlesSource.High if pivot.is_high else CandlesSource.Low
            htf_point = (pivot.candle.time, htf_source(pivot.candle))
            (htf_bearish_points if pivot.is_high else htf_bullish_points).append(htf_point)

        plot.base_plot.mark_points(ltf_points, legend="EMA-pivot touch", color=color)
        plot.second_plot.mark_points(htf_bullish_points, color="#26a69a")
        plot.second_plot.mark_points(htf_bearish_points, color="#ef5350")

    def draw(
        self,
        plot: DoubleChartPlot,
        signal: EmaPivotChochSignal,
        draw_indicators: bool = True,
        draw_emas: bool = True,
        *args,
        **kwargs,
    ):
        # HTF pane: the 3 EMAs (only need to be drawn once if you're calling
        # this in a loop for many signals - pass draw_emas=False after the
        # first call) + the pivot that got touched for THIS signal
        if draw_emas:
            for period, ema_values in self._emas.items():
                plot.second_plot.linear_plot(ema_values.keys(), ema_values.values(), legend=f"EMA{period}")

        pivot_color = "#ef5350" if signal.side is MarketSide.BEARISH else "#26a69a"
        pivot_source = CandlesSource.High if signal.pivot.is_high else CandlesSource.Low
        plot.second_plot.mark_candle(signal.pivot.candle, source=pivot_source, color=pivot_color)

        # LTF pane: the CHoCH/BOS structure (+ optional fibo retrace) that triggered the entry
        self._make_inner_filter()._draw_model(plot.base_plot, signal.inner_signal.choch_model)
        plot.base_plot.mark_signal(signal.inner_signal)

        if draw_indicators and self.confirmation_indicators:
            for indicator in self.confirmation_indicators:
                indicator.plot(plot.base_plot)

    def draw_all(
        self,
        plot: DoubleChartPlot,
        signals: list[EmaPivotChochSignal],
        draw_indicators: bool = True,
    ):
        """
        Draw a whole list of signals (e.g. everything found during a
        walk-forward backtest) at once. Prefer this over calling draw() in a
        loop: each mark_candle()/mark_signal() call adds its own trace, and
        many single-point traces added one at a time make finplot's
        auto-view zoom in on just the last one, leaving the rest of the
        chart (including the candlesticks) far outside the visible
        viewport. This batches every pivot marker and every entry marker
        into one call each per side/color.
        """
        if not signals:
            return

        for period, ema_values in self._emas.items():
            plot.second_plot.linear_plot(ema_values.keys(), ema_values.values(), legend=f"EMA{period}")

        # NOTE: the HTF pivot markers themselves are drawn by draw_touches()
        # for every recorded touch (a superset of the pivots behind these
        # signals), so we don't duplicate them here.

        model_pivot_points: dict[tuple, list] = {}
        retrace_points: dict[MarketSide, list] = {MarketSide.BULLISH: [], MarketSide.BEARISH: []}
        for s in signals:
            model = s.inner_signal.choch_model
            base = "26a69a" if model.side is MarketSide.BULLISH else "ef5350"
            color = f"#{base}" if model.is_choch else f"#{base}70"
            width = 2 if model.is_choch else 1
            # the line has real x-extent (pivot -> break time) so it's safe
            # to draw one at a time - it won't collapse finplot's viewport
            # the way a lone single-point marker does
            plot.base_plot.draw_line(
                model.pivot_candle.time,
                model.break_level,
                model.break_candle.time,
                model.break_level,
                color=color,
                width=width,
            )
            pivot_source = CandlesSource.High if model.side is MarketSide.BULLISH else CandlesSource.Low
            model_pivot_points.setdefault((model.side, color), []).append(
                (model.pivot_candle.time, pivot_source(model.pivot_candle))
            )
            if (
                self.use_fibo_filter
                and model.retrace_level is not None
                and model.touch_candle is not None
            ):
                plot.base_plot.draw_horizontal_line(
                    model.break_candle.time, model.touch_candle.time, model.retrace_level, color=color
                )
                retrace_points[model.side].append((model.touch_candle.time, model.retrace_level))

        for (side, color), points in model_pivot_points.items():
            plot.base_plot.mark_points(points, color=color)
        for side, points in retrace_points.items():
            if not points:
                continue
            # simplified as circles (not the ^/v triangles mark_price uses)
            # so we can batch them in one call instead of one per model
            plot.base_plot.mark_points(
                points, color="#1DBD1D" if side is MarketSide.BULLISH else "#BD1D1D"
            )

        plot.base_plot.mark_signals([s.inner_signal for s in signals])

        if draw_indicators and self.confirmation_indicators:
            for indicator in self.confirmation_indicators:
                indicator.plot(plot.base_plot)

    def generate_dummy_signal(
        self,
        base_chartdata: ChartData,
        side: MarketSide = MarketSide.BULLISH,
    ) -> EmaPivotChochSignal:
        inner_signal = self._make_inner_filter().generate_dummy_signal(base_chartdata, side)

        pivot_candle = base_chartdata.candles[-8]
        dummy_pivot = PivotPoint(
            index=len(base_chartdata.candles) - 8,
            candle=pivot_candle,
            price=pivot_candle.high if side is MarketSide.BEARISH else pivot_candle.low,
            is_high=side is MarketSide.BEARISH,
            confirmed_index=len(base_chartdata.candles) - 8,
            confirmed=True,
        )
        ema_value = (pivot_candle.high + pivot_candle.low) / 2
        touches = (EmaTouch(self.ema_periods[0], ema_value),)

        return EmaPivotChochSignal(
            base_chartdata.chart, inner_signal.candle, side, dummy_pivot, touches, inner_signal
        )


@dataclass(kw_only=True)
class EmaPivotChochTradeConfig(TradeConfig):
    htf_chart: Chart
    strategy: EmaPivotChochFilter  # type: ignore[override]

    def export_config(self) -> dict:
        conf_dict = super().export_config()
        conf_dict.update({"htf_chart": self.htf_chart.export_config()})
        return conf_dict

    def get_chartdata(self, n_bar: int | None = None, *args, **kwargs) -> tuple[ChartData, ChartData]:  # type: ignore[override]
        ltf_chartdata = self.agent.get_chartdata(
            self.chart, n_bar if n_bar else self.n_candle_check
        )
        htf_chartdata = self.agent.get_chartdata(
            self.htf_chart, n_bar if n_bar else self.n_candle_check
        )

        if ltf_chartdata is None or htf_chartdata is None:
            raise ValueError(f"chart data is None from {self.agent.__class__.__name__}")

        if self.heikingashi_chartdata:
            ltf_chartdata = ltf_chartdata.give_heikingashi_chartdata()
            htf_chartdata = htf_chartdata.give_heikingashi_chartdata()

        return ltf_chartdata, htf_chartdata

    async def find_signal(
        self,
        chartdata: ChartData,
        htf_chartdata: ChartData,
        *args,
        **kwargs,
    ) -> None | tuple[EmaPivotChochSignal, Position] | EmaPivotChochSignal:
        signal = self.strategy.check_signal(
            chartdata, htf_chartdata, self.long_signal, self.short_signal
        )
        if signal is None:
            return None
        logger.info(f"EmaPivotChoch Signal: {signal}")

        plot = None
        if self.send_signal:
            plot = DoubleChartPlot(chartdata, htf_chartdata)
            self.strategy.draw(plot, signal, draw_indicators=True)

        if not self.consider_position:
            if self.send_signal:
                await TelegramReporter().new_signal(signal, plot)
            return signal

        position = await self.position_handler.generate_position(
            signal, sl_base_price=signal.inner_signal.choch_model.anchor, plot=plot
        )
        if not position:
            return None
        return signal, position

    async def task(self):
        ltf_chartdata, htf_chartdata = self.get_chartdata()

        ltf_data = copy(ltf_chartdata)
        ltf_data.candles = ltf_data.candles[:-1]

        htf_data = copy(htf_chartdata)
        htf_data.candles = htf_data.candles[:-1]

        res = await self.find_signal(ltf_data, htf_data)
        if res is None:
            return self.give_delay(ltf_data[-1])
        if isinstance(res, tuple):
            signal, position = res
        else:
            signal = res
            position = None
        return self.give_delay(ltf_data[-1], jump=True), signal, position
