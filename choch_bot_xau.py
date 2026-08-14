from AutoTrendlineModule.auto_trendline import AutoTrendlines, BreakLogicMode
from SRZoneModule.sr_zone import SRZones
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

auto_trendlines = AutoTrendlines(
    depth=15,
    backstep=2,
    atr_len=14,
    touch_mult=0.5,
    break_mult=0.4,
    min_touches=2,
    min_line_bars=15,
    max_span_bars=150,
    stale_bars=50,
    max_total_lines=300,
    max_active_per_dir=50,
    merge_projection_bars=50,
    display_only_aligned=False,
    break_logic_mode=BreakLogicMode.CLOSE_CROSS
)

one_m = ForexChochQueueTradeConfig(
    chart=Chart("SOLUSD", TimeFrame.one_minute),
    n_candle_check=1000,
    strategy=ChochQueueFilter(
        pivot_length=2,
        confirmation_indicators=[auto_trendlines],
        backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,  # True -> wait for price to retrace to the fib level | False -> signal as soon as the CHoCH/BOS break happens
        name="ChochQueue",
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

sr_zones = SRZones(
    depth=15,
    backstep=2,
    max_candidates=150,
    atr_len=14,
    atr_median_lookback=21,
    radius_factor=1.0,
    min_radius_mult=0.25,
    max_radius_mult=3.0,
    merge_nearby=True,
    merge_interval_bars=1000,
    width_mult=1.0,
    fallback_width_factor=0.35,
    max_zone_touches=5,
    max_zone_breaks=1,
    zone_break_bars=2,
    min_bars_between_touches=3,
    max_bars_between_touches=200,
    prune_after_bars=4500,
)

xau_1m = ForexChochQueueTradeConfig(
    chart=Chart("XAUUSD", TimeFrame.one_minute),
    strategy=ChochQueueFilter(
        pivot_length=50,
        backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,  # True -> wait for price to retrace to the fib level | False -> signal as soon as the CHoCH/BOS break happens
        name="ChochQueue",
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
TraderBot("Choch Queue Bot", [one_m, xau_1m], report_time={"h": 20, "m": 0})


if __name__ == "__main__":
    # from TradingModule.reporter import TelegramReporter
    # TelegramReporter().disable_reporting()

    asyncio.run(TraderBot().start())
