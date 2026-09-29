import asyncio
import logging
from TraderBot.bots_manager import BotsManager
from TelegramBot import TelegramReporter
from Settings import settings, build_logger, LoggerConfig
from Bots.CompositeStrategies.configured_bots import *


logger = build_logger(
    LoggerConfig(
        name="root",
        log_file_name="SR_CHoCH",
        file_level=logging.DEBUG,
        telegram_channel=settings.TELEGRAM_REPORT_CHANNEL,
        telegram_token=settings.TELEGRAM_BOT_TOKEN,
    )
)

crypto_sr_choch_bots = bitunix_sr_choch_bots

sr_choch_bots = [
    xau_sr_choch_5m_1m,
    eurusd_sr_choch_1h_5m,
    usdjpy_sr_choch_1h_5m,
    gbpusd_sr_choch_1h_5m,
    usdchf_sr_choch_1h_5m,
    audusd_sr_choch_1h_5m,
    usdcad_sr_choch_1h_5m,
    nzdusd_sr_choch_1h_5m,
]

reporter = TelegramReporter(
    "SR_CHoCH", settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_REPORT_CHANNEL
)
manager = BotsManager(
    "SR_CHoCH",
    reporter,
    [*sr_choch_bots, *bitunix_sr_choch_bots],
)

if __name__ == "__main__":
    asyncio.run(manager.start())
