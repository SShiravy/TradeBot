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

# uncomment to run this bot against a second MT5 terminal instance
# settings.METATRADER_TERMINAL_PATH = settings.SECOND_METATRADER_TERMINAL_PATH


xau_5m = ForexEmaPivotChochTradeConfig(
    chart=Chart("XAUUSD", TimeFrame.five_minutes),
    htf_chart=Chart("XAUUSD", TimeFrame.one_hour),
    n_candle_check=1500,
    strategy=EmaPivotChochFilter(
        ema_periods=[40, 131, 278],
        htf_pivot_length=2,
        htf_backstep=2,
        atr_period=14,
        atr_multiplier=1.0,
        max_bars_after_pivot=100,
        choch_pivot_length=2,
        choch_backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,  # True -> wait for price to retrace to the fib level | False -> signal as soon as the CHoCH/BOS break happens
        use_bos=True,  # True -> accept BOS (continuation) as well as CHoCH | False -> only genuine CHoCH breaks
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

TelegramReporter().main_channel = "@nader_support_resistance"
TraderBot("Ema Pivot Choch Bot", [xau_5m], report_time={"h": 20, "m": 0})


if __name__ == "__main__":
    # from TradingModule.reporter import TelegramReporter
    # TelegramReporter().disable_reporting()

    asyncio.run(TraderBot().start())
