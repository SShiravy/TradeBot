from custom_logger import CustomLogger
import logging

CustomLogger(True, consol_log_level=logging.INFO)


def start_backtest():
    from BacktestModule import Backtest
    from BacktestModule.coinex_configs import coinex_five_m_diver

    backtest = Backtest(coinex_five_m_diver, 500)
    backtest.start_backtest(show_image=True)


if __name__ == "__main__":
    start_backtest()
    # import asyncio
    # TODO: check forex two chart same candle time in divergence
    # TODO: wrong short sl triggering
    # TODO: worong sl trailing in reports
    # asyncio.run(mio())
