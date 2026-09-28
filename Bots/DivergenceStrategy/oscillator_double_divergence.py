from ChartModule.models import (
    Chart,
    Signal,
    ChartData,
)
from ChartModule.Indicators import Line
from ChartModule.plot import ChartWithOscillatorFigure
from Bots.DivergenceStrategy.divergence import DivergenceSignal
from Bots.DivergenceStrategy.oscillator_divergence import (
    OscillatorDiverBot,
    OscillatorDivergence,
)
from TraderBot.PositionHandlers.manager import TradesManager
from TraderBot.PositionHandlers.plot import PositionPlotter
from TraderBot.models import ExchangeAgent, Position
from dataclasses import dataclass
import logging


logger = logging.getLogger("OscillatorDoubleDiver")


@dataclass(slots=True, frozen=True)
class OscillatorDoubleDiverSignal(Signal):
    main_chart_line: Line
    main_chart_second_line: Line
    oscillator_line: Line
    oscillator_second_line: Line

    @classmethod
    def generate_signal(
        cls, first_signal: DivergenceSignal, second_signal: DivergenceSignal
    ) -> "OscillatorDoubleDiverSignal":
        return cls(
            first_signal.chart,
            first_signal.candle,
            first_signal.side,
            first_signal.source,
            first_signal.main_chart_line,
            second_signal.main_chart_line,
            first_signal.second_chart_line,
            second_signal.second_chart_line,
        )

    @property
    def first_signal(self) -> DivergenceSignal:
        return DivergenceSignal(
            self.chart,
            self.candle,
            self.side,
            self.source,
            self.main_chart_line,
            self.oscillator_line,
        )

    @property
    def second_signal(self) -> DivergenceSignal:
        return DivergenceSignal(
            self.chart,
            self.candle,
            self.side,
            self.source,
            self.main_chart_second_line,
            self.oscillator_second_line,
        )

    def __str__(self) -> str:
        return (
            f"{self.chart} {self.side} DoubleDiver from {self.source} | "
            f"second {self.main_chart_second_line.start_timestamp}"
            f"->{self.main_chart_second_line.end_timestamp} | "
            f"first {self.main_chart_line.start_timestamp}"
            f"->{self.main_chart_line.end_timestamp}"
        )


class OscillatorDoubleDiverBot(OscillatorDiverBot):
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
        super().__init__(
            chart,
            agent,
            strategy,
            trades_manager,
            bar_between_signals,
            n_candle_check,
            consider_position,
        )
        self.strategy.name = "OcillatorDoubleDiver"

    def generate_figure(
        self,
        chartdata: ChartData,
        signal: OscillatorDoubleDiverSignal,
        position: Position | None = None,
    ) -> ChartWithOscillatorFigure | None:
        if not self.consider_figure:
            return None
        figure = ChartWithOscillatorFigure(
            chartdata,
            self.strategy.oscillator_indicator.data,
            self.n_candle_check,
        )
        self.strategy.plotter(
            figure.main_pane,
            figure.oscillator_pane,
            signal.first_signal,
            self.strategy.indicators,
        )
        self.strategy.plotter(
            figure.main_pane, figure.oscillator_pane, signal.second_signal
        )
        if position:
            PositionPlotter()(figure.main_pane, position)
        return figure

    def check_signal(self, chartdata: ChartData) -> None | OscillatorDoubleDiverSignal:
        signal = self.strategy.check_signal(
            chartdata, self.trades_manager.long_trade, self.trades_manager.short_trade
        )
        if not signal:
            return None
        idx = chartdata.timestamp_index(signal.main_chart_line.start_timestamp) + 2
        second_signal = self.strategy.signal_from(
            chartdata.subdata(end_index=idx),
            self.strategy.oscillator_indicator.data[:idx],
            self.trades_manager.long_trade,
            self.trades_manager.short_trade,
            confirmations=[signal.side],
        )
        if not second_signal:
            return None
        return OscillatorDoubleDiverSignal.generate_signal(signal, second_signal)
