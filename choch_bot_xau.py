from config import settings

settings.METATRADER_TERMINAL_PATH = settings.SECOND_METATRADER_TERMINAL_PATH
settings.TELEGRAM_BOT_TOKEN = "8750919120:AAGwJ6n7_iE9twPx1464Ez8gac4_rxHn-l4"
from TradingModule.reporter import TelegramReporter
from Forex import ForexAgent, ForexChochQueueTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule.PositionHandlers.stepping_handler import SteppingHandlerForex
from TradingModule.trader_bot import TraderBot
from ChochQueueStrategy.choch_queue import ChochQueueFilter
from custom_logger import CustomLogger
import asyncio
import logging


CustomLogger(
    log_file=True, file_log_name="ChochQueueBot", consol_log_level=logging.DEBUG
)

one_m = ForexChochQueueTradeConfig(
    chart=Chart("XAUUSD", TimeFrame.one_minute),
    strategy=ChochQueueFilter(
        pivot_length=50,
        backstep=2,
        retrace_fib=0.5,
        use_wick=True,
        use_fibo_filter=False,  # True -> wait for price to retrace to the fib level | False -> signal as soon as the CHoCH/BOS break happens
        name="ChochQueue",
    ),
    bar_between_signals=2,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=15,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

TelegramReporter().main_channel = "@nader_support_resistance"
TraderBot("Choch Queue Bot", [one_m], report_time={"h": 20, "m": 0})


if __name__ == "__main__":
    # from TradingModule.reporter import TelegramReporter
    # TelegramReporter().disable_reporting()

    asyncio.run(TraderBot().start())
