import asyncio
import logging
from Bots.DivergenceStrategy.configured_bots import (
    btc_sol_1m,
    btc_eth_1m,
    btc_rsi_1m,
    sol_rsi_1m,
)
from TraderBot import BotsManager
from TelegramBot import TelegramReporter
from Settings import settings, build_logger, LoggerConfig

logger = build_logger(
    LoggerConfig(
        name="root",
        log_file_name="DivergenceBots",
        file_level=logging.DEBUG,
        telegram_channel=settings.TELEGRAM_REPORT_CHANNEL,
        telegram_token=settings.TELEGRAM_BOT_TOKEN,
    )
)

reporter = TelegramReporter(
    "Divergence", settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_REPORT_CHANNEL
)
manager = BotsManager(
    "Divergence", reporter, [btc_sol_1m, btc_eth_1m, btc_rsi_1m, sol_rsi_1m]
)

if __name__ == "__main__":
    asyncio.run(manager.start())
