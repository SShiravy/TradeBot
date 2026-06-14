from DivergenceStrategy import DivergenceTradeConfig
from LocalBackTester.Database.create_db import create_db
from LocalBackTester.StatisticalMethods.pnl_distribution import (
    PipPnlDistribution,
)
from LocalBackTester.StatisticalMethods.sl_pip_distribution import (
    PipAfterSLDistribution,
)
from LocalBackTester.models import TickDataHandler
from custom_logger import CustomLogger
from config import settings
import asyncio
import logging


CustomLogger(True, consol_log_level=logging.DEBUG)


def store_klines_from_mt5():
    from LocalBackTester.methods import store_forex_data
    from ChartModule.models import TimeFrame
    from LocalBackTester.models import CsvChart, KlineSource

    symbol = "BTCUSD"
    len_bar = 99000
    timeframe = TimeFrame.one_minute

    chart = CsvChart(
        symbol,
        timeframe,
        csv_path=rf"D:\TraderBot\LocalBackTester\KlinesCSV\Opofincance\opo_{symbol.replace('!', '')}_{timeframe.value}_{len_bar}.csv",
        csv_source=KlineSource.OPOFINANCE_META,
    )

    store_forex_data(chart, n_bars=len_bar)


async def diver_position_local_backtest(
    the_config: DivergenceTradeConfig,
    consider_db=True,
    statisical_pnl_indicators: list = [],
    pnl_distribution_indicaotors: list = [],
    show_plot=True,
):
    from TradingModule import commands
    from LocalBackTester.Database.methods import store_positions_result
    from LocalBackTester.Database.methods import fetch_diver_siganls
    from ChartModule.plot import DoubleChartPlot
    from ChartModule.models import MarketSide
    from copy import copy
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
    if show_plot:
        plot = DoubleChartPlot(chartdata, second_chartdata, n_bar)
        for signal in signals:
            the_config.strategy.draw(plot, signal)
    for pos in position_handler.closed_positions:
        if show_plot:
            pos.plot = plot  # type: ignore
            pos.draw()
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
        overal_report = PositionsReport.give_overall_report(copy(all_reports))
        logging.info("\n" + str(overal_report))

    if show_plot:
        plot.show()  # type: ignore
        del plot  # type: ignore
    del signals, commands_report

    # Indicators -------------------------------
    input("Enter for Continue ....")
    all_positions = position_handler.closed_positions
    if pnl_distribution_indicaotors:
        ticks_handler = TickDataHandler(parquet_path=the_config.chart.ticks_path)  # type:ignore
        for i, indicator in enumerate(pnl_distribution_indicaotors):
            indicator.set_method(the_config, all_positions, ticks_handler)
            indicator.plot(show=True)
            pnl_distribution_indicaotors[i] = None

        del ticks_handler, pnl_distribution_indicaotors

    if statisical_pnl_indicators:
        for i, staticial_indicator in enumerate(statisical_pnl_indicators):
            staticial_indicator(
                all_positions,
                f"{the_config.chart.symbol}_{the_config.chart.timeframe}",
            ).plot(show=True)
            statisical_pnl_indicators[i] = None

        del statisical_pnl_indicators


def test_tick_data():
    from LocalBackTester.models import TickDataHandler

    path = r"D:\TraderBot\LocalBackTester\TickData\Opofinance\XAUUSD!_2025_11_03_to_2026_05_19.parquet"

    # read_tick_data(path)
    tick_handler = TickDataHandler(path)
    logging.info(tick_handler.get_ticks_from_timstamp_range(1769543520, 1769543940))


if __name__ == "__main__":
    settings.METATRADER_TERMINAL_PATH = ""
    from LocalBackTester.methods import *

    from LocalBackTester.local_backtest_configs import (
        diver_solbtc_5m_17570,
        diver_solbtc_5m_1000,
        diver_forex_xau_1m_5000_test,
        diver_forex_xau_1m_99000,
    )

    from LocalBackTester.StatisticalMethods import (
        WeekdayPnLHistogram,
        HourlyPnLHistogram,
        SessionPnLHistogram,
    )

    the_config = diver_solbtc_5m_1000

    # test_tick_data()

    create_db()
    import cProfile
    import pstats

    profiler = cProfile.Profile()
    profiler.enable()

    # plot_csv_kline(the_config.second_chart) # type: ignore

    asyncio.run(diver_signal_local_backtest(the_config, show_plot=True))

    # plot_name = f"{the_config.chart.symbol}_{the_config.chart.timeframe}_99000"
    plot_name = f"{the_config.chart.symbol}_{the_config.chart.timeframe}_17570"

    asyncio.run(
        diver_position_local_backtest(
            the_config,
            consider_db=False,
            statisical_pnl_indicators=[
                WeekdayPnLHistogram,
                HourlyPnLHistogram,
                SessionPnLHistogram,
            ],
            pnl_distribution_indicaotors=[
                PipPnlDistribution(
                    candles_range=200,
                    plot_name=plot_name,
                ),
                PipAfterSLDistribution(
                    candles_range=200, plot_name=plot_name, tolerance_pip=30
                ),
            ],
            show_plot=True,
        )
    )

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumtime")
    stats.print_stats(30)

    # store_mt5_tick_data()
    # read_tick_data()


# TODO: search and replace candle.time.timestamp() with candle.timestamp
# TODO: change find candle by timestamp mothod, for returning index of candle
# TODO: change position model to store timestamp for open_time ...
# TODO: add stepping handler for crypto
