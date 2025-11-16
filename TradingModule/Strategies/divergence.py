from ChartModule.models import (
    Chart,
    IndicatorBaseModel,
    Signal,
    ChartData,
    MarketSide,
    IndicatorCandleSource,
)
from ChartModule.Indicators import TrendLine, Line, SupportConditions
from ChartModule.plot import TwoChartPlot
from TradingModule import TradeConfig, OrderSide, commands, Position
from TradingModule.Strategies.model import Strategy
from dataclasses import dataclass
from copy import copy
import logging

logger = logging.getLogger("Divergence")


@dataclass(slots=True, frozen=True)
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

        trendline.set(base_chartdata.candles[:-1])
        all_lines = copy(trendline.values)  # type: list[Line]
        for base_chart_line in all_lines:
            start_candle_index = base_chartdata.index(base_chart_line.start_candle)
            end_candle_index = base_chartdata.index(base_chart_line.end_candle)
            if second_line_validation:
                second_chart_line = trendline.valid_trendline(
                    second_chartdata.candles, start_candle_index, end_candle_index
                )
                if second_chart_line is None:
                    continue
            else:
                second_chart_line = Line(
                    trendline.source,
                    second_chartdata[start_candle_index],
                    second_chartdata[end_candle_index],
                )

            if (
                base_chart_line.slope * direction < 0
                and second_chart_line.slope * direction > 0
            ):
                return base_chart_line, second_chart_line

    def check_long_signal(self, base_chartdata: ChartData, second_chartdata: ChartData):
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
            base_chartdata[-1],
            MarketSide.BULLISH,
            self.name,
            base_line,
            second_line,
        )
        return signal

    def check_short_signal(
        self, base_chartdata: ChartData, second_chartdata: ChartData
    ):
        if not self.short_support_conditions.check(base_chartdata.candles):
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
            not self.inverse_diver_short,
            self.short_second_line_validation,
        )
        if res is None:
            return None
        base_line, second_line = res
        signal = DivergenceSignal(
            base_chartdata.chart,
            base_chartdata[-1],
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
    ) -> DivergenceSignal | None:
        long_signal = None
        short_signal = None

        confirmations = self.get_indicators_confirmation(chartdata)

        if check_long and MarketSide.BEARISH not in confirmations:
            long_signal = self.check_long_signal(chartdata, second_chartdata)

        if check_short and MarketSide.BULLISH not in confirmations:
            short_signal = self.check_short_signal(chartdata, second_chartdata)

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

    def draw(
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
        if draw_indicators and self.confirmation_indicators:
            for indicator in self.confirmation_indicators:
                indicator.plot(plot.base_plot)


@dataclass(kw_only=True)
class DivergenceTradeConfig(TradeConfig):
    second_chart: Chart
    strategy: Divergence  # type: ignore[override]

    def get_chartdata(self) -> tuple[ChartData, ChartData]:  # type: ignore[override]
        base_chartdata = self.agent.get_chartdata(self.chart, self.n_candle_check)
        second_chartdata = self.agent.get_chartdata(
            self.second_chart, self.n_candle_check
        )

        if base_chartdata is None or second_chartdata is None:
            raise ValueError(f"chart data is None from {self.agent.__class__.__name__}")
        if self.heikingashi_chartdata:
            base_chartdata = base_chartdata.give_heikingashi_chartdata()
            second_chartdata = second_chartdata.give_heikingashi_chartdata()
        return base_chartdata, second_chartdata

    def find_signal(
        self, chartdata: ChartData, second_chartdata: ChartData, *args, **kwargs
    ) -> None | tuple[DivergenceSignal, Position]:
        signal = self.strategy.check_signal(
            chartdata, second_chartdata, self.long_signal, self.short_signal
        )
        if signal is None:
            return None

        position = self.position_handler.generate_position(signal)

        if (self.long_trade and position.side is OrderSide.BUY) or (
            self.short_trade and position.side is OrderSide.SELL
        ):
            command = commands.OpenPosition(position, self.agent)
            command.execute()

        return signal, position

    async def task(self, telegram_bot):
        base_chartdata, second_chartdata = self.get_chartdata()

        base_data = copy(base_chartdata)
        base_data.candles = base_data.candles[:-1]

        second_data = copy(second_chartdata)
        second_data = second_data[:-1]

        res = self.find_signal(base_data, second_data)
        if res is None:
            return self.give_delay(base_data[-1])

        signal, position = res

        if self.send_signal:
            plot = TwoChartPlot(base_data, second_data)
            self.strategy.draw(plot, signal, draw_indicators=True)
            position.draw(plot.base_plot)
            img_path = plot.save_image()
            await telegram_bot.send_photo_to_channel(
                img_path, self.msg_generator(position)
            )

        return self.give_delay(signal.candle, jump=True), signal, position
