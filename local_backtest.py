from DivergenceStrategy import DivergenceTradeConfig
from LocalBackTester.Database.create_db import create_db
from LocalBackTester.StatisticalMethods.models import StatisticalIndicator
from LocalBackTester.diver_backtester import DiverBacktester
from custom_logger import CustomLogger
from config import settings
import asyncio
import logging


CustomLogger(True, consol_log_level=logging.DEBUG)


async def diver_position_local_backtest(
    the_config: DivergenceTradeConfig,
    consider_db=True,
    statistical_indicators: list[StatisticalIndicator] = [],
    show_chartdata=False,
    show_plot=True,
):
    from TradingModule import commands
    from LocalBackTester.Database.methods import store_positions_result
    from LocalBackTester.Database.methods import fetch_diver_siganls
    from ChartModule.plot import DoubleChartPlot
    from ChartModule.models import MarketSide
    from TradingModule.models import PositionsReport
    from LocalBackTester.Database.methods import (
        fetch_positions_result,
        fetch_diver_backtest,
    )

    position_handler = the_config.position_handler
    n_bar = the_config.chart.total_bars_number  # type: ignore

    if consider_db:
        diver_conf = fetch_diver_backtest(the_config)
        if diver_conf is None or diver_conf.id is None:
            raise ValueError(f"TradeConfig not in db: {diver_conf}")

        res = fetch_positions_result(position_handler, diver_conf.id)
        if res:
            logging.info(res)
            return

    signals = fetch_diver_siganls(the_config)
    if signals is None:
        raise Exception(f"There is no related signals for the config: {the_config}")
    chartdata, second_chartdata = the_config.get_chartdata(n_bar)

    # positions
    for signal in signals:
        signal_candle_index = chartdata.candles.index(signal.candle)
        pos_candle = chartdata.candles[signal_candle_index + 1]

        entry_source = (
            signal.base_line.end_candle.high
            if signal.side is MarketSide.BEARISH
            else signal.base_line.end_candle.low
        )

        position = await position_handler.generate_position(
            signal,
            entry_price=pos_candle.open,  # TODO: add tick data param here
            sl_base_price=entry_source,
        )
        if not position:
            continue
        position.open_time = pos_candle.time
        # handler
        for candle in chartdata.candles[signal_candle_index + 1 :]:
            ticks = [
                candle.open,
                candle.low,
                candle.high,
                candle.close,
            ]  # TODO: change here for real ticks
            position_handler.handler(position, ticks)
            await commands.TradeCommand.execute_pending_commands(
                candle.time, report=False
            )
            if position.closed:
                position_handler.closed_positions.append(position)
                position_handler.open_positions.remove(position)
                break

    # plot
    if show_chartdata:
        plot = DoubleChartPlot(chartdata, second_chartdata, n_bar)
        for signal in signals:
            the_config.strategy.draw(plot, signal)
        for pos in position_handler.closed_positions:
            pos.plot = plot
            pos.draw()
        plot.show()
        del plot

    commands_report = commands.TradeCommand.close_records()
    if consider_db:
        result = store_positions_result(
            position_handler, commands_report, int(signals[0].source)
        )
        logging.info(result)
    else:
        all_reports = position_handler.report(flush=False)
        logging.info("Result:\n\n" + commands_report)
        for poses_report in all_reports:
            logging.info("\n" + str(poses_report))
        overal_report = PositionsReport.give_overall_report(all_reports)
        logging.info(f"\n{len(signals)=}")
        logging.info("\n" + str(overal_report))

    del signals, commands_report

    # Indicators -------------------------------
    input("Enter for Continue ....")
    all_positions = position_handler.closed_positions
    plot_name = (
        f"{the_config.chart.symbol}_{the_config.chart.timeframe}_{len(chartdata)}"
    )
    if statistical_indicators:
        for i, indicator in enumerate(statistical_indicators):
            indicator.analyze(all_positions, the_config)
            indicator.plot(plot_name, show=show_plot)
            statistical_indicators[i] = None  # type: ignore

        del statistical_indicators


if __name__ == "__main__":
    settings.METATRADER_TERMINAL_PATH = ""
    from LocalBackTester.methods import *  # noqa: F403
    from LocalBackTester.local_backtest_configs import *  # noqa: F403
    from LocalBackTester.StatisticalMethods import (
        WeekdayPnLHistogram,
        HourlyPnLHistogram,
        SessionPnLHistogram,
        RiskAnalysis,
    )

    the_config = diver_forex_xau_1m_5000_test

    create_db()
    import cProfile
    import pstats

    profiler = cProfile.Profile()
    profiler.enable()

    # plot_csv_kline(the_config.chart) # type: ignore

    # asyncio.run(diver_signal_local_backtest(the_config, show_plot=True))
    statistical_indicators = [
        WeekdayPnLHistogram(),
        HourlyPnLHistogram(),
        SessionPnLHistogram(),
        # PipPnlDistribution(
        #     candles_range=200,
        # ),
        # PipAfterSLDistribution(
        #     candles_range=200,
        #     tolerance_pip=30
        # ),
        RiskAnalysis(),
    ]

    diver_backtester = DiverBacktester(
        the_config, statistical_indicators, show_chartdata=True
    )
    asyncio.run(
        diver_backtester.positions_backtest(use_database=False, show_plots=False)
    )

    asyncio.run(
        diver_position_local_backtest(
            the_config,
            consider_db=False,
            statistical_indicators=statistical_indicators,
            show_chartdata=True,
            show_plot=False,
        )
    )

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumtime")
    stats.print_stats(30)
