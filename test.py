from LocalBackTester.methods import store_mt5_tick_data
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


def test_handler_export_config():
    from DivergenceStrategy.backtest_configs import forex_diver_one_m

    logging.info(forex_diver_one_m.position_handler.export_config())


if __name__ == "__main__":
    # asyncio.run(start_diver_crypto_backtest_pack())
    # asyncio.run(start_diver_backtest())
    # asyncio.run(start_fibochoch_backtest())
    # asyncio.run(start_fich_diver_backtest())

    # new_backtest()

    # store_mt5_tick_data()

    asyncio.run(test_open_position())
    # test_handler_export_config()
