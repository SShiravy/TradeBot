from config import settings

settings.TELEGRAM_BOT_TOKEN = "8750919120:AAGwJ6n7_iE9twPx1464Ez8gac4_rxHn-l4"
from TradingModule.reporter import TelegramReporter
from TradingModule.trader_bot import TraderBot
from SRZoneModule.configs import *
from custom_logger import CustomLogger
import asyncio
import logging


CustomLogger(
    log_file=True, file_log_name="Forex_SR_ChoCh", consol_log_level=logging.DEBUG
)


TelegramReporter().main_channel = "@nader_support_resistance"

TraderBot(
    "SR_ChoCh",
    [
        usdjpy,
        eurusd,
        usdchf,
        gbp,
        audusd,
        usdcad,
        nzd,
        ada,
        ave,
        fil,
        atom,
        zec,
        iota,
        xtz,
        xrp,
        xmr,
        xlm,
        vet,
        uni,
        sol,
        mtc,
        ltc,
        lnk,
        dsh,
        dot,
        dog,
        btc,
        bsv,
        bnb,
        bch,
        avx,
    ],
    report_time={"h": 20, "m": 22},
)


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
