from ChartModule.models import (
    Chart,
    Signal,
    ChartData,
    MarketSide,
    CandlesSource,
)
from ChartModule.Indicators import (
    IndicatorBaseModel,
    LineFinder,
    Line,
    SupportCandleConditions,
)
from ChartModule.plot import DoubleChartPlot
from TradingModule.reporter import TelegramReporter
from TradingModule.trader_bot import TradeConfig, Position
from TradingModule.models import Strategy
from dataclasses import dataclass, field
from typing import Literal
from copy import copy
import logging


logger = logging.getLogger("Divergence")


@dataclass(slots=True, frozen=True)
class DivergenceSignal(Signal):
    main_chart_line: Line
    other_chart_line: Line


class Divergence(Strategy):
    def __init__(
        self,
        min_step: int,
        max_step: int,
        confirmation_indicators: list[IndicatorBaseModel] = [],
        long_support_conditions=SupportCandleConditions.RED_GREEN,
        short_support_conditions=SupportCandleConditions.GREEN_RED,
        name="Divergence",
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
        self.min_step = min_step
        self.max_step = max_step
        self.inverse_diver_long = inverse_diver_long
        self.inverse_diver_short = inverse_diver_short
        self.long_other_chart_line_validation = long_other_chart_line_validation
        self.short_other_chart_line_validation = short_other_chart_line_validation
        self.body_candle = body_candle

    def export_config(self):
        conf_dict = super().export_config()
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

    @classmethod
    def find_divergence(
        cls,
        trendline: LineFinder,
        base_chartdata: ChartData,
        second_chartdata: ChartData,
        inverse: bool = False,
        other_chart_line_validation: bool = True,
    ) -> tuple[Line, Line] | None:
        direction = -1 if inverse else 1

        trendline.set(base_chartdata.candles[:-1])
        all_lines = trendline.data  # type: list[Line]
        for base_chart_line in all_lines:
            start_candle_index = base_chartdata.candle_index(
                base_chart_line.start_candle
            )
            end_candle_index = base_chartdata.candle_index(base_chart_line.end_candle)
            if other_chart_line_validation:
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
            LineFinder(
                CandlesSource.Bottom if self.body_candle else CandlesSource.Low,
                self.min_step,
                self.max_step,
                support_conditions=self.long_support_conditions,
            ),
            base_chartdata,
            second_chartdata,
            self.inverse_diver_long,
            self.long_other_chart_line_validation,
        )
        if res is None:
            return None
        main_chart_line, other_chart_line = res
        signal = DivergenceSignal(
            base_chartdata.chart,
            base_chartdata[-1],
            MarketSide.BULLISH,
            self.name,
            main_chart_line,
            other_chart_line,
        )
        return signal

    def check_short_signal(
        self, base_chartdata: ChartData, second_chartdata: ChartData
    ):
        if not self.short_support_conditions.check(base_chartdata.candles):
            return None
        res = self.find_divergence(
            LineFinder(
                CandlesSource.Top if self.body_candle else CandlesSource.High,
                self.min_step,
                self.max_step,
                support_conditions=self.short_support_conditions,
            ),
            base_chartdata,
            second_chartdata,
            not self.inverse_diver_short,
            self.short_other_chart_line_validation,
        )
        if res is None:
            return None
        main_chart_line, other_chart_line = res
        signal = DivergenceSignal(
            base_chartdata.chart,
            base_chartdata[-1],
            MarketSide.BEARISH,
            self.name,
            main_chart_line,
            other_chart_line,
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
            return short_signal

        if long_signal:
            return long_signal

        return None

    def report(self):
        return ""

    def generate_dummy_signal(
        self,
        base_chartdata: ChartData,
        second_chartdata: ChartData,
        side: Literal[MarketSide.BEARISH, MarketSide.BULLISH] = MarketSide.BEARISH,
    ):
        if side == MarketSide.BULLISH:
            line_candlesource = (
                CandlesSource.Bottom if self.body_candle else CandlesSource.Low
            )
        else:  # side == MarketSide.BEARISH
            line_candlesource = (
                CandlesSource.Top if self.body_candle else CandlesSource.High
            )

        signal = DivergenceSignal(
            base_chartdata.chart,
            base_chartdata.candles[-1],
            side,
            "dummy_signal",
            main_chart_line=Line(
                line_candlesource,
                base_chartdata.candles[-5],
                base_chartdata.candles[-2],
            ),
            other_chart_line=Line(
                line_candlesource,
                second_chartdata.candles[-5],
                second_chartdata.candles[-2],
            ),
        )
        return signal

    def draw(
        self,
        plot: DoubleChartPlot,
        signal: DivergenceSignal,
        draw_indicators: bool = True,
    ):
        plot.base_plot.mark_signal(signal)
        plot.base_plot.draw_straight_line(
            signal.main_chart_line.start_candle,
            signal.main_chart_line.end_candle,
            signal.main_chart_line.source,
        )
        plot.second_plot.draw_straight_line(
            signal.other_chart_line.start_candle,
            signal.other_chart_line.end_candle,
            signal.other_chart_line.source,
        )
        if draw_indicators and self.confirmation_indicators:
            for indicator in self.confirmation_indicators:
                indicator.plot(plot.base_plot)


@dataclass(kw_only=True)
class TwoChartDiverTradeConfig(TradeConfig):
    second_chart: Chart
    strategy: Divergence  # type: ignore[override]
    merge_two_chart_time: bool = field(default=True)

    def export_config(self) -> dict:
        conf_dict = super().export_config()
        conf_dict.update({"second_chart": self.second_chart.export_config()})
        return conf_dict

    def get_chartdata(self, n_bar: int | None = None) -> tuple[ChartData, ChartData]:  # type: ignore[override]
        base_chartdata = self.agent.get_chartdata(
            self.chart, n_bar if n_bar else self.n_candle_check
        )
        second_chartdata = self.agent.get_chartdata(
            self.second_chart, n_bar if n_bar else self.n_candle_check
        )

        if base_chartdata is None or second_chartdata is None:
            raise ValueError(f"chart data is None from {self.agent.__class__.__name__}")
        return base_chartdata, second_chartdata

    async def find_signal(
        self,
        chartdata: ChartData,
        second_chartdata: ChartData,
    ) -> None | tuple[DivergenceSignal, Position] | DivergenceSignal:
        signal = self.strategy.check_signal(
            chartdata, second_chartdata, self.long_signal, self.short_signal
        )
        if signal is None:
            return None
        logger.info(f"Two Chart Divergence Signal:{signal}")

        plot = None
        if self.send_signal:
            plot = DoubleChartPlot(chartdata, second_chartdata)
            self.strategy.draw(plot, signal, draw_indicators=True)

        if not self.consider_position:
            if self.send_signal:
                await TelegramReporter().new_signal(signal, plot)
            return signal

        entry_source = (
            signal.main_chart_line.end_candle.high
            if signal.side is MarketSide.BEARISH
            else signal.main_chart_line.end_candle.low
        )

        position = await self.position_handler.generate(
            signal, sl_base_price=entry_source, plot=plot
        )
        if position:
            return signal, position
        return None

    async def task(self):
        base_chartdata, second_chartdata = self.get_chartdata()

        base_data = copy(base_chartdata)
        base_data.candles = base_data.candles[:-1]

        second_data = copy(second_chartdata)
        second_data.candles = second_data[:-1]

        res = await self.find_signal(base_data, second_data)
        if res is None:
            return self.give_delay(base_chartdata[-1])
        if isinstance(res, tuple):
            signal, position = res
        else:
            signal = res
            position = None
        return self.give_delay(base_chartdata[-1], jump=True), signal, position

    async def backtest(  # type: ignore
        self,
        n_bar=500,
        len_sub_data=100,
        show_image=True,
    ):
        self.send_signal = False

        all_signals: list[Signal | DivergenceSignal] = []

        jump = 0
        base_chartdata, second_chartdata = self.get_chartdata(n_bar)
        for i in range(len_sub_data, len(base_chartdata) - 2):
            base_sub_data = ChartData(base_chartdata.chart, base_chartdata[:i])
            seocnd_sub_data = ChartData(
                second_chartdata.chart,
                second_chartdata[:i],
            )

            if jump > 0:
                jump -= 1
                continue
            signal = await self.find_signal(base_sub_data, seocnd_sub_data)
            if signal is None:
                continue
            jump = self.bar_between_signals
            all_signals.append(signal)  # type: ignore

        plot = DoubleChartPlot(base_chartdata, second_chartdata, plot_n_candles=n_bar)
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
