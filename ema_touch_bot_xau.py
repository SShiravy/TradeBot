from config import settings
settings.TELEGRAM_BOT_TOKEN = "8937168160:AAHtl4qXCSKXgT6YTSZEvYYDSHs3UcVqD5Y"

from TradingModule.reporter import TelegramReporter
from Forex import ForexAgent, ForexEmaTouchTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule.PositionHandlers.stepping_handler import SteppingHandlerForex
from TradingModule.trader_bot import TraderBot
from EmaTouchStrategy.ema_touch import EmaTouchFilter
from custom_logger import CustomLogger
import asyncio
import logging


CustomLogger(
    log_file=True, file_log_name="EmaTouchBot", consol_log_level=logging.DEBUG
)


xau_1h = ForexEmaTouchTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

xau_4h = ForexEmaTouchTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)


TelegramReporter().main_channel = "@crypto_result_1"
TraderBot("Ema Touch Bot", [xau_1h,xau_4h], report_time={"h": 20, "m": 12})


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
