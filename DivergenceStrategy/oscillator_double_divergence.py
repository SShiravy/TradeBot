from datetime import timedelta

from ChartModule.models import (
    Candle,
    Signal,
    ChartData,
    MarketSide,
)
from ChartModule.Indicators import (
    Line,
)
from ChartModule.plot import ChartWithOscillatorPlot
from DivergenceStrategy.oscillator_divergence import (
    OscillatorDiverSignal,
    OscillatorDivergence,
)
from Forex.agent import ForexAgent
from TradingModule.reporter import TelegramReporter
from TradingModule.trader_bot import TradeConfig, Position
from dataclasses import dataclass
from copy import copy
import logging


logger = logging.getLogger("DoubleDivergence")


@dataclass(slots=True, frozen=True)
class OscillatorDoubleDiverSignal(Signal):
    main_chart_line: Line
    main_chart_second_line: Line
    other_chart_line_prices: tuple[float, float]
    other_chart_second_line_prices: tuple[float, float]

    @classmethod
    def generate_signal(
        cls, first_signal: OscillatorDiverSignal, second_signal: OscillatorDiverSignal
    ):
        return cls(
            first_signal.chart,
            first_signal.candle,
            first_signal.side,
            first_signal.source,
            first_signal.main_chart_line,
            second_signal.main_chart_line,
            first_signal.other_chart_line_prices,
            second_signal.other_chart_line_prices,
        )

    @property
    def first_signal(self):
        return OscillatorDiverSignal(
            self.chart,
            self.candle,
            self.side,
            self.source,
            self.main_chart_line,
            self.other_chart_line_prices,
        )

    @property
    def second_signal(self):
        return OscillatorDiverSignal(
            self.chart,
            self.main_chart_second_line.end_candle,
            self.side,
            self.source,
            self.main_chart_second_line,
            self.other_chart_second_line_prices,
        )


@dataclass(kw_only=True)
class OscillatorDoubleDiverConfig(TradeConfig):
    strategy: OscillatorDivergence  # type: ignore[override]
    same_line_source: bool = True

    def give_delay(self, last_candle: Candle, jump=False) -> timedelta:
        # TODO: fix here for all agents not only forex
        delay = self.chart.timeframe.time_delta
        if jump:
            delay *= self.bar_between_signals
        last_candle_time = ForexAgent().get_chartdata(self.chart, n_bars=1).candles[0]  # type: ignore
        next_timestamp = int(round(last_candle_time.timestamp) + delay.total_seconds())
        sleep_time_based_on_timestamp = (
            next_timestamp - ForexAgent().give_current_timestamp(self.chart)
        )

        return timedelta(seconds=sleep_time_based_on_timestamp + 1)

    async def find_signal(
        self, chartdata: ChartData
    ) -> (
        None
        | tuple[OscillatorDoubleDiverSignal, Position]
        | OscillatorDoubleDiverSignal
    ):
        first_signal = self.strategy.check_signal(
            chartdata, self.long_signal, self.short_signal
        )
        if first_signal is None:
            return None
        left_index = chartdata.candle_index(first_signal.main_chart_line.start_candle)
        second_sub_chart = copy(chartdata)
        second_sub_chart.candles = chartdata.candles[: left_index + 2]
        second_signal = self.strategy.check_signal(
            second_sub_chart, self.long_signal, self.short_signal, shift_candle=True
        )
        if second_signal is None or second_signal.side != first_signal.side:
            return None
        if (
            self.same_line_source
            and first_signal.main_chart_line.source
            != second_signal.main_chart_line.source
        ):
            return None
        double_diver_signal = OscillatorDoubleDiverSignal.generate_signal(
            first_signal, second_signal
        )
        logger.info(f"OscillatorDiver Signal:{double_diver_signal}")
        # TODO: change entry source to agent.get_current_tick
        plot = None
        if self.send_signal:
            self.strategy.oscillator_indicator.set(candles=chartdata.candles)
            plot = ChartWithOscillatorPlot(
                chartdata, self.strategy.oscillator_indicator.data
            )
            self.strategy.draw(plot, first_signal, draw_indicators=True)
            self.strategy.draw(
                plot, second_signal, draw_indicators=False, mark_signal=False
            )
            self.strategy.oscillator_indicator.plot(plot, plot.oscillator_ax)

        if not self.consider_position:
            if self.send_signal:
                await TelegramReporter().new_signal(double_diver_signal, plot)
            return double_diver_signal

        entry_source = (
            first_signal.main_chart_line.end_candle.high
            if first_signal.side is MarketSide.BEARISH
            else first_signal.main_chart_line.end_candle.low
        )
        position = await self.position_handler.generate_position(
            double_diver_signal, sl_base_price=entry_source, plot=plot
        )
        if not position:
            return None
        return double_diver_signal, position

    async def task(self):
        chart_data = self.get_chartdata()

        # TODO: add a param for removing last candle or not (current candle)
        sub_chart_data = copy(chart_data)
        sub_chart_data.candles = sub_chart_data.candles[:-1]
        chartdata = self.get_chartdata()
        res = await self.find_signal(chartdata)
        if res is None:
            return self.give_delay(chartdata[-1])
        if isinstance(res, tuple):
            signal, position = res
        else:
            signal = res
            position = None
        return self.give_delay(chartdata[-1], jump=True), signal, position

    async def backtest(  # type: ignore
        self,
        n_bar=500,
        len_sub_data=100,
        show_image=True,
    ):
        self.send_signal = False
        all_signals: list[OscillatorDoubleDiverSignal] = []
        default_consider_positions = self.consider_position
        self.consider_position = False
        jump = 0
        chartdata = self.get_chartdata(n_bar)
        for i in range(len_sub_data, len(chartdata) - 2):
            sub_chart_data = ChartData(chartdata.chart, chartdata[:i])

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
        self.strategy.draw(plot, all_signals[0].first_signal, draw_indicators=True)  # type: ignore
        self.strategy.draw(
            plot, all_signals[0].second_signal, draw_indicators=False, mark_signal=False
        )  # type: ignore
        for signal in all_signals[1:]:
            self.strategy.draw(plot, signal.first_signal, draw_indicators=False)  # type: ignore
            self.strategy.draw(
                plot, signal.second_signal, draw_indicators=False, mark_signal=False
            )  # type: ignore
        if show_image:
            plot.show()
        self.consider_position = default_consider_positions
        return all_signals, plot
