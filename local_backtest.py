from LocalBackTester.Database.create_db import create_db
from LocalBackTester.agent import LocalAgent
from ChartModule.plot import ChartPlot
from custom_logger import CustomLogger
import logging
from config import settings

settings.METATRADER_TERMINAL_PATH = ""


CustomLogger(True, consol_log_level=logging.DEBUG)


def plot_csv_kline():
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
        valid_diver_backtest_hash,
    )
    from LocalBackTester.backtest_configs import (
        diver_forex_xau_1m,
        diver_crypto_solbtc_1m,
    )

    the_config = diver_crypto_solbtc_1m

    if store_db:
        valid_hash = valid_diver_backtest_hash(the_config)
        if not valid_hash:
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


if __name__ == "__main__":
    import asyncio
    
    # plot_csv_kline()

    # asyncio.run(crypto_backtest())
    # asyncio.run(forex_backtest())

    # store_meta_klines()

    create_db()

    asyncio.run(signal_backtester())


# TODO: search and replace candle.time.timestamp() with candle.timestamp
