from custom_logger import CustomLogger
import logging


CustomLogger(True, consol_log_level=logging.DEBUG)


async def start_diver_backtest():
    from DivergenceStrategy.backtest_configs import one_h_diver

    await one_h_diver.backtest(1000, len_sub_data=100)


async def start_fibochoch_backtest():
    from FiboChochStrategy.backtest_configs import coinex_one_h

    await coinex_one_h.backtest(1000, 50)


if __name__ == "__main__":
    import asyncio

    # asyncio.run(start_diver_backtest())
    asyncio.run(start_fibochoch_backtest())

    # new_backtest()


# TODO: partial close
# TODO: position handler with MA and control tp sl with it
# TODO: multiple loss in a row for long and short handler
# TODO: pos open candle should not check in position handler
# TODO: add backtest bot
# TODO: check market is open not woking! last tick is just now always
