from config import settings

settings.TELEGRAM_BOT_TOKEN = "8470075659:AAHxX4BDBiUeKB85REsL8RB7jpe8XeubDbc"
from TradingModule.reporter import TelegramReporter
from TradingModule.trader_bot import TraderBot
from DivergenceStrategy.rsi_choch_configs import *
from custom_logger import CustomLogger
import asyncio
import logging


CustomLogger(
    log_file=True, file_log_name="RSI_3Push_Choch", consol_log_level=logging.DEBUG
)


TelegramReporter().main_channel = "@three_push"
TraderBot(
    "RSI_3Push_Choch",
    [
        xau_5m_1m,
        xau_15m_1m,
        eurusd_5m_1m,
        usdjpy_5m_1m,
        gbpusd_5m_1m,
        usdchf_5m_1m,
        audusd_5m_1m,
        usdcad_5m_1m,
        nzdusd_5m_1m,
        eurusd_15m_1m,
        usdjpy_15m_1m,
        gbpusd_15m_1m,
        usdchf_15m_1m,
        audusd_15m_1m,
        usdcad_15m_1m,
        nzdusd_15m_1m,
        adausd_1h_5m,
        aveusd_1h_5m,
        filusd_1h_5m,
        atomusd_1h_5m,
        apeusd_1h_5m,
        zecusd_1h_5m,
        neousd_1h_5m,
        iotausd_1h_5m,
        xtzusd_1h_5m,
        xrpusd_1h_5m,
        xmrusd_1h_5m,
        xlmusd_1h_5m,
        vetusd_1h_5m,
        uniusd_1h_5m,
        solusd_1h_5m,
        mtcusd_1h_5m,
        ltcusd_1h_5m,
        lnkusd_1h_5m,
        dshusd_1h_5m,
        dotusd_1h_5m,
        dogusd_1h_5m,
        btcusd_1h_5m,
        bsvusd_1h_5m,
        bnbusd_1h_5m,
        bchusd_1h_5m,
        axsusd_1h_5m,
        avxusd_1h_5m,
        adausd_15m_1m,
        aveusd_15m_1m,
        filusd_15m_1m,
        atomusd_15m_1m,
        apeusd_15m_1m,
        zecusd_15m_1m,
        neousd_15m_1m,
        iotausd_15m_1m,
        xtzusd_15m_1m,
        xrpusd_15m_1m,
        xmrusd_15m_1m,
        xlmusd_15m_1m,
        vetusd_15m_1m,
        uniusd_15m_1m,
        solusd_15m_1m,
        mtcusd_15m_1m,
        ltcusd_15m_1m,
        lnkusd_15m_1m,
        dshusd_15m_1m,
        dotusd_15m_1m,
        dogusd_15m_1m,
        btcusd_15m_1m,
        bsvusd_15m_1m,
        bnbusd_15m_1m,
        bchusd_15m_1m,
        axsusd_15m_1m,
        avxusd_15m_1m,
    ],
    report_time={"h": 20, "m": 20},
)


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
