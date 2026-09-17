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
from ChartModule.plot import DoubleChartFigure
from TraderBot.PositionHandlers.manager import TradesManager
import TraderBot.Commands as commands
from TraderBot.trader_bot import TraderBot
from TraderBot.models import ExchangeAgent, Strategy
import logging


logger = logging.getLogger("OscillatorDivergence")


class OscillatorDivergence(Strategy):
    def __init__(
        self,
        oscillator_indicator: Indicator,
        min_step: int,
        max_step: int,
        indicators: list[Indicator] = [],
        long_support_conditions=SupportCandlesPattern.RED_GREEN,
        short_support_conditions=SupportCandlesPattern.GREEN_RED,
        name="OscillatorDivergence",
        inverse_diver_long: bool = False,
        inverse_diver_short: bool = False,
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
        base_chartdata: ChartData,
        second_chartdata: ChartData,
        inverse: bool = False,
        other_chart_line_validation: bool = True,
    ) -> tuple[Line, Line] | None:
        # TODO: implement other_chart_line_validation
        wanted_base, wanted_second = (
            (MarketSide.BEARISH, MarketSide.BULLISH)
            if inverse
            else (MarketSide.BULLISH, MarketSide.BEARISH)
        )

        for base_line in linefinder.iter_lines_at_index(base_chartdata, -1):
            if base_line.direction() is not wanted_base:
                continue

            second_line = linefinder.validate_line_at(
                second_chartdata, base_line.start_timestamp, base_line.end_timestamp
            )
            if second_line is None:
                continue
            if second_line.direction() is not wanted_second:
                continue

            return base_line, second_line

        return None

    def check_long_signal(self, base_chartdata: ChartData, second_chartdata: ChartData):
        if not self.long_support_conditions.check(base_chartdata):
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
        if not self.short_support_conditions.check(base_chartdata):
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
        check_long: bool = True,
        check_short: bool = True,
    ) -> DivergenceSignal | None:
        long_signal = None
        short_signal = None

        confirmations = self.get_indicators_confirmation(chartdata)
        self.oscillator_indicator.set(chartdata)

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


class DivergenceBot(TraderBot):
    def __init__(
        self,
        chart: Chart,
        second_chart: Chart,
        agent: ExchangeAgent,
        strategy: OscillatorDivergence,
        trades_manager: TradesManager,
        bar_between_signals: int = 2,
        n_candle_check: int = 100,
        consider_position: bool = True,
    ):
        self.second_chart = second_chart
        self.chart = chart
        self.agent = agent
        self.strategy = strategy
        self.trades_manager = trades_manager
        self.bar_between_signals = bar_between_signals
        self.n_candle_check = n_candle_check
        self.consider_position = consider_position

    def post_init(self):
        if not self.agent.prepare_chart(self.second_chart):
            raise ValueError(
                f"Failed to prepare chart for {self.identifier} on second chart"
            )
        if not self.agent.prepare_chart(self.chart):
            raise ValueError(f"Failed to prepare chart for {self.identifier}")
        logging.info(f"{self.identifier} Bot initialized")

    @property
    def identifier(self):
        return f"{self.chart}_{self.second_chart}_{self.strategy.name}"

    def export_config(self) -> dict:
        conf_dict = super().export_config()
        conf_dict.update({"second_chart": self.second_chart.export_config()})
        return conf_dict

    def check_signal(
        self, chartdata: ChartData, second_chartdata: ChartData
    ) -> None | DivergenceSignal:
        signal = self.strategy.check_signal(
            chartdata,
            second_chartdata,
            self.trades_manager.long_trade,
            self.trades_manager.short_trade,
        )
        if not signal:
            return None

    async def task(self):
        chartdata = self.get_chartdata()
        second_chartdata = self.get_chartdata(chart=self.second_chart)
        signal = self.check_signal(chartdata, second_chartdata)
        if signal:
            if self.consider_position:
                position = self.trades_manager.generate_position(signal)
                if position:
                    plot = DoubleChartFigure(
                        chartdata, second_chartdata, self.n_candle_check
                    )
                    self.trade(signal, position, plot)
            else:
                plot = DoubleChartFigure(
                    chartdata, second_chartdata, self.n_candle_check
                )
                self.strategy.plotter(
                    plot.main_pane, plot.second_pane, signal, self.strategy.indicators
                )
                commands.NewSignalReport(signal, plot=plot).send(
                    reporter=self.trades_manager.reporter
                )

        return self.give_delay(chartdata.timestamps[-1])
