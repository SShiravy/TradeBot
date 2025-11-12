from ChartModule.Indicators.models import SupportConditions, IndicatorCandleSource
from ChartModule.Indicators import TrendLine, Line
from ChartModule.models import IndicatorBaseModel, Signal, ChartData, MarketSide
from TradingModule.Strategies.model import Strategy
from copy import copy
import logging

logger = logging.getLogger("Divergence")


class Divergence(Strategy):
    def __init__(
        self,
        min_step: int,
        max_step: int,
        name: str,
        confirmation_indicators: list[IndicatorBaseModel],
        long_support_conditions=SupportConditions.RED_GREEN,
        short_support_conditions=SupportConditions.GREEN_RED,
        plot=True,
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
            plot=plot,
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
        signal = Signal(
            base_chartdata.chart,
            base_line.end_candle,
            MarketSide.BULLISH,
            source=self.name,
        )
        return signal, base_line, second_line

    def short_signal(self, base_chartdata: ChartData, second_chartdata):
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
        signal = Signal(
            base_chartdata.chart,
            base_line.end_candle,
            MarketSide.BEARISH,
            source=self.name,
        )
        return signal, base_line, second_line

    def check_signal(
        self,
        chartdata: ChartData,
        second_chartdata: ChartData,
        check_long: bool = True,
        check_short: bool = True,
    ) -> Signal | None:
        long_res = None
        short_res = None

        confirmations = self.get_indicators_confirmation(chartdata)

        if (
            check_long
            and self.long_support_conditions.check(chartdata.candles)
            and MarketSide.BEARISH not in confirmations
        ):
            long_res = self.long_signal(chartdata, second_chartdata)

        if (
            check_short
            and self.long_support_conditions.check(chartdata.candles)
            and MarketSide.BULLISH not in confirmations
        ):
            short_res = self.short_signal(chartdata, second_chartdata)

        if long_res and short_res:
            logger.warning("long and short signal in same time!")
            return None

        if short_res:
            pass

        if long_res:
            pass

        return None

    def report(self):
        return ""

    def plot(self):
        pass
