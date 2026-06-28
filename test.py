from custom_logger import CustomLogger
import logging
import asyncio


CustomLogger(True, consol_log_level=logging.DEBUG)


async def start_diver_backtest():
    from DivergenceStrategy.backtest_configs import (
        forex_diver_one_m,
    )

    await forex_diver_one_m.backtest(1000, show_image=True)


async def start_diver_crypto_backtest_pack():
    from BacktestModule.crypto_diver_pack import start_diver_crypto_backtest_pack

    await start_diver_crypto_backtest_pack(send_report=True)


async def start_fibochoch_backtest():
    from FiboChochStrategy.backtest_configs import forex_five_m

    await forex_five_m.backtest(2000, consider_positions=False)


async def start_fich_diver_backtest():
    from FiboChochDiverStrategy.backtest_configs import forex_one_m

    await forex_one_m.backtest(1000)


async def test_open_position():
    from TradingModule.trader_bot import TraderBot
    from TradingModule.reporter import TelegramReporter
    from ChartModule.models import MarketSide
    from DivergenceStrategy.backtest_configs import (
        forex_diver_one_m,
    )

    TelegramReporter().disable_reporting()
    the_config = forex_diver_one_m
    the_config.position_handler.short_trade = True
    the_config.position_handler.long_trade = True

    base_chartdata, second_chartdata = the_config.get_chartdata(100)
    diver_signal = the_config.strategy.generate_dummy_signal(
        base_chartdata, second_chartdata, MarketSide.BULLISH
    )
    logging.info(f"dummy diver signal: {diver_signal}")
    pos = await the_config.position_handler.generate_position(diver_signal)
    logging.info(f"position created from the dummy signal: {pos}")
    logging.info(
        f"opoen position: {the_config.agent.get_open_positions(chart=the_config.chart, comment_filter='')}"
    )
    await asyncio.gather(
        TraderBot(name="test opening pos", configs=[the_config]).manage()
    )


async def test_BitUnix_open_position():
    from TradingModule.trader_bot import TraderBot
    from config import settings
    from TradingModule.reporter import TelegramReporter
    from ChartModule.models import MarketSide
    from DivergenceStrategy.backtest_configs import (
        crypto_diver_five_m_sol,
        crypto_diver_five_m_near,
    )
    from BitUnix import BitUnixAgent

    agent = BitUnixAgent(settings.BITUNIX_API_KEY, settings.BITUNIX_API_SECRET_KEY)

    # from ChartModule.models import Chart, TimeFrame
    # from ChartModule.plot import ChartPlot
    # logging.debug(agent.bitunix_api.get_kline("BTCUSDT", "5m", limit=1))
    # chartdata = agent.get_chartdata(
    #     Chart("BTCUSDT", TimeFrame.five_minutes), n_bars=200
    # )
    # ChartPlot(chartdata, 200).show()  # type: ignore

    logging.debug(agent.bitunix_api.get_account())

    TelegramReporter().disable_reporting()
    the_config = crypto_diver_five_m_near
    the_config.position_handler.short_trade = True
    the_config.position_handler.long_trade = True

    base_chartdata, second_chartdata = the_config.get_chartdata(10)
    diver_signal = the_config.strategy.generate_dummy_signal(
        base_chartdata, second_chartdata, MarketSide.BULLISH
    )
    logging.info(f"dummy diver signal: {diver_signal}")
    pos = await the_config.position_handler.generate_position(diver_signal)
    if not pos:
        raise ValueError(f"{pos=}")
    await asyncio.gather(
        TraderBot(name="test opening pos", configs=[the_config]).manage()
    )


def test_handler_export_config():
    from DivergenceStrategy.backtest_configs import forex_diver_one_m

    logging.info(forex_diver_one_m.position_handler.export_config())


def store_mt5_data():
    from LocalBackTester.models import CsvChart
    from ChartModule.models import TimeFrame
    from LocalBackTester.methods import store_forex_data, plot_csv_kline, store_mt5_tick_data

    # store_mt5_tick_data()

    chart = CsvChart("XAUUSD!",timeframe=TimeFrame.one_minute,
                     csv_path="opo_XAUUSD_1m_99000_28_6.csv")
    store_forex_data(chart,99000)
    plot_csv_kline(chart)
    pass




if __name__ == "__main__":
    # asyncio.run(start_diver_crypto_backtest_pack())
    # asyncio.run(start_diver_backtest())
    # asyncio.run(start_fibochoch_backtest())
    # asyncio.run(start_fich_diver_backtest())

    # new_backtest()

    # store_mt5_data()

    # asyncio.run(test_open_position())

    # test_handler_export_config()

    # asyncio.run(test_BitUnix_open_position())

    from datetime import datetime
    print(datetime.fromtimestamp(1782604800))
