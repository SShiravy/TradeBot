from custom_logger import CustomLogger
import logging

CustomLogger(True, consol_log_level=logging.INFO)


def start_backtest():
    from BacktestModule import Backtest
    from BacktestModule.forex_configs import forex_five_m_diver
    # Check forex

    backtest = Backtest(forex_five_m_diver, 1000)
    backtest.start_backtest(show_image=True)


if __name__ == "__main__":
    start_backtest()
    # import asyncio
    # TODO: implement two days off in task , and one houre off
    # TODO: Trailing Stop report
    # TODO: sma ema check 
    # TODO: seperate sl tp for long short
    # TODO: position handler with MA and control tp sl with it
    # TODO: multiple loss in a row for long and short handler

    # asyncio.run(mio())

