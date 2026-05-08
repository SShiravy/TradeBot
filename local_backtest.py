from LocalBackTester.agent import LocalAgent
from LocalBackTester.all_charts import BTCUSDT_1h_2024_9, SOLUSDT_1h_2024_9
from ChartModule.plot import ChartPlot
from custom_logger import CustomLogger
import logging


CustomLogger(True, consol_log_level=logging.DEBUG)


def plot_csv_kline():
    agent = LocalAgent()
    chartdata = agent.get_chartdata(SOLUSDT_1h_2024_9)
    ChartPlot(chartdata, len(chartdata.candles)).show()  # type: ignore


async def crypto_backtest():
    from Coinex.bot_config import CoinexDiverTradeConfig
    from DivergenceStrategy.divergence import Divergence
    from TradingModule.PositionHandlers.ratio_handlers import SlTpRatioCrypto

    local_agent = LocalAgent()
    config = CoinexDiverTradeConfig(
        chart=SOLUSDT_1h_2024_9,
        second_chart=BTCUSDT_1h_2024_9,
        strategy=Divergence(3, 500, [], name="CoinexDiver", inverse_diver_long=True),
        position_handler=SlTpRatioCrypto(
            local_agent,
            ratio=1.5,
            stoploss_percent=0.5,
            initial_volume=10,
            leverage=10,
            long_trade=False,
            short_trade=False,
        ),
        agent=local_agent,  # type: ignore
        heikingashi_chartdata=True,
    )

    await config.backtest(BTCUSDT_1h_2024_9.number_of_bars, 200)


def store_meta_klines():
    from LocalBackTester.methods import store_forex_data
    from ChartModule.models import TimeFrame
    from LocalBackTester.models import CsvChart

    symbol = "BTCUSD"
    len_bar = 99000
    timeframe = TimeFrame.one_minute

    chart = CsvChart(symbol,timeframe,
                csv_path=rf"D:\TraderBot\LocalBackTester\KlinesCSV\Opofincance\opo_{symbol.replace('!','')}_{timeframe.value}_{len_bar}.csv")
    
    store_forex_data(chart,n_bars=len_bar)
    # TODO: make it better method by adding above params to store_forex_data function
    


if __name__ == "__main__":
    # plot_csv_kline()

    # import asyncio
    # asyncio.run(crypto_backtest())

    store_meta_klines()



# TODO: search and replace candle.time.timestamp() with candle.timestamp
