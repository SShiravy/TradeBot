from custom_logger import CustomLogger
import logging


CustomLogger(True, consol_log_level=logging.DEBUG)


async def start_fibochoch_backtest():
    from BacktestModule import Backtest
    from BacktestModule.FiboChochStrategy.forex_configs import five_m

    # Check forex
    backtest = Backtest(five_m, 900)
    await backtest.start_backtest(show_image=True)


async def start_diver_backtest():
    from BacktestModule import Backtest
    from BacktestModule.DivergenceStrategy.forex_configs import forex_one_m_diver

    # Check forex
    backtest = Backtest(forex_one_m_diver, 100)
    await backtest.start_backtest(show_image=True)


if __name__ == "__main__":
    # fibo_test()
    # test_moving_color()
    import asyncio

    asyncio.run(start_fibochoch_backtest())
    # TODO: partial close
    # TODO: position handler with MA and control tp sl with it
    # TODO: multiple loss in a row for long and short handler
    # TODO: pos open candle should not check in position handler
    # TODO: add backtest bot
    # TODO: check market is open not woking! last tick is just now always

    # asyncio.run(start_diver_backtest())
