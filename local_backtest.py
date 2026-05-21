from DivergenceStrategy import DivergenceTradeConfig
from LocalBackTester.Database.create_db import create_db
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
    the_config: DivergenceTradeConfig, consider_db=True
):
    settings.METATRADER_TERMINAL_PATH = ""

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
    plot = DoubleChartPlot(chartdata, second_chartdata, n_bar)
    for signal in signals:
        the_config.strategy.draw(plot, signal)

    pnl_list = []
    timestamp_list = []

    for pos in position_handler.closed_positions:
        pos.plot = plot
        pos.draw()

        pnl_list.append(pos.pnl)
        timestamp_list.append(pos.open_time)

    commands_report = commands.TradeCommand.close_records()

    if consider_db:
        result = store_positions_result(
            position_handler, commands_report, int(signals[0].source)
        )
        logging.info(result)
    else:
        all_reports = position_handler.report()
        logging.info("Result:\n\n" + commands_report)
        for poses_report in all_reports:
            logging.info("\n" + str(poses_report))
        overal_report = PositionsReport.give_overall_report(copy(all_reports))
        logging.info("\n" + str(overal_report))

    plot.show()

    from LocalBackTester.StatisticalMethods.hours_histogram import (
        plot_hourly_pnl_histogram,
    )

    plot_hourly_pnl_histogram(
        pnl_list,
        timestamp_list,
        f"{the_config.chart.symbol}_{the_config.chart.timeframe}",
    )


if __name__ == "__main__":
    from LocalBackTester.methods import *

    from LocalBackTester.local_backtest_configs import (
        diver_crypto_solbtc_1m,
        diver_forex_xau_1m_5000_test,
    )

    the_config = diver_forex_xau_1m_5000_test

    create_db()

    # asyncio.run(diver_signal_local_backtest(the_config))
    asyncio.run(diver_position_local_backtest(the_config, consider_db=False))

    # store_mt5_tick_data()
    # read_tick_data()


# TODO: search and replace candle.time.timestamp() with candle.timestamp
# TODO: change find candle by timestamp mothod, for returning index of candle
# TODO: change position model to store timestamp for open_time ...
# TODO: add stepping handler for crypto
