from ChartModule.Indicators.models import SupportConditions, IndicatorCandleSource
from ChartModule.models import IndicatorBaseModel, Signal, ChartData, MarketSide
from TradingModule.Strategies.model import Strategy
from ChartModule.Indicators import TrendLine, Line
from ChartModule.plot import TwoChartPlot
from dataclasses import dataclass
from copy import copy
import logging

logger = logging.getLogger("Divergence")


@dataclass(slots=True)
class DivergenceSignal(Signal):
    base_line: Line
    second_line: Line


class Divergence(Strategy):
    def __init__(
        self,
        min_step: int,
        max_step: int,
        confirmation_indicators: list[IndicatorBaseModel],
        long_support_conditions=SupportConditions.RED_GREEN,
        short_support_conditions=SupportConditions.GREEN_RED,
        name="Divergence",
        inverse_diver_long: bool = False,
        inverse_diver_short: bool = False,
        long_second_line_validation: bool = True,
        short_second_line_validation: bool = True,
    ) -> None:
        super().__init__(
            name,
            confirmation_indicators,
            long_support_conditions,
            short_support_conditions,
        )
        self.min_step = min_step
        self.max_step = max_step
        self.inverse_diver_long = inverse_diver_long
        self.inverse_diver_short = inverse_diver_short
        self.long_second_line_validation = long_second_line_validation
        self.short_second_line_validation = short_second_line_validation

    @classmethod
    def find_divergence(
        cls,
        trendline: TrendLine,
        base_chartdata: ChartData,
        second_chartdata: ChartData,
        inverse: bool = False,
        second_line_validation: bool = True,
    ) -> tuple[Line, Line] | None:
        direction = -1 if inverse else 1
        trendline.set(base_chartdata.candles)
        all_lines = copy(trendline.values)  # type: list[Line]
        for base_chart_line in all_lines:
            start_candle_index = base_chartdata.index(base_chart_line.start_candle)
            end_candle_index = base_chartdata.index(base_chart_line.end_candle)
            if second_line_validation:
                second_chart_line = trendline.valid_trendline(
                    second_chartdata.candles, start_candle_index, end_candle_index
                )
            else:
                second_chart_line = Line(
                    trendline.source,
                    second_chartdata[start_candle_index],
                    second_chartdata[end_candle_index],
                )

            if second_chart_line is None:
                continue

            if (
                base_chart_line.slope * direction > 0
                and second_chart_line.slope * direction < 0
            ):
                return base_chart_line, second_chart_line

    def long_signal(self, base_chartdata: ChartData, second_chartdata):
        if not self.long_support_conditions.check(base_chartdata.candles):
            return None
        res = self.find_divergence(
            TrendLine(
                IndicatorCandleSource.Low,
                self.min_step,
                self.max_step,
                support_conditions=self.long_support_conditions,
            ),
            base_chartdata,
            second_chartdata,
            self.inverse_diver_long,
            self.long_second_line_validation,
        )
        if res is None:
            return None
        base_line, second_line = res
        signal = DivergenceSignal(
            base_chartdata.chart,
            base_line.end_candle,
            MarketSide.BULLISH,
            self.name,
            base_line,
            second_line,
        )
        return signal

    def short_signal(self, base_chartdata: ChartData, second_chartdata):
        if not self.long_support_conditions.check(base_chartdata.candles):
            return None
        res = self.find_divergence(
            TrendLine(
                IndicatorCandleSource.High,
                self.min_step,
                self.max_step,
                support_conditions=self.short_support_conditions,
            ),
            base_chartdata,
            second_chartdata,
            self.inverse_diver_short,
            self.short_second_line_validation,
        )
        if res is None:
            return None
        base_line, second_line = res
        signal = DivergenceSignal(
            base_chartdata.chart,
            base_line.end_candle,
            MarketSide.BEARISH,
            self.name,
            base_line,
            second_line,
        )
        return signal

    def check_signal(
        self,
        chartdata: ChartData,
        second_chartdata: ChartData,
        check_long: bool = True,
        check_short: bool = True,
    ) -> Signal | None:
        long_signal = None
        short_signal = None

        confirmations = self.get_indicators_confirmation(chartdata)

        if check_long and MarketSide.BEARISH not in confirmations:
            long_signal = self.long_signal(chartdata, second_chartdata)

        if check_short and MarketSide.BULLISH not in confirmations:
            short_signal = self.short_signal(chartdata, second_chartdata)

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

    def plot(
        self, plot: TwoChartPlot, signal: DivergenceSignal, draw_indicators: bool = True
    ):
        plot.base_plot.mark_signal(signal)
        plot.base_plot.draw_straight_line(
            signal.base_line.start_candle,
            signal.base_line.end_candle,
            signal.base_line.source,
        )
        plot.second_plot.draw_straight_line(
            signal.second_line.start_candle,
            signal.second_line.end_candle,
            signal.second_line.source,
        )
        if draw_indicators:
            for indicator in self.confirmation_indicators:
                indicator.plot(plot.base_plot)
