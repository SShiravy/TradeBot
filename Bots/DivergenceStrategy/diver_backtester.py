from Bots.DivergenceStrategy.old_oscillator_divergence import OscillatorDiverConfig
from TraderBot import commands
from LocalBackTester.Database.methods import (
    fetch_oscillator_diver_siganls,
    store_positions_result,
)
from LocalBackTester.Database.methods import fetch_two_chart_diver_siganls
from ChartModule.plot import ChartWithOscillatorPlot, DoubleChartPlot
from ChartModule.models import ChartData, MarketSide
from TraderBot.PositionHandlers.manager import PositionGenerator
from TraderBot.models import PositionsReport
from LocalBackTester.Database.methods import (
    fetch_positions_result,
    fetch_diver_backtest,
)
from Bots.DivergenceStrategy import TwoChartDiverTradeConfig
from LocalBackTester.StatisticalMethods.models import StatisticalIndicator
import logging

logger = logging.getLogger("DiverBacktest")


class TwoChartDiverBacktester:
    def __init__(
        self,
        diver_config: TwoChartDiverTradeConfig,
        statistical_indicators: list[StatisticalIndicator] = [],
        show_chartdata: bool = False,
    ) -> None:
        self.diver_config = diver_config
        self.show_chartdata = show_chartdata
        self.statistical_indicators = statistical_indicators

    def plot_double_chart(
        self,
        chartdata: ChartData,
        second_chartdata: ChartData,
        signals: list,
        position_handler: PositionGenerator,
    ):
        n_bar = self.diver_config.chart.total_bars_number  # type: ignore
        plot = DoubleChartPlot(chartdata, second_chartdata, n_bar)
        for signal in signals:
            self.diver_config.strategy.draw(plot, signal)

        for pos in position_handler.closed_positions:
            pos.plot = plot
            pos.draw()
        plot.show()
        del plot

    async def positions_backtest(self, use_database=True, show_plots=True):
        position_handler = self.diver_config.position_generator
        n_bar = self.diver_config.chart.total_bars_number  # type: ignore

        if use_database:
            diver_conf = fetch_diver_backtest(self.diver_config)
            if diver_conf is None or diver_conf.id is None:
                raise ValueError(f"TradeConfig not in db: {diver_conf}")
            res = fetch_positions_result(position_handler, diver_conf.id)
            if res:
                logger.info(res)
                return

        all_signals = fetch_two_chart_diver_siganls(self.diver_config)
        if all_signals is None:
            raise Exception(
                f"There is no related signals for the config: {self.diver_config}"
            )

        def give_next_signal(all_signals):
            for signal in all_signals:
                entry_source = (
                    signal.main_chart_line.end_candle.high
                    if signal.side is MarketSide.BEARISH
                    else signal.main_chart_line.end_candle.low
                )
                yield signal, entry_source
            yield None, None

        signal_generator = give_next_signal(all_signals)
        signal, entry_source = next(signal_generator)
        chartdata, second_chartdata = self.diver_config.get_chartdata(n_bar)

        for i, candle in enumerate(chartdata.candles):
            # TODO: tickdata

            ticks = [
                candle.open,
                candle.low,
                candle.high,
                candle.close,
            ]
            for pos in position_handler.open_positions.copy():
                if pos.closed_timestamp:
                    position_handler.closed_positions.append(pos)
                    position_handler.open_positions.remove(pos)
                    continue
                position_handler.handler(pos, ticks)

            await commands.Command.execute_pending_commands(candle.time, report=False)
            if signal is None:
                if not position_handler.open_positions:
                    break
                continue

            if candle.timestamp < signal.candle.timestamp:
                continue
            if candle.timestamp > signal.candle.timestamp:
                raise ProcessLookupError(
                    f"error on finding signal candle: {signal.candle=} | {candle.timestamp}"
                )
            # candle == signal.candle
            pos_candle = chartdata.candles[i + 1]
            position = await position_handler.generate(
                signal,
                entry_price=pos_candle.open,
                sl_base_price=entry_source,
            )
            signal, entry_source = next(signal_generator)
            if not position:
                continue
            position.open_time = pos_candle.time

        # Plot chartdata -----------
        if self.show_chartdata:
            self.plot_double_chart(
                chartdata, second_chartdata, all_signals, position_handler
            )

        # Report ------------------
        commands_report = commands.Command.close_records()
        if use_database:
            result = store_positions_result(
                position_handler, commands_report, int(all_signals[0].source)
            )
            logger.info(result)
        else:
            all_reports = position_handler.report(flush=False)
            logger.info("Result:\n\n" + commands_report)
            for poses_report in all_reports:
                logger.info("\n" + str(poses_report))
            overal_report = PositionsReport.give_overall_report(all_reports)
            logger.info(f"\n{len(all_signals)=}")
            logger.info("\n" + str(overal_report))

        del all_signals, commands_report

        # Statistical Indicators -----------------
        all_positions = position_handler.closed_positions
        plot_name = f"{self.diver_config.chart.symbol}_{self.diver_config.chart.timeframe}_{n_bar}"
        if self.statistical_indicators:
            for i, indicator in enumerate(self.statistical_indicators):
                indicator.analyze(all_positions, self.diver_config)
                indicator.plot(plot_name, show=show_plots)


class OscilatorDiverBacktester:
    def __init__(
        self,
        diver_config: OscillatorDiverConfig,
        statistical_indicators: list[StatisticalIndicator] = [],
        show_chartdata: bool = False,
    ) -> None:
        self.diver_config = diver_config
        self.show_chartdata = show_chartdata
        self.statistical_indicators = statistical_indicators

    def plot_double_chart(
        self,
        chartdata: ChartData,
        signals: list,
        position_handler: PositionGenerator,
    ):
        n_bar = self.diver_config.chart.total_bars_number  # type: ignore
        plot = ChartWithOscillatorPlot(
            chartdata, self.diver_config.strategy.oscillator_indicator, n_bar
        )
        self.diver_config.strategy.oscillator_indicator.plot(plot, plot.oscillator_ax)

        for signal in signals:
            self.diver_config.strategy.draw(plot, signal)

        for pos in position_handler.closed_positions:
            pos.plot = plot
            pos.draw()
        plot.show()
        del plot

    async def positions_backtest(self, use_database=True, show_plots=True):
        position_handler = self.diver_config.position_generator
        n_bar = self.diver_config.chart.total_bars_number  # type: ignore

        if use_database:
            diver_conf = fetch_diver_backtest(self.diver_config)
            if diver_conf is None or diver_conf.id is None:
                raise ValueError(f"TradeConfig not in db: {diver_conf}")
            res = fetch_positions_result(position_handler, diver_conf.id)
            if res:
                logger.info(res)
                return

        all_signals = fetch_oscillator_diver_siganls(self.diver_config)
        if all_signals is None:
            raise Exception(
                f"There is no related signals for the config: {self.diver_config}"
            )

        def give_next_signal(all_signals):
            for signal in all_signals:
                entry_source = (
                    signal.main_chart_line.end_candle.high
                    if signal.side is MarketSide.BEARISH
                    else signal.main_chart_line.end_candle.low
                )
                yield signal, entry_source
            yield None, None

        signal_generator = give_next_signal(all_signals)
        signal, entry_source = next(signal_generator)
        chartdata = self.diver_config.get_chartdata(n_bar)

        for i, candle in enumerate(chartdata.candles):
            # TODO: tickdata

            ticks = [
                candle.open,
                candle.low,
                candle.high,
                candle.close,
            ]
            for pos in position_handler.open_positions.copy():
                if pos.closed_timestamp:
                    position_handler.closed_positions.append(pos)
                    position_handler.open_positions.remove(pos)
                    continue
                position_handler.handler(pos, ticks)

            await commands.Command.execute_pending_commands(candle.time, report=False)
            if signal is None:
                if not position_handler.open_positions:
                    break
                continue

            if candle.timestamp < signal.candle.timestamp:
                continue
            if candle.timestamp > signal.candle.timestamp:
                raise ProcessLookupError(
                    f"error on finding signal candle: {signal.candle=} | {candle.timestamp}"
                )
            # candle == signal.candle
            pos_candle = chartdata.candles[i + 1]
            position = await position_handler.generate(
                signal,
                entry_price=pos_candle.open,
                sl_base_price=entry_source,
            )
            signal, entry_source = next(signal_generator)
            if not position:
                continue
            position.open_time = pos_candle.time

        # Plot chartdata -----------
        if self.show_chartdata:
            self.plot_double_chart(chartdata, all_signals, position_handler)

        # Report ------------------
        commands_report = commands.Command.close_records()
        if use_database:
            result = store_positions_result(
                position_handler, commands_report, int(all_signals[0].source)
            )
            logger.info(result)
        else:
            all_reports = position_handler.report(flush=False)
            logger.info("Result:\n\n" + commands_report)
            for poses_report in all_reports:
                logger.info("\n" + str(poses_report))
            overal_report = PositionsReport.give_overall_report(all_reports)
            logger.info(f"\n{len(all_signals)=}")
            logger.info("\n" + str(overal_report))

        del all_signals, commands_report

        # Statistical Indicators -----------------
        all_positions = position_handler.closed_positions
        plot_name = f"{self.diver_config.chart.symbol}_{self.diver_config.chart.timeframe}_{n_bar}"
        if self.statistical_indicators:
            for i, indicator in enumerate(self.statistical_indicators):
                indicator.analyze(all_positions, self.diver_config)
                indicator.plot(plot_name, show=show_plots)


# async def backtest(  # type: ignore
#     self,
#     n_bar=500,
#     len_sub_data=100,
#     show_image=True,
# ):
#     self.send_signal_msg = False
#     self.consider_position = False

#     all_signals: list[Signal | DivergenceSignal] = []

#     jump = 0
#     base_chartdata, second_chartdata = self.get_chartdata(n_bar)
#     n = 1
#     for i in range(len_sub_data, len(base_chartdata) - 1):
#         base_subdata = base_chartdata.subdata(end_index=i, copy=False)
#         seocnd_sub_data = second_chartdata.subdata(end_index=i, copy=False)
#         logger.debug(f"backtest subdata: {base_subdata[-1]}-{n}")
#         n += 1
#         if jump > 0:
#             jump -= 1
#             continue
#         signal = await self.find_signal(base_subdata, seocnd_sub_data)
#         logger.debug(f"backtest found signal: {signal}")
#         if signal is None:
#             continue
#         jump = self.bar_between_signals
#         all_signals.append(signal)  # type: ignore
#     logger.info(f"backtest found {len(all_signals)} signals")
#     plot = DoubleChartPlot(base_chartdata, second_chartdata, plot_n_candles=n_bar)
#     if not all_signals:
#         if show_image:
#             plot.show()
#         return [], plot

#     self.strategy.draw(plot, all_signals[0], draw_indicators=True)  # type: ignore
#     for signal in all_signals[1:]:
#         self.strategy.draw(plot, signal, draw_indicators=False)  # type: ignore
#     if show_image:
#         plot.show()
#     return all_signals, plot
