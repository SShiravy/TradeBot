from custom_logger import CustomLogger
import logging

CustomLogger(True, consol_log_level=logging.INFO)


async def start_backtest():
    from BacktestModule import Backtest
    from BacktestModule.forex_configs import forex_five_m_cvd
    from BacktestModule.coinex_configs import coinex_one_h_diver

    # Check forex
    backtest = Backtest(forex_five_m_cvd, 1000)
    await backtest.start_backtest(show_image=True)


if __name__ == "__main__":
    import asyncio

    # TODO: seperate sl tp for long short
    # TODO: position handler with MA and control tp sl with it
    # TODO: multiple loss in a row for long and short handler
    # TODO: pos open candle should not check in position handler
    # TODO: pip on pos handler and config
    # TODO: add backtest bot

    asyncio.run(start_backtest())
