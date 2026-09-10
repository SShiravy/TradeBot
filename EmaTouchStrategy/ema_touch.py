from ChartModule.models import (
    Chart,
    Signal,
    ChartData,
    MarketSide,
    Candle,
    CandlesSource,
)
from ChartModule.Indicators import IndicatorBaseModel, SupportCandleConditions
from ChartModule.Indicators.moving_avg import EMA
from ChartModule.plot import ChartPlot
from TradingModule.trader_bot import TradeConfig
from TradingModule.models import Position, Strategy
from dataclasses import dataclass, field
import logging
import colorsys

logger = logging.getLogger("EmaTouch")


@dataclass(slots=True, frozen=True)
class EmaTouchSignal(Signal):
    source: str = field(default="EmaTouch", init=False)
    ema_period: int
    ema_value: float
    break_candle: Candle
    first_touch_candle: Candle

    def __str__(self) -> str:
        return (
            f"{self.chart} {self.side} EMA{self.ema_period}@{self.ema_value:.5f} "
            f"broke {self.break_candle.time} -> 1st touch {self.first_touch_candle.time} "
            f"-> signal {self.candle.time}"
        )


class EmaTouchFilter(Strategy):

    def __init__(
        self,
        ema_periods: list[int],
        min_candles_between_touches: int = 15,
        max_candles_between_touches: int = 200,
        reanchor_invalid_touch: bool = False,
        confirmation_indicators: list[IndicatorBaseModel] = [],
        long_support_conditions=SupportCandleConditions.RAW,
        short_support_conditions=SupportCandleConditions.RAW,
        name="EmaTouch",
    ) -> None:
        """
        reanchor_invalid_touch: how an out-of-window second touch is
        handled.
          False (default, "wait") -> an early touch (before
              min_candles_between_touches have passed) is ignored and we
              keep waiting on the *same* first touch until the window
              closes; a late touch (after max_candles_between_touches has
              already elapsed) means the window is over with no signal,
              so the setup resets to idle.
          True ("re_anchor") -> ANY out-of-window touch (early or late)
              itself becomes the new first touch and the window restarts
              counting from it.
        """
        super().__init__(
            name,
            long_support_conditions,
            short_support_conditions,
            confirmation_indicators,
        )
        self.ema_periods = ema_periods
        self.min_candles_between_touches = min_candles_between_touches
        self.max_candles_between_touches = max_candles_between_touches
        self.reanchor_invalid_touch = reanchor_invalid_touch

        self.chart: Chart | None = None
        self.last_reported_time = None
        self._emas: dict[int, dict] = {}
        # last full walk's state per period, kept only so draw()/debugging
        # can inspect it - check_signal() replays the whole given window
        # fresh every call (same convention as EmaPivotChochFilter) and
        # never relies on this being carried forward from a prior call.
        self.debug_last_call: dict = {}

    def check_signal(
        self,
        chartdata: ChartData,
        check_long: bool = True,
        check_short: bool = True,
        *args,
        **kwargs,
    ) -> EmaTouchSignal | None:
        self.chart = chartdata.chart
        candles = chartdata.candles
        if len(candles) < 3:
            return None
        last_candle = candles[-1]

        self._emas = {period: EMA(period).set(candles) for period in self.ema_periods}
        self.debug_last_call = {
            "candle_count": len(candles),
            "first_time": candles[0].time,
            "last_time": last_candle.time,
        }

        best_signal: EmaTouchSignal | None = None
        for period in self.ema_periods:
            signal = self._walk_period(candles, period, last_candle)
            if signal is None:
                continue
            if signal.side is MarketSide.BULLISH and not check_long:
                continue
            if signal.side is MarketSide.BEARISH and not check_short:
                continue
            best_signal = signal
            break

        if best_signal is None:
            return None
        if (
            self.last_reported_time is not None
            and best_signal.candle.time <= self.last_reported_time
        ):
            return None

        confirmations = self.get_indicators_confirmation(chartdata)
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

    def _walk_period(
        self, candles: list[Candle], period: int, last_candle: Candle
    ) -> EmaTouchSignal | None:
        ema_values = self._emas[period]

        phase = "idle"  # idle | waiting_first_touch | waiting_second_touch
        direction: MarketSide | None = None
        break_candle: Candle | None = None
        first_touch_candle: Candle | None = None
        first_touch_index: int | None = None

        prev_close: float | None = None
        prev_ema: float | None = None
        result: EmaTouchSignal | None = None

        for i, candle in enumerate(candles):
            ema_value = ema_values.get(candle.timestamp)
            if ema_value is None:
                prev_close, prev_ema = None, None
                continue

            broke_down = (
                prev_close is not None
                and prev_ema is not None
                and prev_close >= prev_ema
                and candle.close < ema_value
                and candle.side is MarketSide.BEARISH
            )
            broke_up = (
                prev_close is not None
                and prev_ema is not None
                and prev_close <= prev_ema
                and candle.close > ema_value
                and candle.side is MarketSide.BULLISH
            )

            if phase != "idle" and (
                (direction is MarketSide.BEARISH and broke_up)
                or (direction is MarketSide.BULLISH and broke_down)
            ):
                # the original break is no longer valid - price closed
                # back through the EMA the other way. Drop the setup; the
                # same candle is still checked below for starting a fresh
                # break of its own.
                phase, direction = "idle", None
                break_candle = first_touch_candle = None
                first_touch_index = None

            if phase == "idle":
                if broke_down:
                    phase, direction, break_candle = (
                        "waiting_first_touch",
                        MarketSide.BEARISH,
                        candle,
                    )
                elif broke_up:
                    phase, direction, break_candle = (
                        "waiting_first_touch",
                        MarketSide.BULLISH,
                        candle,
                    )
                prev_close, prev_ema = candle.close, ema_value
                continue

            touched = candle.low <= ema_value <= candle.high
            if touched:
                if phase == "waiting_first_touch":
                    first_touch_candle, first_touch_index = candle, i
                    phase = "waiting_second_touch"
                elif phase == "waiting_second_touch":
                    assert first_touch_index is not None
                    span = i - first_touch_index
                    if (
                        self.min_candles_between_touches
                        <= span
                        <= self.max_candles_between_touches
                    ):
                        if candle.time == last_candle.time:
                            assert break_candle is not None and first_touch_candle is not None
                            result = EmaTouchSignal(
                                self.chart,
                                candle,
                                direction,
                                ema_period=period,
                                ema_value=ema_value,
                                break_candle=break_candle,
                                first_touch_candle=first_touch_candle,
                            )
                        phase, direction = "idle", None
                        break_candle = first_touch_candle = None
                        first_touch_index = None
                    elif span < self.min_candles_between_touches:
                        if self.reanchor_invalid_touch:
                            first_touch_candle, first_touch_index = candle, i
                        # else ("wait"): ignore, keep waiting on the same
                        # first touch until the window closes
                    else:  # span > max_candles_between_touches
                        if self.reanchor_invalid_touch:
                            first_touch_candle, first_touch_index = candle, i
                        else:
                            # window is over with nothing valid in it
                            phase, direction = "idle", None
                            break_candle = first_touch_candle = None
                            first_touch_index = None

            prev_close, prev_ema = candle.close, ema_value

        return result

    def _ema_colors(self) -> dict[int, str]:
        n = len(self.ema_periods)
        colors = {}
        for i, period in enumerate(self.ema_periods):
            hue = i / n
            r, g, b = colorsys.hsv_to_rgb(hue, 0.65, 0.85)
            colors[period] = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
        return colors

    def report(self, *args, **kwargs) -> str:
        return ""

    def draw(
        self,
        plot: ChartPlot,
        signal: EmaTouchSignal,
        draw_indicators: bool = True,
        *args,
        **kwargs,
    ):
        super().draw(plot, signal, draw_indicators)
        ema_values = self._emas.get(signal.ema_period)
        if ema_values:
            plot.linear_plot(
                list(ema_values.keys()),
                list(ema_values.values()),
                color=self._ema_colors()[signal.ema_period],
                legend=f"EMA{signal.ema_period}",
            )
        color = "#26a69a" if signal.side is MarketSide.BULLISH else "#ef5350"
        # a down-break/BEARISH setup is touched by a candle reaching UP
        # from below (its high); an up-break/BULLISH setup is touched by
        # a candle reaching DOWN from above (its low).
        touch_source = (
            CandlesSource.Low if signal.side is MarketSide.BULLISH else CandlesSource.High
        )
        plot.mark_candle(
            signal.break_candle, source=CandlesSource.Close, color="#ff9800", legend="Break"
        )
        plot.mark_candle(
            signal.first_touch_candle,
            source=touch_source,
            color="#ffd54f",
            legend="1st touch",
        )
        plot.draw_horizontal_line(
            signal.first_touch_candle.time,
            signal.candle.time,
            signal.ema_value,
            color=color,
        )
        plot.mark_signal(signal)

    def draw_all(
        self,
        plot: ChartPlot,
        signals: list[EmaTouchSignal],
        draw_indicators: bool = True,
    ):
        if not signals:
            return
        self.draw(plot, signals[0], draw_indicators=draw_indicators)
        for signal in signals[1:]:
            self.draw(plot, signal, draw_indicators=False)


class EmaTouchTradeConfig(TradeConfig):
    strategy: EmaTouchFilter  # type: ignore[override]
