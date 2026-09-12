from ChartModule.models import (
    Candle,
    Signal,
    ChartData,
    MarketSide,
    CandlesSource,
)
from ChartModule.Indicators import (
    IndicatorBaseModel,
    Line,
    SupportCandleConditions,
)
from ChartModule.plot import ChartWithOscillatorPlot
from TraderBot.reporter import TelegramReporter
from TraderBot.trader_bot import TraderBot, Position
from TraderBot.models import Strategy
from dataclasses import dataclass
from typing import Literal
from copy import copy
import numpy as np
import logging


logger = logging.getLogger("DoubleDivergence")


@dataclass(slots=True, frozen=True)
class OscillatorDiverSignal(Signal):
    main_chart_line: Line
    other_chart_line_prices: tuple[float, float]


class OscillatorDivergence(Strategy):
    def __init__(
        self,
        oscillator_indicator,
        min_step: int,
        max_step: int,
        confirmation_indicators: list[IndicatorBaseModel] = [],
        long_support_conditions=SupportCandleConditions.RED_GREEN,
        short_support_conditions=SupportCandleConditions.GREEN_RED,
        name="OscillatorDivergence",
        inverse_diver_long: bool = False,
        inverse_diver_short: bool = False,
        long_other_chart_line_validation: bool = True,
        short_other_chart_line_validation: bool = True,
        body_candle: bool = False,
        ignore_shadow_cross: bool = False,
    ) -> None:
        super().__init__(
            name,
            long_support_conditions,
            short_support_conditions,
            confirmation_indicators,
        )
        self.oscillator_indicator = oscillator_indicator
        self.min_step = min_step
        self.max_step = max_step
        self.inverse_diver_long = inverse_diver_long
        self.inverse_diver_short = inverse_diver_short
        self.long_other_chart_line_validation = long_other_chart_line_validation
        self.short_other_chart_line_validation = short_other_chart_line_validation
        self.body_candle = body_candle
        self.ignore_shadow_cross = ignore_shadow_cross

    def export_config(self):
        conf_dict = super().export_config()
        conf_dict.update(self.oscillator_indicator.export_configs())
        conf_dict.update(
            {
                "min_step": self.min_step,
                "max_step": self.max_step,
                "inverse_diver_long": self.inverse_diver_long,
                "inverse_diver_short": self.inverse_diver_short,
                "long_other_chart_line_validation": self.long_other_chart_line_validation,
                "short_other_chart_line_validation": self.short_other_chart_line_validation,
                "body_candle": self.body_candle,
            }
        )
        return conf_dict

    def validate_line(
        self,
        candles_body_values,
        line_body_values,
        candles_shadow_values,
        line_shadow_values,
        start_candle: Candle,
        end_candle: Candle,
        direction: Literal[1, -1],
        shadow_slope: float,
        body_slope: float,
    ):
        shadow_line = None
        body_line = None
        if self.ignore_shadow_cross:
            shadow_line = np.all(
                (candles_body_values - line_shadow_values) * direction >= 0
            )
        else:
            shadow_line = np.all(
                (candles_shadow_values - line_shadow_values) * direction >= 0
            )
        if shadow_line:
            line = Line(
                CandlesSource.Low if direction == 1 else CandlesSource.High,
                start_candle,
                end_candle,
            )
            line.slope = shadow_slope
            return line

        if self.body_candle:
            body_line = np.all(
                (candles_body_values - line_body_values) * direction >= 0
            )
        if body_line:
            line = Line(
                CandlesSource.Bottom if direction == 1 else CandlesSource.Top,
                start_candle,
                end_candle,
            )
            line.slope = body_slope
            return line
        return None

    def find_divergence(
        self, chartdata: ChartData, oscillator_data: dict, shift_candle: bool = True
    ):
        if shift_candle:
            oscillator_list = list(oscillator_data.values())[:-1]
            last_index = len(chartdata) - 2

        else:
            oscillator_list = list(oscillator_data.values())
            last_index = len(chartdata) - 1

        oscillator_array = np.array(oscillator_list)
        last_candle = chartdata[last_index]
        long_diver_factor = -1 if self.inverse_diver_long else 1
        short_diver_factor = 1 if self.inverse_diver_short else -1

        last_candle_bottom = last_candle.body_bottom
        last_candle_top = last_candle.body_top
        last_candle_low = last_candle.low
        last_candle_high = last_candle.high

        oscillator_last_value = oscillator_list[-1]

        indices = np.arange(self.max_step + 1, dtype=np.float64)
        candles_bottom_values = np.empty(self.max_step + 1, dtype=np.float64)
        candles_top_values = np.empty(self.max_step + 1, dtype=np.float64)
        candles_low_values = np.empty(self.max_step + 1, dtype=np.float64)
        candles_high_values = np.empty(self.max_step + 1, dtype=np.float64)

        count = 0

        start = last_index
        stop = max(-1, last_index - self.max_step)

        long_signal = None
        short_signal = None
        long_support_condition_last = self.long_support_conditions.check(chartdata)
        short_support_condition_last = self.short_support_conditions.check(chartdata)

        for candle_index in range(start, stop, -1):
            candle = chartdata[candle_index]

            long_support_condition_start = self.long_support_conditions.check(
                chartdata.subdata(start_index=0, end_index=candle_index + 2)
            )
            short_support_condition_start = self.short_support_conditions.check(
                chartdata.subdata(start_index=0, end_index=candle_index + 2)
            )

            start_candle_bottom = candle.body_bottom
            start_candle_top = candle.body_top
            start_candle_low = candle.low
            start_candle_high = candle.high

            count += 1
            candles_bottom_values[-count] = start_candle_bottom
            candles_top_values[-count] = start_candle_top
            candles_low_values[-count] = start_candle_low
            candles_high_values[-count] = start_candle_high

            step = last_index - candle_index

            if step < self.min_step:
                continue
            line_indices = indices[-count:] - indices[-count]

            bottom_slope = (last_candle_bottom - start_candle_bottom) / step
            top_slope = (last_candle_top - start_candle_top) / step
            low_slope = (last_candle_low - start_candle_low) / step
            high_slope = (last_candle_high - start_candle_high) / step

            bottom_line = start_candle_bottom + line_indices * bottom_slope
            top_line = start_candle_top + line_indices * top_slope
            low_line = start_candle_low + line_indices * low_slope
            high_line = start_candle_high + line_indices * high_slope

            # Long Condition ----
            long_base_condition = (
                long_support_condition_last
                and long_support_condition_start
                and long_signal is None
            )
            main_line = None
            if long_base_condition:
                main_line = self.validate_line(
                    candles_bottom_values[-count:],
                    bottom_line,
                    candles_low_values[-count:],
                    low_line,
                    candle,
                    last_candle,
                    1,
                    low_slope,
                    bottom_slope,
                )
            if main_line:
                oscillator_start_value = oscillator_list[-count]
                oscillator_slope = (
                    oscillator_last_value - oscillator_start_value
                ) / step
                if (
                    oscillator_slope * long_diver_factor > 0
                    and main_line.slope * long_diver_factor < 0
                ):
                    oscillator_line_values = (
                        oscillator_start_value + line_indices * oscillator_slope
                    )
                    current_oscillator_values = oscillator_array[-count:]

                    if not self.long_other_chart_line_validation or np.all(
                        (current_oscillator_values - oscillator_line_values) >= 0
                    ):
                        long_signal = OscillatorDiverSignal(
                            chartdata.chart,
                            chartdata[-1],
                            MarketSide.BULLISH,
                            self.name,
                            main_line,
                            (oscillator_start_value, oscillator_last_value),
                        )
            # Short Condition ----
            short_base_condition = (
                short_support_condition_last
                and short_support_condition_start
                and short_signal is None
            )
            main_line = None
            if short_base_condition:
                main_line = self.validate_line(
                    candles_top_values[-count:],
                    top_line,
                    candles_high_values[-count:],
                    high_line,
                    candle,
                    last_candle,
                    -1,
                    high_slope,
                    top_slope,
                )
            if main_line:
                oscillator_start_value = oscillator_list[-count]
                oscillator_slope = (
                    oscillator_last_value - oscillator_start_value
                ) / step
                if (
                    oscillator_slope * short_diver_factor > 0
                    and main_line.slope * short_diver_factor < 0
                ):
                    oscillator_line_values = (
                        oscillator_start_value + line_indices * oscillator_slope
                    )
                    current_oscillator_values = oscillator_array[-count:]

                    if not self.short_other_chart_line_validation or np.all(
                        (current_oscillator_values - oscillator_line_values) <= 0
                    ):
                        short_signal = OscillatorDiverSignal(
                            chartdata.chart,
                            chartdata[-1],
                            MarketSide.BEARISH,
                            self.name,
                            main_line,
                            (oscillator_start_value, oscillator_last_value),
                        )
        return long_signal, short_signal

    def check_signal(
        self,
        chartdata: ChartData,
        check_long: bool = True,
        check_short: bool = True,
        shift_candle: bool = True,
    ) -> OscillatorDiverSignal | None:
        long_signal = None
        short_signal = None

        # confirmations = self.get_indicators_confirmation(chartdata)
        self.oscillator_indicator.set(chartdata)

        long_signal, short_signal = self.find_divergence(
            chartdata, self.oscillator_indicator.data, shift_candle
        )

        if long_signal and short_signal:
            logger.warning("long and short signal on same candle!")
            return None

        if check_short and short_signal:
            return short_signal

        if check_long and long_signal:
            return long_signal

        return None

    def report(self):
        return ""

    def generate_dummy_signal(
        self,
        chartdata: ChartData,
        side: Literal[MarketSide.BEARISH, MarketSide.BULLISH] = MarketSide.BEARISH,
    ):
        self.oscillator_indicator.set(chartdata)
        if side == MarketSide.BULLISH:
            line_candlesource = (
                CandlesSource.Bottom if self.body_candle else CandlesSource.Low
            )
        else:  # side == MarketSide.BEARISH
            line_candlesource = (
                CandlesSource.Top if self.body_candle else CandlesSource.High
            )

        signal = OscillatorDiverSignal(
            chartdata.chart,
            chartdata[-1],
            side,
            "dummy_oscillator_signal",
            Line(
                line_candlesource,
                chartdata[-5],
                chartdata[-2],
            ),
            (
                self.oscillator_indicator.data[chartdata[-5].timestamp],
                self.oscillator_indicator.data[chartdata[-2].timestamp],
            ),
        )
        return signal

    def draw(
        self,
        plot: ChartWithOscillatorPlot,
        signal: OscillatorDiverSignal,
        draw_indicators: bool = True,
        mark_signal: bool = True,
    ):
        if mark_signal:
            plot.base_plot.mark_signal(signal)
        plot.base_plot.draw_straight_line(
            signal.main_chart_line.start_candle,
            signal.main_chart_line.end_candle,
            signal.main_chart_line.source,
        )
        plot.base_plot.draw_straight_line(
            signal.main_chart_line.start_candle,
            signal.main_chart_line.end_candle,
            signal.main_chart_line.source,
            ax=plot.oscillator_ax,
            prices=(
                self.oscillator_indicator.data[
                    int(signal.main_chart_line.start_candle.timestamp)
                ],
                self.oscillator_indicator.data[
                    int(signal.main_chart_line.end_candle.timestamp)
                ],
            ),
        )
        if draw_indicators and self.confirmation_indicators:
            for indicator in self.confirmation_indicators:
                indicator.plot(plot.base_plot)


@dataclass(kw_only=True)
class OscillatorDiverConfig(TraderBot):
    strategy: OscillatorDivergence  # type: ignore[override]

    async def find_signal(
        self, chartdata: ChartData
    ) -> None | tuple[OscillatorDiverSignal, Position] | OscillatorDiverSignal:
        signal = self.strategy.check_signal(
            chartdata, self.long_signal, self.short_signal
        )
        if signal is None:
            return None
        logger.info(f"Oscillator Divergence Signal:{signal}")

        plot = None
        if self.send_signal_msg:
            self.strategy.oscillator_indicator.set(candles=chartdata)
            plot = ChartWithOscillatorPlot(
                chartdata, self.strategy.oscillator_indicator.data
            )
            self.strategy.draw(plot, signal, draw_indicators=True)
            self.strategy.oscillator_indicator.plot(plot, plot.oscillator_ax)

        if not self.consider_position:
            if self.send_signal_msg:
                await TelegramReporter().new_signal(signal, plot)
            return signal

        entry_source = (
            signal.main_chart_line.end_candle.high
            if signal.side is MarketSide.BEARISH
            else signal.main_chart_line.end_candle.low
        )  # TODO: change entry source to agent.get_current_tick

        position = await self.position_generator.generate(
            signal, sl_base_price=entry_source, plot=plot
        )
        if not position:
            return None
        return signal, position

    async def task(self):
        chart_data = self.get_chartdata()

        # TODO: add a param for removing last candle or not (current candle)
        sub_chart_data = copy(chart_data)
        sub_chart_data = sub_chart_data.subdata()

        res = await self.find_signal(sub_chart_data)
        if res is None:
            return self.give_delay(chart_data[-1])
        if isinstance(res, tuple):
            signal, position = res
        else:
            signal = res
            position = None
        return self.give_delay(chart_data[-1], jump=True), signal, position

    async def backtest(  # type: ignore
        self,
        n_bar=500,
        len_sub_data=100,
        show_image=True,
    ):
        self.send_signal_msg = False
        all_signals: list[OscillatorDiverSignal] = []

        jump = 0
        chartdata = self.get_chartdata(n_bar)
        for i in range(len_sub_data, len(chartdata) - 2):
            sub_chart_data = chartdata.subdata(start_index=0, end_index=i)

            if jump > 0:
                jump -= 1
                continue
            signal = await self.find_signal(sub_chart_data)
            if signal is None:
                continue
            jump = self.bar_between_signals
            all_signals.append(signal)  # type: ignore

        plot = ChartWithOscillatorPlot(
            chartdata, self.strategy.oscillator_indicator.data, len(chartdata)
        )
        self.strategy.oscillator_indicator.plot(plot, plot.oscillator_ax)
        if not all_signals:
            if show_image:
                plot.show()
            return [], plot
        self.strategy.draw(plot, all_signals[0], draw_indicators=True)  # type: ignore
        for signal in all_signals[1:]:
            self.strategy.draw(plot, signal, draw_indicators=False)  # type: ignore
        if show_image:
            plot.show()
        return all_signals, plot
