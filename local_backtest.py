from LocalBackTester.Database.create_db import create_db
from LocalBackTester.Database.methods import store_positions_result
from LocalBackTester.agent import LocalAgent
from custom_logger import CustomLogger
from config import settings
import asyncio
import logging

settings.METATRADER_TERMINAL_PATH = ""


CustomLogger(True, consol_log_level=logging.DEBUG)


def plot_csv_kline():
    from ChartModule.plot import ChartPlot
    from LocalBackTester.all_charts import SOLUSDT_1h_2024_9

    agent = LocalAgent()
    chartdata = agent.get_chartdata(SOLUSDT_1h_2024_9)
    ChartPlot(chartdata, len(chartdata.candles)).show()  # type: ignore


def store_meta_klines():
    from LocalBackTester.methods import store_forex_data
    from ChartModule.models import TimeFrame
    from LocalBackTester.models import CsvChart

    symbol = "BTCUSD"
    len_bar = 99000
    timeframe = TimeFrame.one_minute

    chart = CsvChart(
        symbol,
        timeframe,
        csv_path=rf"D:\TraderBot\LocalBackTester\KlinesCSV\Opofincance\opo_{symbol.replace('!', '')}_{timeframe.value}_{len_bar}.csv",
    )

    store_forex_data(chart, n_bars=len_bar)
    # TODO: make it better method by adding above params to store_forex_data function


async def signal_backtester(store_db=True):
    from LocalBackTester.Database.methods import (
        store_diver_backtest,
        store_diver_signal,
        fetch_diver_backtest,
    )
    from LocalBackTester.backtest_configs import (
        diver_forex_xau_1m,
        diver_crypto_solbtc_1m,
    )

    the_config = diver_crypto_solbtc_1m

    if store_db:
        valid_hash = fetch_diver_backtest(the_config)
        if valid_hash:
            raise Exception("Same config already exists in db...")

    res = await the_config.backtest(
        n_bar=the_config.chart.number_of_bars,  # type: ignore
        len_sub_data=200,
        consider_positions=False,
        show_image=True,
    )

    if store_db:
        backtest_datapoint = store_diver_backtest(the_config)
        logging.debug(backtest_datapoint)

        dive_signals = res[0]
        store_diver_signal(dive_signals, backtest_datapoint.id)  # type: ignore


def load_diver_backtest():
    from LocalBackTester.backtest_configs import (
        diver_forex_xau_1m,
        diver_crypto_solbtc_1m,
    )
    from LocalBackTester.Database.methods import fetch_diver_siganls
    from ChartModule.plot import DoubleChartPlot

    the_config = diver_crypto_solbtc_1m
    n_bar = 700

    signals = fetch_diver_siganls(the_config)
    if signals is None:
        raise Exception(f"There is no related signals for the config: {the_config}")
    chartdata, second_chartdata = the_config.get_chartdata(n_bar)

    plot = DoubleChartPlot(chartdata, second_chartdata, n_bar)
    for signal in signals:
        the_config.strategy.draw(plot, signal)
    plot.show()


async def position_backtester():
    from TradingModule import commands
    from LocalBackTester.backtest_configs import (
        diver_forex_xau_1m,
        diver_crypto_solbtc_1m,
    )
    from LocalBackTester.Database.methods import fetch_diver_siganls
    from ChartModule.plot import DoubleChartPlot
    from LocalBackTester.Database.backtest_models import PositionsResult
    from LocalBackTester.Database.methods import (
        fetch_positions_result,
        fetch_diver_backtest,
    )

    the_config = diver_forex_xau_1m
    position_handler = the_config.position_handler
    n_bar = 5000

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
        position = await position_handler.generate_position(
            signal,
            entry_price=pos_candle.open,  # TODO: add tick data param here
        )
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
    for pos in position_handler.closed_positions:
        pos.plot = plot
        pos.draw()

    commands_report = commands.TradeCommand.close_records()

    result = store_positions_result(
        position_handler, commands_report, int(signals[0].source)
    )
    logging.info(result)
    plot.show()

    # from copy import copy
    # from TradingModule.models import PositionsReport
    # commands_report = commands.TradeCommand.close_records()
    # all_reports = position_handler.report()
    # logging.info("Result:\n\n" + commands_report)
    # for poses_report in all_reports:
    #     logging.info("\n" + str(poses_report))
    # overal_report = PositionsReport.give_overall_report(copy(all_reports))
    # logging.info("\n" + str(overal_report))

    plot.show()


if __name__ == "__main__":
    # plot_csv_kline()

    # asyncio.run(crypto_backtest())
    # asyncio.run(forex_backtest())

    # store_meta_klines()

    create_db()
    # asyncio.run(signal_backtester())

    # load_diver_backtest()

    asyncio.run(position_backtester())


# TODO: search and replace candle.time.timestamp() with candle.timestamp
# TODO: change find candle by timestamp mothod, for returning index of candle
# TODO: change position model to store timestamp for open_time ...
# TODO: add max_win/lose_in_row to PositionReport ...
# TODO: add duration to PositionReport...
# TODO: Handle Extra commands in backtest --> Executed: {'OpenPosition': 23, 'TrailStoploss': 21, 'ChangeTakeProfit': 20, 'SendPositionSignal': 23, 'TakeProfit': 8, 'StopLoss': 15}
# TODO: handle different timestamp in local db for crypto and forex
