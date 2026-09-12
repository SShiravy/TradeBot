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
        xau_3m,
        eurusd_1h,
        eurusd_4h,
        usdjpy_1h,
        usdjpy_4h,
        gbpusd_1h,
        gbpusd_4h,
        usdchf_1h,
        usdchf_4h,
        audusd_1h,
        audusd_4h,
        usdcad_1h,
        usdcad_4h,
        nzdusd_1h,
        nzdusd_4h,
        adausd_1h,
        adausd_4h,
        aveusd_1h,
        aveusd_4h,
        filusd_1h,
        filusd_4h,
        atomusd_1h,
        atomusd_4h,
        zecusd_1h,
        zecusd_4h,
        iotausd_1h,
        iotausd_4h,
        xtzusd_1h,
        xtzusd_4h,
        xrpusd_1h,
        xrpusd_4h,
        xmrusd_1h,
        xmrusd_4h,
        xlmusd_1h,
        xlmusd_4h,
        vetusd_1h,
        vetusd_4h,
        uniusd_1h,
        uniusd_4h,
        solusd_1h,
        solusd_4h,
        mtcusd_1h,
        mtcusd_4h,
        ltcusd_1h,
        ltcusd_4h,
        lnkusd_1h,
        lnkusd_4h,
        dshusd_1h,
        dshusd_4h,
        dotusd_1h,
        dotusd_4h,
        dogusd_1h,
        dogusd_4h,
        btcusd_1h,
        btcusd_4h,
        bsvusd_1h,
        bsvusd_4h,
        bnbusd_1h,
        bnbusd_4h,
        bchusd_1h,
        bchusd_4h,
        avxusd_1h,
        avxusd_4h,
    ],
    report_time={"h": 20, "m": 0},
)


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
