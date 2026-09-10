from config import settings
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


xau_5m = ForexEmaTouchTradeConfig(
    chart=Chart("XAUUSD", TimeFrame.five_minutes),
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

TelegramReporter().main_channel = settings.TELEGRAM_CRYPTO_CHANNEL_ID
TraderBot("Ema Touch Bot", [xau_5m], report_time={"h": 20, "m": 0})


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
