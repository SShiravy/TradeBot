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
    from BackTest.configured_charts import BTCUSD_1m_99000, SOLUSD_1m_99000
    from Bots.CompositeStrategies.configured_bots import *
    from Bots.EmaStrategy.configured_bots import xau_3m
    from Bots.ChochStrategy.configured_bots import xau_choch_1m

    bot = xau_3m

    bot.chart = BTCUSD_1m_99000
    bot.htf_chart = SOLUSD_1m_99000
    backtest_agent = BacktestAgent(bot.agent, [SOLUSD_1m_99000, BTCUSD_1m_99000])

    simulator = SignalBacktest(bot, backtest_agent)
    asyncio.run(simulator.run())
