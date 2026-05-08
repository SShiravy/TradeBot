from Forex.agent import forex_timeframe_mapper
from LocalBackTester.models import CsvChart
from custom_logger import CustomLogger
import mt5_wrapper as mt5
import pandas as pd
import logging


CustomLogger(True, consol_log_level=logging.DEBUG)


def store_forex_data(chart:CsvChart,n_bars=1000):
    ohlcv_res = mt5.copy_rates_from_pos(
            chart.symbol, forex_timeframe_mapper(chart.timeframe), 1, n_bars
        )
    logging.debug(ohlcv_res)
    df = pd.DataFrame(ohlcv_res)
    df.rename(columns={
    'time': 'open_time',"real_volume":"volume"},inplace=True)
    df = df[['open_time', 'open', 'high', 'low', 'close', 'tick_volume', 'spread', 'volume']]
    df.to_csv(chart.csv_path, index=False)
    logging.debug(df)
