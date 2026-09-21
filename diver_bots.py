import asyncio
import logging
from Bots.DivergenceStrategy.configured_bots import *
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
    "Divergence",
    reporter,
    [
        xau_rsi_double_diver_5m,
        xau_rsi_double_diver_5m,
        eurusd_rsi_double_diver_5m,
        eurusd_rsi_double_diver_15m,
        usdjpy_rsi_double_diver_5m,
        usdjpy_rsi_double_diver_15m,
        gbpusd_rsi_double_diver_5m,
        gbpusd_rsi_double_diver_15m,
        usdchf_rsi_double_diver_5m,
        usdchf_rsi_double_diver_15m,
        audusd_rsi_double_diver_5m,
        audusd_rsi_double_diver_15m,
        usdcad_rsi_double_diver_5m,
        usdcad_rsi_double_diver_15m,
        nzdusd_rsi_double_diver_5m,
        nzdusd_rsi_double_diver_15m,
    ],
)

if __name__ == "__main__":
    asyncio.run(manager.start())
