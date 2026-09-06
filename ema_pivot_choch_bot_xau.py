from config import settings
from TradingModule.reporter import TelegramReporter
from TradingModule.trader_bot import TraderBot
from EmaPivotChochStrategy.configs import *
from custom_logger import CustomLogger
import asyncio
import logging


CustomLogger(
    log_file=True, file_log_name="EmaPivotChochBot", consol_log_level=logging.DEBUG
)


TelegramReporter().main_channel = settings.TELEGRAM_CRYPTO_CHANNEL_ID
TraderBot(
    "Ema Pivot Choch Bot",
    [
        eurusd,
        usdjpy,
        gbpusd,
        usdchf,
        audusd,
        usdcad,
        nzdusd,
        adausd,
        aveusd,
        filusd,
        atomusd,
        apeusd,
        zecusd,
        neousd,
        iotausd,
        xtzusd,
        xrpusd,
        xmrusd,
        xlmusd,
        vetusd,
        uniusd,
        solusd,
        mtcusd,
        ltcusd,
        lnkusd,
        dshusd,
        dotusd,
        dogusd,
        btcusd,
        bsvusd,
        bnbusd,
        bchusd,
        axsusd,
        avxusd,
    ],
    report_time={"h": 20, "m": 0},
)


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
