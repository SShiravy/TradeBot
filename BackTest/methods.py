from ExchangeAgents.MT5.agent import forex_timeframe_mapper
from BackTest.models import CsvChart
from BackTest.agent import BacktestAgent
from Settings.custom_logger import build_logger, LoggerConfig
import mt5_wrapper as mt5
import pandas as pd
import logging

from TraderBot.models import ExchangeAgent

build_logger(LoggerConfig(name="root"))


def plot_csv_kline(chart: CsvChart, exchange_agent: ExchangeAgent):
    from ChartModule.plot import SingleChartFigure

    agent = BacktestAgent(exchange_agent, chart)
    chartdata = agent.get_chartdata(chart)
    if not chartdata:
        raise ValueError(f"Chartdata is None for {chart}")
    SingleChartFigure(chartdata, len(chartdata)).show()


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


def store_mt5_tick_data():
    import mt5_wrapper as mt5
    import pandas as pd
    from datetime import datetime

    mt5.initialize()
    symbol = "XAUUSD!"

    ticks = mt5.copy_ticks_range(
        symbol, datetime(2025, 12, 1), datetime.now(), mt5.COPY_TICKS_ALL
    )
    logging.debug(ticks)

    df = pd.DataFrame(ticks)

    logging.debug(f"{df.columns=}")
    start = datetime.fromtimestamp(df.iloc[0].time).strftime(format="%Y_%m_%d")
    end = datetime.fromtimestamp(df.iloc[-1].time).strftime(format="%Y_%m_%d")
    logging.debug(f"{len(df)=}")

    file_name = f"{symbol}_{start}_to_{end}.parquet"

    df.to_parquet(
        rf"D:\TraderBot\LocalBackTester\TickData\Opofinance\{file_name}", index=False
    )


def store_binance_tick_data(csv_path: str):
    import logging
    import pandas as pd
    from datetime import datetime

    df = pd.read_csv(csv_path)

    logging.debug(f"{df.columns=}")
    logging.debug(f"{len(df)=}")

    mt5_df = pd.DataFrame(
        {
            "time": df["transact_time"] // 1000,
            "bid": df["price"],
            "ask": df["price"],
            "last": df["price"],
            "volume": df["quantity"],
            "time_msc": df["transact_time"],
            "flags": 0,
            "volume_real": df["quantity"],
        }
    )

    start = datetime.fromtimestamp(mt5_df.iloc[0]["time"]).strftime("%Y_%m_%d")

    end = datetime.fromtimestamp(mt5_df.iloc[-1]["time"]).strftime("%Y_%m_%d")

    symbol = "BINANCE"

    file_name = f"{symbol}_{start}_to_{end}.parquet"

    mt5_df.to_parquet(
        rf"D:\TraderBot\LocalBackTester\TickData\Binance\{file_name}",
        index=False,
    )

    logging.info(f"Stored {len(mt5_df)} ticks")


def read_tick_data(path):
    import pandas as pd

    df = pd.read_parquet(path)
    logging.debug(f"{df.head(10)=}")
    logging.debug(f"{df.iloc[-10:]=}")
    logging.debug(f"{len(df)=}")


def test_tick_data():
    from BackTest.models import TickDataHandler

    path = r"D:\TraderBot\LocalBackTester\TickData\Opofinance\XAUUSD!_2025_11_03_to_2026_05_19.parquet"

    read_tick_data(path)
    tick_handler = TickDataHandler(path)
    logging.info(tick_handler.get_ticks_from_timstamp_range(1769543520, 1769543940))


def store_klines_from_mt5():
    from BackTest.methods import store_forex_data
    from ChartModule.models import TimeFrame
    from BackTest.models import CsvChart, KlineSource

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
