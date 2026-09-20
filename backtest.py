from Settings.custom_logger import build_logger, LoggerConfig
from Settings.config import settings
import asyncio
import logging


logger = build_logger(
    LoggerConfig(
        name="root",
        log_file_name="BackTest",
        file_level=logging.DEBUG,
        telegram_channel=settings.TELEGRAM_TEST_CHANNEL,
        telegram_token=settings.TELEGRAM_TEST_BOT,
    )
)

if __name__ == "__main__":
    from BackTest import SignalBacktest, BacktestAgent

    # from BackTest.methods import *  # noqa: F403
    # from BackTest.StatisticalMethods import *  # noqa: F403
    from BackTest.configured_charts import SOLUSD_1m_5000_test, XAUUSD_1m_5000_test
    from Bots.DivergenceStrategy.configured_bots import xau_dxy_1m

    bot = xau_dxy_1m

    bot.chart = XAUUSD_1m_5000_test
    bot.second_chart = SOLUSD_1m_5000_test
    backtest_agent = BacktestAgent(
        bot.agent, [XAUUSD_1m_5000_test, SOLUSD_1m_5000_test]
    )

    simulator = SignalBacktest(bot, backtest_agent)
    asyncio.run(simulator.run())
