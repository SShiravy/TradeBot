from BitUnix.agent import BitUnixAgent
from BitUnix.bot_configs import BitUnixChochQueueTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule.PositionHandlers.stepping_handler import SteppingHandlerCrypto
from TradingModule.reporter import TelegramReporter
from TradingModule.trader_bot import TraderBot
from ChochQueueStrategy.choch_queue import ChochQueueFilter
from custom_logger import CustomLogger
from config import settings
import asyncio
import logging

CustomLogger(
    log_file=True, file_log_name="ChochQueueCryptoBot", consol_log_level=logging.DEBUG
)

bitunix_agent = BitUnixAgent(settings.BITUNIX_API_KEY, settings.BITUNIX_API_SECRET_KEY)

choch_five_m_sol = BitUnixChochQueueTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.five_minutes),
    strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        retrace_fib=0.5,
        use_wick=True,
        use_fibo_filter=False,  # True -> wait for price to retrace to the fib level | False -> signal as soon as the CHoCH/BOS break happens
        name="ChochQueue",
    ),
    position_handler=SteppingHandlerCrypto(
        bitunix_agent,
        leverage=30,
        stoploss_percent=0.7,
        targets_ratio=[1, 2, 3],
        initial_volume=0.1,
        long_trade=False,
        short_trade=False,
        trail_stop=True,
    ),
    agent=bitunix_agent,
    heikingashi_chartdata=False,
)


TelegramReporter().main_channel = settings.TELEGRAM_CRYPTO_CHANNEL_ID
TraderBot(
    "Choch Queue Crypto Bot",
    [choch_five_m_sol],
    report_time={"h": 20, "m": 1},
)


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
