import asyncio
import logging
from Bots.DivergenceStrategy.diver_configs import xau_jpy_1m, xau_dxy_1m, xau_rsi_1m
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
manager = BotsManager("Divergence", reporter, [xau_jpy_1m, xau_dxy_1m, xau_rsi_1m])

if __name__ == "__main__":
    asyncio.run(manager.start())
