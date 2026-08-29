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
        touches_str = ",".join((str(t) for t in self.touches))
        return f"EmaPivotChoch|{self.side}|{self.candle.time}|pivot={self.pivot}|touches=[{touches_str}]|inner={self.inner_signal.choch_model}"


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
        self.use_bos = use_bos
        self.use_choch = use_choch
        self.ltf_chart: Chart
        self.htf_chart: Chart
        self.last_reported_time: datetime | None = None
        self._pivots: list[PivotPoint] = []
        self._emas: dict[int, dict[int, float]] = {}
        self._atr: dict[int, float] = {}
        self.debug_counters: dict[str, int] = {
            "pivots_in_window": 0,
            "touched_by_ema": 0,
            "ltf_window_ok": 0,
            "inner_choch_called": 0,
            "inner_choch_fresh_match": 0,
        }
        self.debug_last_call: dict = {}
        self._touch_events: dict[
            tuple, tuple[PivotPoint, tuple["EmaTouch", ...], Candle]
        ] = {}

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
        lo, hi = (0, len(candles))
        while lo < hi:
            mid = (lo + hi) // 2
            if candles[mid].time < from_time:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def _touching_emas(self, pivot: PivotPoint) -> list[EmaTouch]:
        atr_value = self._atr.get(pivot.candle.timestamp)
        max_distance = (atr_value * self.atr_multiplier) if atr_value is not None else 0.0
        if pivot.is_high:
            zone_low = pivot.candle.low
            zone_high = pivot.candle.high + max_distance
        else:
            zone_low = pivot.candle.low - max_distance
            zone_high = pivot.candle.high

        touches: list[EmaTouch] = []
        for period in self.ema_periods:
            ema_value = self._emas[period].get(pivot.candle.timestamp)
            if ema_value is None:
                continue
            if zone_low <= ema_value <= zone_high:
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
        pivot_detector = SwingPivots(
            depth=self.htf_pivot_length, backstep=self.htf_backstep
        )
        pivot_detector.set(htf_chartdata.candles)
        self._pivots = pivot_detector.data
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
            "htf_first_time": (
                htf_chartdata.candles[0].time if htf_chartdata.candles else None
            ),
            "htf_last_time": (
                htf_chartdata.candles[-1].time if htf_chartdata.candles else None
            ),
            "pivots_found": len(self._pivots),
            "pivots_time_range": (
                (self._pivots[0].candle.time, self._pivots[-1].candle.time)
                if self._pivots
                else None
            ),
        }
        best_signal: EmaPivotChochSignal | None = None
        for pivot in reversed(self._pivots):
            if last_ltf_candle.time < pivot.candle.time:
                continue
            required_side = MarketSide.BEARISH if pivot.is_high else MarketSide.BULLISH
            if required_side is MarketSide.BEARISH and (not check_short):
                continue
            if required_side is MarketSide.BULLISH and (not check_long):
                continue
            touches = self._touching_emas(pivot)
            if not touches:
                continue
            self.debug_counters["touched_by_ema"] += 1
            start_index = self._find_start_index(ltf_candles, pivot.candle.time)
            if start_index < len(ltf_candles):
                touch_key = (pivot.candle.time, pivot.is_high)
                if touch_key not in self._touch_events:
                    self._touch_events[touch_key] = (
                        pivot,
                        tuple(touches),
                        ltf_candles[start_index],
                    )
            if not self.use_choch:
                continue
            if start_index >= len(ltf_candles):
                continue
            window_candles = ltf_candles[start_index:]
            if len(window_candles) > self.max_bars_after_pivot + 1:
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
            if not self.use_bos and (not inner_signal.choch_model.is_choch):
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
            break
        if best_signal is None:
            return None
        if (
            self.last_reported_time is not None
            and best_signal.candle.time <= self.last_reported_time
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
        self.last_reported_time = best_signal.candle.time
        logger.info(f"Signal: {best_signal}")
        return best_signal

    def report(self, *args, **kwargs) -> str:
        return ""

    def describe_touches(self) -> list[dict]:
        htf_span = (
            self.htf_chart.timeframe.time_delta if hasattr(self, "htf_chart") else None
        )
        ltf_first_time = self.debug_last_call.get("ltf_first_time")
        out = []
        for pivot, touches, ltf_touch_candle in self._touch_events.values():
            delta = ltf_touch_candle.time - pivot.candle.time
            out_of_range = (
                ltf_first_time is not None and pivot.candle.time < ltf_first_time
            )
            out.append(
                {
                    "pivot_time": pivot.candle.time,
                    "pivot_is_high": pivot.is_high,
                    "ltf_marker_time": ltf_touch_candle.time,
                    "delta": delta,
                    "out_of_ltf_range": out_of_range,
                    "suspicious": not out_of_range
                    and htf_span is not None
                    and (delta >= htf_span),
                }
            )
        return sorted(out, key=lambda d: d["pivot_time"])

    def draw_touches(self, plot: DoubleChartPlot, color: str = "#ffb300"):
        ltf_points = []
        htf_bullish_points = []
        htf_bearish_points = []
        for pivot, touches, ltf_touch_candle in self._touch_events.values():
            ltf_source = CandlesSource.High if pivot.is_high else CandlesSource.Low
            ltf_points.append((ltf_touch_candle.time, ltf_source(ltf_touch_candle)))
            htf_source = CandlesSource.High if pivot.is_high else CandlesSource.Low
            htf_point = (pivot.candle.time, htf_source(pivot.candle))
            (htf_bearish_points if pivot.is_high else htf_bullish_points).append(
                htf_point
            )
        plot.base_plot.mark_points(ltf_points, color=color)
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
        if draw_emas:
            for period, ema_values in self._emas.items():
                plot.second_plot.linear_plot(ema_values.keys(), ema_values.values())
        pivot_color = "#ef5350" if signal.side is MarketSide.BEARISH else "#26a69a"
        pivot_source = CandlesSource.High if signal.pivot.is_high else CandlesSource.Low
        plot.second_plot.mark_candle(
            signal.pivot.candle, source=pivot_source, color=pivot_color
        )
        self._make_inner_filter()._draw_model(
            plot.base_plot, signal.inner_signal.choch_model
        )
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
        if not signals:
            return
        for period, ema_values in self._emas.items():
            plot.second_plot.linear_plot(ema_values.keys(), ema_values.values())
        model_pivot_points: dict[tuple, list] = {}
        retrace_points: dict[MarketSide, list] = {
            MarketSide.BULLISH: [],
            MarketSide.BEARISH: [],
        }
        for s in signals:
            model = s.inner_signal.choch_model
            base = "26a69a" if model.side is MarketSide.BULLISH else "ef5350"
            color = f"#{base}" if model.is_choch else f"#{base}70"
            width = 2 if model.is_choch else 1
            plot.base_plot.draw_line(
                model.pivot_candle.time,
                model.break_level,
                model.break_candle.time,
                model.break_level,
                color=color,
                width=width,
            )
            pivot_source = (
                CandlesSource.High
                if model.side is MarketSide.BULLISH
                else CandlesSource.Low
            )
            model_pivot_points.setdefault((model.side, color), []).append(
                (model.pivot_candle.time, pivot_source(model.pivot_candle))
            )
            if (
                self.use_fibo_filter
                and model.retrace_level is not None
                and (model.touch_candle is not None)
            ):
                plot.base_plot.draw_horizontal_line(
                    model.break_candle.time,
                    model.touch_candle.time,
                    model.retrace_level,
                    color=color,
                )
                retrace_points[model.side].append(
                    (model.touch_candle.time, model.retrace_level)
                )
        for (side, color), points in model_pivot_points.items():
            plot.base_plot.mark_points(points, color=color)
        for side, points in retrace_points.items():
            if not points:
                continue
            plot.base_plot.mark_points(
                points, color="#1DBD1D" if side is MarketSide.BULLISH else "#BD1D1D"
            )
        plot.base_plot.mark_signals([s.inner_signal for s in signals])
        if draw_indicators and self.confirmation_indicators:
            for indicator in self.confirmation_indicators:
                indicator.plot(plot.base_plot)

    def generate_dummy_signal(
        self, base_chartdata: ChartData, side: MarketSide = MarketSide.BULLISH
    ) -> EmaPivotChochSignal:
        inner_signal = self._make_inner_filter().generate_dummy_signal(
            base_chartdata, side
        )
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
            base_chartdata.chart,
            inner_signal.candle,
            side,
            dummy_pivot,
            touches,
            inner_signal,
        )


@dataclass(kw_only=True)
class EmaPivotChochTradeConfig(TradeConfig):
    htf_chart: Chart
    strategy: EmaPivotChochFilter
    n_ltf_candle_check: int = 1500
    n_htf_candle_check: int = 500

    def export_config(self) -> dict:
        conf_dict = super().export_config()
        conf_dict.update({"htf_chart": self.htf_chart.export_config()})
        return conf_dict

    def get_chartdata(
        self, n_bar: int | None = None, *args, **kwargs
    ) -> tuple[ChartData, ChartData]:
        ltf_chartdata = self.agent.get_chartdata(
            self.chart, n_bar if n_bar else self.n_ltf_candle_check
        )
        htf_chartdata = self.agent.get_chartdata(
            self.htf_chart, n_bar if n_bar else self.n_htf_candle_check
        )
        if ltf_chartdata is None or htf_chartdata is None:
            raise ValueError(f"chart data is None from {self.agent.__class__.__name__}")
        if self.heikingashi_chartdata:
            ltf_chartdata = ltf_chartdata.give_heikingashi_chartdata()
            htf_chartdata = htf_chartdata.give_heikingashi_chartdata()
        return (ltf_chartdata, htf_chartdata)

    def _make_plot(self, ltf_chartdata: ChartData, htf_chartdata: ChartData) -> DoubleChartPlot:
        plot_n_candles = max(len(ltf_chartdata.candles), len(htf_chartdata.candles))
        return DoubleChartPlot(ltf_chartdata, htf_chartdata, plot_n_candles=plot_n_candles)

    async def find_signal(
        self, chartdata: ChartData, htf_chartdata: ChartData, *args, **kwargs
    ) -> None | tuple[EmaPivotChochSignal, Position] | EmaPivotChochSignal:
        signal = self.strategy.check_signal(
            chartdata, htf_chartdata, self.long_signal, self.short_signal
        )
        if signal is None:
            return None
        logger.info(f"EmaPivotChoch Signal: {signal}")
        plot = None
        if self.send_signal:
            plot = self._make_plot(chartdata, htf_chartdata)
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
        return (signal, position)

    async def send_touch_report(self, ltf_chartdata: ChartData, htf_chartdata: ChartData):
        plot = self._make_plot(ltf_chartdata, htf_chartdata)
        for period, ema_values in self.strategy._emas.items():
            plot.second_plot.linear_plot(ema_values.keys(), ema_values.values())
        self.strategy.draw_touches(plot)
        img_path = plot.save_image(f"{self.strategy.name}_{self.chart}")
        msg = f"{self.strategy.name}\n📈 {self.chart}\nEMA-pivot touch report"
        await TelegramReporter().send_msg(TelegramReporter().main_channel, msg, img_path)

    async def task(self):
        ltf_chartdata, htf_chartdata = self.get_chartdata()
        ltf_data = copy(ltf_chartdata)
        ltf_data.candles = ltf_data.candles[:-1]
        htf_data = copy(htf_chartdata)
        htf_data.candles = htf_data.candles[:-1]

        touch_count_before = len(self.strategy._touch_events)
        res = await self.find_signal(ltf_data, htf_data)
        new_touch = len(self.strategy._touch_events) > touch_count_before

        if new_touch and not self.strategy.use_bos and not self.strategy.use_choch:
            await self.send_touch_report(ltf_data, htf_data)

        if res is None:
            return self.give_delay(ltf_data[-1])
        if isinstance(res, tuple):
            signal, position = res
        else:
            signal = res
            position = None
        return (self.give_delay(ltf_data[-1], jump=True), signal, position)
