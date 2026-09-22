from typing import overload

import numpy as np

from Bots.DivergenceStrategy.divergence import DivergencePlotter, DivergenceSignal
from ChartModule.models import (
    Chart,
    ChartData,
    MarketSide,
    CandlesSource,
)
from ChartModule.Indicators import (
    Indicator,
    LineFinder,
    Line,
    SupportCandlesPattern,
)
from ChartModule.plot import ChartWithOscillatorFigure
from TraderBot.PositionHandlers.manager import TradesManager
from TraderBot.PositionHandlers.plot import PositionPlotter
from TraderBot.trader_bot import TraderBot
from TraderBot.models import ExchangeAgent, Position, Strategy
import logging


logger = logging.getLogger("OscillatorDivergence")


class OscillatorDivergence(Strategy):
    def __init__(
        self,
        oscillator_indicator: Indicator,
        min_step: int,
        max_step: int,
        indicators: list[Indicator] = [],
        long_support_conditions=SupportCandlesPattern.RAW,
        short_support_conditions=SupportCandlesPattern.RAW,
        name="OscillatorDivergence",
        inverse_diver_long: bool = True,
        inverse_diver_short: bool = True,
        long_other_chart_line_validation: bool = True,
        short_other_chart_line_validation: bool = True,
        body_candle: bool = False,
    ) -> None:
        self.oscillator_indicator = oscillator_indicator
        self.name = name
        self.plotter = DivergencePlotter()
        self.indicators = indicators
        self.long_support_conditions = long_support_conditions
        self.short_support_conditions = short_support_conditions
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
                "oscillator": self.oscillator_indicator.export_configs(),
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
        linefinder: LineFinder,
        chartdata: ChartData,
        oscillator_data: np.ndarray,
        inverse: bool = False,
        other_chart_line_validation: bool = True,
    ) -> tuple[Line, Line] | None:
        # TODO: implement other_chart_line_validation
        wanted_base, wanted_second = (
            (MarketSide.BEARISH, MarketSide.BULLISH)
            if inverse
            else (MarketSide.BULLISH, MarketSide.BEARISH)
        )

        for base_line in linefinder.iter_lines_at_index(chartdata, -1):
            if base_line.direction is not wanted_base:
                continue
            second_line = linefinder.validate_value_line(
                oscillator_data,
                chartdata.timestamps,
                base_line.start_timestamp,
                base_line.end_timestamp,
                linefinder._cross_multiplier(),
            )
            if second_line is None:
                continue
            if second_line.direction is not wanted_second:
                continue

            return base_line, second_line

        return None

    def check_long_signal(self, chartdata: ChartData, oscillator_data: np.ndarray):
        if not self.long_support_conditions.check(chartdata):
            return None
        res = self.find_divergence(
            LineFinder(
                CandlesSource.Bottom if self.body_candle else CandlesSource.Low,
                self.min_step,
                self.max_step,
                support_conditions=self.long_support_conditions,
            ),
            chartdata,
            oscillator_data,
            self.inverse_diver_long,
            self.long_other_chart_line_validation,
        )
        if res is None:
            return None
        main_chart_line, other_chart_line = res
        signal = DivergenceSignal(
            chartdata.chart,
            chartdata[-1],
            MarketSide.BULLISH,
            self.name,
            main_chart_line,
            other_chart_line,
        )
        return signal

    def check_short_signal(self, chartdata: ChartData, oscillator_data: np.ndarray):
        if not self.short_support_conditions.check(chartdata):
            return None
        res = self.find_divergence(
            LineFinder(
                CandlesSource.Top if self.body_candle else CandlesSource.High,
                self.min_step,
                self.max_step,
                support_conditions=self.short_support_conditions,
            ),
            chartdata,
            oscillator_data,
            not self.inverse_diver_short,
            self.short_other_chart_line_validation,
        )
        if res is None:
            return None
        main_chart_line, other_chart_line = res
        signal = DivergenceSignal(
            chartdata.chart,
            chartdata[-1],
            MarketSide.BEARISH,
            self.name,
            main_chart_line,
            other_chart_line,
        )
        return signal

    def signal_from(
        self,
        chartdata: ChartData,
        oscillator_data: np.ndarray,
        check_long: bool = True,
        check_short: bool = True,
        confirmations: list[MarketSide] | None = None,
    ) -> DivergenceSignal | None:
        if confirmations is None:
            confirmations = self.get_indicators_confirmation(chartdata)

        long_signal = None
        short_signal = None

        if check_long and MarketSide.BEARISH not in confirmations:
            long_signal = self.check_long_signal(chartdata, oscillator_data)

        if check_short and MarketSide.BULLISH not in confirmations:
            short_signal = self.check_short_signal(chartdata, oscillator_data)

        if long_signal and short_signal:
            logger.warning("long and short signal in same time!")
            return None

        if short_signal:
            return short_signal

        if long_signal:
            return long_signal

        return None

    def check_signal(
        self,
        chartdata: ChartData,
        check_long: bool = True,
        check_short: bool = True,
    ) -> DivergenceSignal | None:
        confirmations = self.get_indicators_confirmation(chartdata)
        self.oscillator_indicator.set(chartdata)
        return self.signal_from(
            chartdata,
            self.oscillator_indicator.data,
            check_long,
            check_short,
            confirmations,
        )


class OscillatorDiverBot(TraderBot):
    def __init__(
        self,
        chart: Chart,
        agent: ExchangeAgent,
        strategy: OscillatorDivergence,
        trades_manager: TradesManager,
        bar_between_signals: int = 2,
        n_candle_check: int = 100,
        consider_position: bool = True,
    ):
        self.chart = chart
        self.agent = agent
        self.strategy = strategy
        self.trades_manager = trades_manager
        self.bar_between_signals = bar_between_signals
        self.n_candle_check = n_candle_check
        self.consider_position = consider_position
        self.consider_figure = True

    def generate_figure(
        self,
        chartdata: ChartData,
        signal: DivergenceSignal,
        position: Position | None = None,
        *args,
        **kwargs,
    ) -> ChartWithOscillatorFigure | None:
        if not self.consider_figure:
            return None
        figure = ChartWithOscillatorFigure(
            chartdata,
            self.strategy.oscillator_indicator.data,
            self.n_candle_check,
        )
        self.strategy.plotter(
            figure.main_pane, figure.oscillator_pane, signal, self.strategy.indicators
        )
        if position:
            PositionPlotter()(figure.main_pane, position)
        return figure
