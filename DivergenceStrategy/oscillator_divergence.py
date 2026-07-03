from BacktestModule.dummy_models import DummyAgent
from ChartModule.models import (
    Chart,
    Signal,
    ChartData,
    MarketSide,
    CandlesSource,
)
from ChartModule.Indicators import (
    IndicatorBaseModel,
    Line,
    RSI,
    SupportCandleConditions,
)
from ChartModule.plot import ChartWithOscillatorPlot
from TradingModule.trader_bot import TradeConfig, commands, Position
from TradingModule.models import Strategy
from dataclasses import dataclass, field
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
        oscillator_indicator: RSI,
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

    def find_divergence(
        self,
        chartdata: ChartData,
        oscillator_data: dict,
    ):
        oscillator_list = list(oscillator_data.values())
        oscillator_array = np.array(oscillator_list)
        last_index = len(chartdata.candles) - 1
        last_candle = chartdata.candles[last_index]
        long_diver_factor = -1 if self.inverse_diver_long else 1
        short_diver_factor = -1 if self.inverse_diver_short else 1

        if self.body_candle:
            long_candle_source = CandlesSource.Bottom
            short_candle_source = CandlesSource.Top
        else:
            long_candle_source = CandlesSource.Low
            short_candle_source = CandlesSource.High

        long_last_value = long_candle_source(last_candle)
        short_last_value = short_candle_source(last_candle)
        oscillator_last_value = oscillator_list[-1]

        indices = np.arange(self.max_step + 1, dtype=np.float64)
        long_source_values = np.empty(self.max_step + 1, dtype=np.float64)
        short_source_values = np.empty(self.max_step + 1, dtype=np.float64)

        count = 0

        start = last_index
        stop = max(-1, last_index - self.max_step)

        long_signal = None
        short_signal = None

        for candle_index in range(start, stop, -1):
            candle = chartdata.candles[candle_index]

            # long_support_condition_result  = self.long_support_conditions.check(chartdata.candles[: candle_index + 2])

            long_start_value = long_candle_source(candle)
            short_start_value = short_candle_source(candle)
            count += 1

            long_source_values[-count] = long_start_value
            short_source_values[-count] = long_start_value

            step = last_index - candle_index

            if step < self.min_step:
                continue
            line_indices = indices[-count:] - indices[-count]

            long_slope = (long_last_value - long_start_value) / step
            short_slope = (short_last_value - short_start_value) / step

            long_line_values = long_start_value + line_indices * long_slope

            short_line_values = short_start_value + line_indices * short_slope

            if np.all((long_source_values[-count:] - long_line_values) >= 0):
                oscillator_start_value = oscillator_list[-count]
                oscillator_slope = (
                    oscillator_last_value - oscillator_start_value
                ) / step
                if (
                    oscillator_slope * long_diver_factor > 0
                    and long_slope * long_diver_factor < 0
                ):
                    oscillator_line_values = (
                        oscillator_start_value + line_indices * oscillator_slope
                    )
                    current_oscillator_values = oscillator_array[-count:]

                    if self.long_other_chart_line_validation == False or np.all(
                        (current_oscillator_values - oscillator_line_values) >= 0
                    ):
                        main_chart_line = Line(long_candle_source, candle, last_candle)
                        long_signal = OscillatorDiverSignal(
                            chartdata.chart,
                            last_candle,
                            MarketSide.BULLISH,
                            self.name,
                            main_chart_line,
                            (oscillator_start_value, oscillator_last_value),
                        )

        return long_signal, short_signal

    def check_signal(
        self,
        chartdata: ChartData,
        check_long: bool = True,
        check_short: bool = True,
    ) -> OscillatorDiverSignal | None:
        long_signal = None
        short_signal = None

        # confirmations = self.get_indicators_confirmation(chartdata)
        self.oscillator_indicator.set(chartdata.candles)

        long_signal, short_signal = self.find_divergence(
            chartdata, self.oscillator_indicator.data
        )

        if long_signal and short_signal:
            logger.warning("long and short signal in same time!")
            return None

        if short_signal:
            logger.info(f"Short Signal:{short_signal}")
            return short_signal

        if long_signal:
            logger.info(f"Long Signal:{long_signal}")
            return long_signal

        return None

    def report(self):
        return ""

    def generate_dummy_signal(
        self,
        chartdata: ChartData,
        side: Literal[MarketSide.BEARISH, MarketSide.BULLISH] = MarketSide.BEARISH,
    ):
        self.oscillator_indicator.set(chartdata.candles)
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
            chartdata.candles[-1],
            side,
            "dummy_oscillator_signal",
            Line(
                line_candlesource,
                chartdata.candles[-5],
                chartdata.candles[-2],
            ),
            (
                self.oscillator_indicator.data[chartdata.candles[-5].timestamp],
                self.oscillator_indicator.data[chartdata.candles[-2].timestamp],
            ),
        )
        return signal

    def draw(
        self,
        plot: ChartWithOscillatorPlot,
        signal: OscillatorDiverSignal,
        draw_indicators: bool = True,
    ):
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
class OscillatorDiverConfig(TradeConfig):
    strategy: OscillatorDivergence  # type: ignore[override]

    async def find_signal(
        self, chartdata: ChartData, consider_position: bool = True
    ) -> None | tuple[OscillatorDiverSignal, Position] | OscillatorDiverSignal:
        signal = self.strategy.check_signal(
            chartdata, self.long_signal, self.short_signal
        )
        if signal is None:
            return None

        entry_source = (
            signal.main_chart_line.end_candle.high
            if signal.side is MarketSide.BEARISH
            else signal.main_chart_line.end_candle.low
        )
        # TODO: change entry source to agent.get_current_tick
        plot = None
        if self.send_signal:
            plot = ChartWithOscillatorPlot(
                chartdata, self.strategy.oscillator_indicator.data
            )
            self.strategy.draw(plot, signal, draw_indicators=True)
            self.strategy.oscillator_indicator.plot(plot, plot.oscillator_ax)

        if not consider_position:
            return signal
        position = await self.position_handler.generate_position(
            signal, sl_base_price=entry_source, plot=plot
        )
        if not position:
            return None
        return signal, position

    async def task(self):
        chart_data = self.get_chartdata()

        # TODO: add a param for removing last candle or not (current candle)
        sub_chart_data = copy(chart_data)
        sub_chart_data.candles = sub_chart_data.candles[:-1]

        res = await self.find_signal(sub_chart_data, consider_position=True)
        if res is None:
            return self.give_delay(chart_data[-1])

        signal, position = res  # type: ignore

        return self.give_delay(chart_data[-1], jump=True), signal, position

    async def backtest(  # type: ignore
        self,
        n_bar=500,
        len_sub_data=100,
        show_image=True,
    ):
        self.send_signal = False
        all_signals: list[OscillatorDiverSignal] = []

        jump = 0
        chartdata = self.get_chartdata(n_bar)
        for i in range(len_sub_data, len(chartdata) - 2):
            sub_chart_data = ChartData(chartdata.chart, chartdata[:i])

            if jump > 0:
                jump -= 1
                continue
            signal = await self.find_signal(sub_chart_data, consider_position=False)
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
