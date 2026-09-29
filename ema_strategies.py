import asyncio
import logging
from TraderBot.bots_manager import BotsManager
from Settings import settings, build_logger, LoggerConfig
from Bots.EmaStrategy.configured_bots import *


logger = build_logger(
    LoggerConfig(
        name="root",
        log_file_name="EmaStrategies",
        file_level=logging.DEBUG,
        telegram_channel=settings.TELEGRAM_REPORT_CHANNEL,
        telegram_token=settings.TELEGRAM_BOT_TOKEN,
    )
)


# each strategy sends its signals to its own channel (ema_touch_reporter /
# ema_pivot_choch_reporter, set in Bots/EmaStrategy/configured_bots.py) -
# the manager's own reporter below is only for system-level messages
# (errors, heartbeat, PnL summaries), not per-signal reports.
manager = BotsManager(
    "EmaStrategies",
    ema_touch_reporter,
    [*ema_touch_bots, *ema_pivot_choch_bots],
)

if __name__ == "__main__":
    asyncio.run(manager.start())
