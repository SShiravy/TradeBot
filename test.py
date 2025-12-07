from custom_logger import CustomLogger
import logging


CustomLogger(True, consol_log_level=logging.DEBUG)


async def start_diver_backtest():
    from BacktestModule import Backtest
    from DivergenceStrategy.backtest_configs import coinex_one_h_diver

    # Check forex
    backtest = Backtest(coinex_one_h_diver, 1000)
    await backtest.start_backtest(show_image=True)


async def start_fibochoch_backtest():
    from BacktestModule import Backtest
    from FiboChochStrategy.backtest_configs import coinex_one_h

    # Check forex
    backtest = Backtest(coinex_one_h, 1000)
    await backtest.start_backtest(show_image=True)


def new_backtest():
    import asyncio
    from BacktestModule.backtest_new_version import Backtest
    from FiboChochStrategy.backtest_configs import coinex_five_m

    async def test():
        await Backtest(coinex_five_m, show_image=True).start_task_backtest()

    asyncio.run(test())


if __name__ == "__main__":
    # asyncio.run(start_diver_backtest())
    # asyncio.run(start_fibochoch_backtest())

    new_backtest()


# TODO: partial close
# TODO: position handler with MA and control tp sl with it
# TODO: multiple loss in a row for long and short handler
# TODO: pos open candle should not check in position handler
# TODO: add backtest bot
# TODO: check market is open not woking! last tick is just now always
