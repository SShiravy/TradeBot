from config import settings

settings.TELEGRAM_BOT_TOKEN = "8937168160:AAHtl4qXCSKXgT6YTSZEvYYDSHs3UcVqD5Y"

from TradingModule.reporter import TelegramReporter
from TradingModule.trader_bot import TraderBot
from EmaTouchStrategy.configs import *
from custom_logger import CustomLogger
import asyncio
import logging


CustomLogger(log_file=True, file_log_name="EmaTouchBot", consol_log_level=logging.DEBUG)


TelegramReporter().main_channel = "@crypto_result_1"
TraderBot(
    "Ema Touch Bot",
    [
        xau_5m,
        xau_1h,
        xau_4h,
        eurusd_1h,
        usdjpy_1h,
        gbpusd_1h,
        usdchf_1h,
        audusd_1h,
        usdcad_1h,
        nzdusd_1h,
        adausd_1h,
        aveusd_1h,
        filusd_1h,
        atomusd_1h,
        apeusd_1h,
        zecusd_1h,
        neousd_1h,
        iotausd_1h,
        xtzusd_1h,
        xrpusd_1h,
        xmrusd_1h,
        xlmusd_1h,
        vetusd_1h,
        uniusd_1h,
        solusd_1h,
        mtcusd_1h,
        ltcusd_1h,
        lnkusd_1h,
        dshusd_1h,
        dotusd_1h,
        dogusd_1h,
        btcusd_1h,
        bsvusd_1h,
        bnbusd_1h,
        bchusd_1h,
        axsusd_1h,
        avxusd_1h,
        eurusd_4h,
        usdjpy_4h,
        gbpusd_4h,
        usdchf_4h,
        audusd_4h,
        usdcad_4h,
        nzdusd_4h,
        adausd_4h,
        aveusd_4h,
        filusd_4h,
        atomusd_4h,
        apeusd_4h,
        zecusd_4h,
        neousd_4h,
        iotausd_4h,
        xtzusd_4h,
        xrpusd_4h,
        xmrusd_4h,
        xlmusd_4h,
        vetusd_4h,
        uniusd_4h,
        solusd_4h,
        mtcusd_4h,
        ltcusd_4h,
        lnkusd_4h,
        dshusd_4h,
        dotusd_4h,
        dogusd_4h,
        btcusd_4h,
        bsvusd_4h,
        bnbusd_4h,
        bchusd_4h,
        axsusd_4h,
        avxusd_4h,
    ],
    report_time={"h": 20, "m": 12},
)


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
