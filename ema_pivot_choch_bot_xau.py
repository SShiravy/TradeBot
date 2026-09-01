from config import settings
from TradingModule.reporter import TelegramReporter
from Forex import ForexAgent, ForexEmaPivotChochTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule.PositionHandlers.stepping_handler import SteppingHandlerForex
from TradingModule.trader_bot import TraderBot
from EmaPivotChochStrategy.ema_pivot_choch import EmaPivotChochFilter
from custom_logger import CustomLogger
import asyncio
import logging


CustomLogger(
    log_file=True, file_log_name="EmaPivotChochBot", consol_log_level=logging.DEBUG
)


xau_1m = ForexEmaPivotChochTradeConfig(
    chart=Chart("XAUUSD", TimeFrame.one_minute),
    htf_chart=Chart("XAUUSD", TimeFrame.five_minutes),
    n_ltf_candle_check=120,
    n_htf_candle_check=120,
    strategy=EmaPivotChochFilter(
        ema_periods=[20, 40, 60],
        htf_pivot_length=1,
        htf_backstep=2,
        atr_period=14,
        atr_multiplier=1.0,
        max_bars_after_pivot=100,
        choch_pivot_length=2,
        choch_backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,
        use_bos=False,
        use_choch=False,
        name="EmaPivotChoch",
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
TraderBot("Ema Pivot Choch Bot", [xau_1m], report_time={"h": 20, "m": 0})


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
