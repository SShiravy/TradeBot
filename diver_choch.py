import asyncio
import logging
from TraderBot import BotsManager
from TelegramBot import TelegramReporter
from Settings import settings, build_logger, LoggerConfig
from Bots.CompositeStrategies.configured_bots import *


logger = build_logger(
    LoggerConfig(
        name="root",
        log_file_name="DivergenceBots",
        file_level=logging.DEBUG,
        telegram_channel=settings.TELEGRAM_REPORT_CHANNEL,
        telegram_token=settings.TELEGRAM_BOT_TOKEN,
    )
)


rsi_diver_choch_bots = [
    xau_5m_rsi_choch,
    xau_15m_rsi_choch,
    eurusd_5m_rsi_choch,
    eurusd_15m_rsi_choch,
    usdjpy_5m_rsi_choch,
    usdjpy_15m_rsi_choch,
    gbpusd_5m_rsi_choch,
    gbpusd_15m_rsi_choch,
]

rsi_double_diver_choch_bots = [
    eurusd_5m_rsi_double_diver_choch,
    eurusd_15m_rsi_double_diver_choch,
    usdjpy_5m_rsi_double_diver_choch,
    usdjpy_15m_rsi_double_diver_choch,
    gbpusd_5m_rsi_double_diver_choch,
    gbpusd_15m_rsi_double_diver_choch,
    usdchf_5m_rsi_double_diver_choch,
    usdchf_15m_rsi_double_diver_choch,
    audusd_5m_rsi_double_diver_choch,
    audusd_15m_rsi_double_diver_choch,
    usdcad_5m_rsi_double_diver_choch,
    usdcad_15m_rsi_double_diver_choch,
    nzdusd_5m_rsi_double_diver_choch,
    nzdusd_15m_rsi_double_diver_choch,
]


reporter = TelegramReporter(
    "Divergence", settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_REPORT_CHANNEL
)
manager = BotsManager(
    "Divergence",
    reporter,
    [*rsi_double_diver_choch_bots, *rsi_diver_choch_bots],
)

if __name__ == "__main__":
    asyncio.run(manager.start())
