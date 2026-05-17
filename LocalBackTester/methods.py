from Forex.agent import forex_timeframe_mapper
from DivergenceStrategy.divergence import DivergenceTradeConfig
from LocalBackTester.Database.methods import fetch_diver_siganls
from ChartModule.plot import DoubleChartPlot
from LocalBackTester.agent import LocalAgent
from LocalBackTester.models import CsvChart
from LocalBackTester.Database.methods import (
    store_diver_backtest,
    store_diver_signal,
    fetch_diver_backtest,
)
from custom_logger import CustomLogger
import mt5_wrapper as mt5
import pandas as pd
import logging


CustomLogger(True, consol_log_level=logging.DEBUG)


def plot_csv_kline(chart: CsvChart):
    from ChartModule.plot import ChartPlot

    agent = LocalAgent()
    chartdata = agent.get_chartdata(chart)
    ChartPlot(chartdata, len(chartdata.candles)).show()  # type: ignore


def store_forex_data(chart: CsvChart, n_bars=1000):
    ohlcv_res = mt5.copy_rates_from_pos(
        chart.symbol, forex_timeframe_mapper(chart.timeframe), 1, n_bars
    )
    logging.debug(ohlcv_res)
    df = pd.DataFrame(ohlcv_res)
    df.rename(columns={"time": "open_time", "real_volume": "volume"}, inplace=True)
    df = df[
        ["open_time", "open", "high", "low", "close", "tick_volume", "spread", "volume"]
    ]
    df.to_csv(chart.csv_path, index=False)
    logging.debug(df)


def load_diver_backtest(the_config: DivergenceTradeConfig):
    n_bar = the_config.chart.total_bars_number  # type: ignore
    signals = fetch_diver_siganls(the_config)
    if signals is None:
        raise Exception(f"There is no related signals for the config: {the_config}")
    chartdata, second_chartdata = the_config.get_chartdata(n_bar)

    plot = DoubleChartPlot(chartdata, second_chartdata, n_bar)
    for signal in signals:
        the_config.strategy.draw(plot, signal)
    plot.show()


async def diver_signal_local_backtest(the_config: DivergenceTradeConfig):
    diver_backtest = fetch_diver_backtest(the_config)

    if diver_backtest:
        logging.info("Already in db. Loading previous backtest ....")
        load_diver_backtest(the_config)
        return

    res = await the_config.backtest(
        n_bar=the_config.chart.total_bars_number,  # type: ignore
        len_sub_data=the_config.n_candle_check,
        consider_positions=False,
        show_image=True,
    )

    backtest_datapoint = store_diver_backtest(the_config)
    logging.debug(backtest_datapoint)
    diver_signals = res[0]
    store_diver_signal(diver_signals, backtest_datapoint.id)  # type: ignore
