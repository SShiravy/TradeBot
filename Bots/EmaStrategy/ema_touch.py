from ChartModule.models import (
    Chart,
    Signal,
    ChartData,
    MarketSide,
    Candle,
    CandlesSource,
)
from ChartModule.Indicators import Indicator, SupportCandlesPattern
from ChartModule.Indicators.moving_avg import EMA
from ChartModule.plot import ChartPane, SingleChartFigure
from TraderBot.models import ExchangeAgent, Position, Strategy, StrategyPlotter
from TraderBot.PositionHandlers.manager import TradesManager
from TraderBot.PositionHandlers.plot import PositionPlotter
from TraderBot.trader_bot import TraderBot
from dataclasses import dataclass
import pandas as pd
import numpy as np
import logging
import colorsys

logger = logging.getLogger("EmaTouch")


@dataclass(slots=True, frozen=True)
class EmaTouchSignal(Signal):
    ema_period: int
    ema_value: float
    break_candle: Candle
    first_touch_candle: Candle

    def __str__(self) -> str:
        return (
            f"{self.chart} {self.side} EMA{self.ema_period}@{self.ema_value:.5f} "
            f"broke {self.break_candle.timestamp} "
            f"-> 1st touch {self.first_touch_candle.timestamp} "
            f"-> signal {self.candle.timestamp}"
        )


def ema_colors(periods: list[int]) -> dict[int, str]:
    colors = {}
    for i, period in enumerate(periods):
        hue = i / len(periods)
        r, g, b = colorsys.hsv_to_rgb(hue, 0.65, 0.85)
        colors[period] = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
    return colors


class EmaTouchPlotter(StrategyPlotter):
    BULLISH_COLOR = "#26a69a"
    BEARISH_COLOR = "#ef5350"
    BREAK_COLOR = "#ff9800"
    TOUCH_COLOR = "#ffd54f"

    @staticmethod
    def _candle_index(pane: ChartPane, candle: Candle) -> int | None:
        """
        Position of `candle` in the pane's visible window, or None when it
        falls outside it -- the pane only holds the tail that is drawn, so
        an older break candle simply has nothing to mark.
        """
        chartdata = pane.chartdata
        if chartdata is None:
            return None
        idx = int(np.searchsorted(chartdata.timestamps, candle.timestamp))
        if idx >= len(chartdata) or int(chartdata.timestamps[idx]) != candle.timestamp:
            return None
        return idx

    def draw_ema(
        self,
        pane: ChartPane,
        ema_values: pd.Series,
        period: int,
        periods: list[int],
    ) -> None:
        """
        The pane already holds only the candles that will be drawn, so the
        EMA gets clipped to that same span -- the old code did this by
        slicing the last `plot_n_candles` values off the dict.
        """
        if pane.chartdata is None or len(ema_values) == 0:
            return
        visible = ema_values.reindex(pane.chartdata.timestamps).dropna()
        if visible.empty:
            return
        pane.linear_plot(
            visible.index.to_numpy(),
            visible.to_numpy(),
            color=ema_colors(periods)[period],
            legend=f"EMA{period}",
        )

    def __call__(
        self,
        pane: ChartPane,
        signal: EmaTouchSignal,
        indicators: list[Indicator] = [],
        emas: dict[int, pd.Series] | None = None,
        periods: list[int] | None = None,
        *args,
        **kwargs,
    ):
        super().__call__(pane, signal, indicators)

        if emas is not None and signal.ema_period in emas:
            self.draw_ema(
                pane,
                emas[signal.ema_period],
                signal.ema_period,
                periods or list(emas),
            )

        color = (
            self.BULLISH_COLOR
            if signal.side is MarketSide.BULLISH
            else self.BEARISH_COLOR
        )
        # a down-break/BEARISH setup is touched by a candle reaching UP
        # from below (its high); an up-break/BULLISH setup is touched by
        # a candle reaching DOWN from above (its low).
        touch_source = (
            CandlesSource.Low
            if signal.side is MarketSide.BULLISH
            else CandlesSource.High
        )

        break_index = self._candle_index(pane, signal.break_candle)
        if break_index is not None:
            pane.mark_candle(
                break_index,
                source=CandlesSource.Close,
                color=self.BREAK_COLOR,
                legend="Break",
            )

        touch_index = self._candle_index(pane, signal.first_touch_candle)
        if touch_index is not None:
            pane.mark_candle(
                touch_index,
                source=touch_source,
                color=self.TOUCH_COLOR,
                legend="1st touch",
            )

        pane.draw_horizontal_line(
            signal.first_touch_candle.timestamp,
            signal.candle.timestamp,
            signal.ema_value,
            color=color,
        )

    def draw_all(
        self,
        pane: ChartPane,
        signals: list[EmaTouchSignal],
        indicators: list[Indicator] = [],
        emas: dict[int, pd.Series] | None = None,
        periods: list[int] | None = None,
    ) -> None:
        if not signals:
            return
        self(pane, signals[0], indicators, emas, periods)
        for signal in signals[1:]:
            self(pane, signal, [], emas, periods)


class EmaTouchFilter(Strategy):
    def __init__(
        self,
        ema_periods: list[int],
        min_candles_between_touches: int = 15,
        max_candles_between_touches: int = 200,
        reanchor_invalid_touch: bool = False,
        indicators: list[Indicator] = [],
        long_support_conditions=SupportCandlesPattern.RAW,
        short_support_conditions=SupportCandlesPattern.RAW,
        name="EmaTouch",
    ) -> None:
        """
        reanchor_invalid_touch: how an out-of-window touch is handled.
        The [min, max] window is measured from the break candle itself
        to the touch candle.
          False (default, "wait") -> an early touch (before
              min_candles_between_touches have passed since the break)
              is ignored and we keep waiting on the *same* break candle
              until the window closes; a late touch (after
              max_candles_between_touches has already elapsed since the
              break) means the window is over with no signal, so the
              setup resets to idle.
          True ("re_anchor") -> ANY out-of-window touch (early or late)
              itself becomes the new anchor (as if it were the break)
              and the window restarts counting from it.
        """
        super().__init__(
            name,
            EmaTouchPlotter(),
            long_support_conditions,
            short_support_conditions,
            indicators,
        )
        self.ema_periods = ema_periods
        self.min_candles_between_touches = min_candles_between_touches
        self.max_candles_between_touches = max_candles_between_touches
        self.reanchor_invalid_touch = reanchor_invalid_touch

        self.chart: Chart | None = None
        self.last_reported_timestamp: int | None = None
        self._emas: dict[int, pd.Series] = {}
        # last full walk's state per period, kept only so the plotter and
        # debugging can inspect it - check_signal() replays the whole given
        # window fresh every call (same convention as EmaPivotChochFilter)
        # and never relies on this being carried forward from a prior call.
        self.debug_last_call: dict = {}

    def export_config(self):
        conf_dict = super().export_config()
        conf_dict.update(
            {
                "ema_periods": self.ema_periods,
                "min_candles_between_touches": self.min_candles_between_touches,
                "max_candles_between_touches": self.max_candles_between_touches,
                "reanchor_invalid_touch": self.reanchor_invalid_touch,
            }
        )
        return conf_dict

    @property
    def emas(self) -> dict[int, pd.Series]:
        """The EMA series from the last check_signal call -- what the plotter draws."""
        return self._emas

    def check_signal(
        self,
        chartdata: ChartData,
        check_long: bool = True,
        check_short: bool = True,
        *args,
        **kwargs,
    ) -> EmaTouchSignal | None:
        self.chart = chartdata.chart
        if len(chartdata) < 3:
            return None
        last_candle = chartdata[-1]

        self._emas = {period: EMA(period).set(chartdata) for period in self.ema_periods}
        self.debug_last_call = {
            "candle_count": len(chartdata),
            "first_time": int(chartdata.timestamps[0]),
            "last_time": last_candle.timestamp,
        }

        best_signal: EmaTouchSignal | None = None
        for period in self.ema_periods:
            signal = self._walk_period(chartdata, period, last_candle)
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
            self.last_reported_timestamp is not None
            and best_signal.candle.timestamp <= self.last_reported_timestamp
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

        self.last_reported_timestamp = best_signal.candle.timestamp
        logger.info(f"Signal: {best_signal}")
        return best_signal

    def _walk_period(
        self, chartdata: ChartData, period: int, last_candle: Candle
    ) -> EmaTouchSignal | None:
        # aligned by index: the EMA is computed on exactly this chartdata,
        # so a NaN (warmup) is the only "no value here" case
        ema_series = self._emas[period].to_numpy()
        highs, lows, closes = chartdata.high, chartdata.low, chartdata.close

        phase = "idle"  # idle | waiting_touch
        direction: MarketSide | None = None
        break_candle: Candle | None = None
        break_index: int | None = None

        prev_close: float | None = None
        prev_ema: float | None = None
        result: EmaTouchSignal | None = None

        for i in range(len(chartdata)):
            ema_value = float(ema_series[i])
            if np.isnan(ema_value):
                prev_close, prev_ema = None, None
                continue

            close = float(closes[i])
            broke_down = (
                prev_close is not None
                and prev_ema is not None
                and prev_close >= prev_ema
                and close < ema_value
            )
            broke_up = (
                prev_close is not None
                and prev_ema is not None
                and prev_close <= prev_ema
                and close > ema_value
            )

            if phase == "waiting_touch":
                # a close back through the EMA against the setup is a BREAK
                # of the setup, not a retest - this is checked BEFORE the
                # touch test below, even when the same candle's wick also
                # reaches the EMA (that wick is incidental to the break).
                if (direction is MarketSide.BEARISH and broke_up) or (
                    direction is MarketSide.BULLISH and broke_down
                ):
                    phase, direction = "idle", None
                    break_candle = None
                    break_index = None
                elif lows[i] <= ema_value <= highs[i]:
                    assert break_index is not None
                    candle = chartdata.candle(i)
                    span = i - break_index
                    if (
                        self.min_candles_between_touches
                        <= span
                        <= self.max_candles_between_touches
                    ):
                        if candle.timestamp == last_candle.timestamp:
                            assert break_candle is not None
                            result = EmaTouchSignal(
                                self.chart,
                                candle,
                                direction,
                                self.name,
                                ema_period=period,
                                ema_value=ema_value,
                                break_candle=break_candle,
                                first_touch_candle=candle,
                            )
                        phase, direction = "idle", None
                        break_candle = None
                        break_index = None
                    elif span > self.max_candles_between_touches:
                        if self.reanchor_invalid_touch:
                            # too late: this touch itself becomes the new
                            # anchor, same direction, window restarts
                            break_candle, break_index = candle, i
                        else:
                            phase, direction = "idle", None
                            break_candle = None
                            break_index = None
                    elif self.reanchor_invalid_touch:
                        # too early: ignored unless reanchoring - keep
                        # waiting on the SAME direction, just re-anchored
                        # to this touch candle (a touch never flips the
                        # setup's direction; only a break-back does, and
                        # that was already handled above)
                        break_candle, break_index = candle, i
                    prev_close, prev_ema = close, ema_value
                    continue

            if phase == "idle":
                if broke_down:
                    phase, direction, break_candle, break_index = (
                        "waiting_touch",
                        MarketSide.BEARISH,
                        chartdata.candle(i),
                        i,
                    )
                elif broke_up:
                    phase, direction, break_candle, break_index = (
                        "waiting_touch",
                        MarketSide.BULLISH,
                        chartdata.candle(i),
                        i,
                    )
                prev_close, prev_ema = close, ema_value
                continue

            prev_close, prev_ema = close, ema_value

        return result

    def draw_all(self, pane: ChartPane, signals: list[EmaTouchSignal]) -> None:
        """Every signal on one pane -- backtest/debug view."""
        self.plotter.draw_all(
            pane, signals, self.indicators, self._emas, self.ema_periods
        )


class EmaTouchBot(TraderBot):
    """
    Single-chart bot -- everything but the figure comes from TraderBot.

    Same shape as OscillatorDiverBot: the only thing this strategy's
    plotter needs that the base does not supply is the EMA series it just
    computed, so `generate_figure` is the one override.
    """

    strategy: EmaTouchFilter  # type: ignore[assignment]

    def __init__(
        self,
        chart: Chart,
        agent: ExchangeAgent,
        strategy: EmaTouchFilter,
        trades_manager: TradesManager,
        bar_between_signals: int = 2,
        n_candle_check: int = 500,
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

    def generate_figure(  # type: ignore[override]
        self,
        chartdata: ChartData,
        signal: EmaTouchSignal,
        position: Position | None = None,
        *args,
        **kwargs,
    ) -> SingleChartFigure | None:
        if not self.consider_figure:
            return None
        figure = SingleChartFigure(chartdata, self.n_candle_check)
        self.strategy.plotter(
            figure.main_pane,
            signal,
            self.strategy.indicators,
            self.strategy.emas,
            self.strategy.ema_periods,
        )
        if position:
            PositionPlotter()(figure.main_pane, position)
        return figure
