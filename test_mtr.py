from config import settings

settings.TELEGRAM_BOT_TOKEN = "8937168160:AAHtl4qXCSKXgT6YTSZEvYYDSHs3UcVqD5Y"
from AutoTrendlineModule.auto_trendline import AutoTrendlines
from CompositeStrategies.mtr_strategy import MTRConfig
from Forex.agent import ForexAgent
from TradingModule.reporter import TelegramReporter
from ChartModule import Chart, TimeFrame
from TradingModule.PositionHandlers.stepping_handler import SteppingHandlerForex
from TradingModule.trader_bot import TraderBot
from custom_logger import CustomLogger
import asyncio
import logging


CustomLogger(log_file=True, file_log_name="MTR", consol_log_level=logging.DEBUG)

sol = MTRConfig(
    chart=Chart("SOLUSD", TimeFrame.one_minute),
    strategy=None,
    bar_between_signals=2,
    consider_position=False,
    mtr_indicator=AutoTrendlines(
        depth=15,
        backstep=2,
        atr_len=14,
        touch_mult=0.5,
        break_mult=0.4,
        min_touches=2,
        min_line_bars=5,
        max_span_bars=150,
        stale_bars=50,
        max_total_lines=500,
        max_active_per_dir=50,
        merge_projection_bars=50,
        display_only_aligned=False,
    ),
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


audcad = MTRConfig(
    chart=Chart("AUDCAD!", TimeFrame.one_minute),
    strategy=None,
    bar_between_signals=2,
    consider_position=False,
    mtr_indicator=AutoTrendlines(
        depth=15,
        backstep=2,
        atr_len=14,
        touch_mult=0.5,
        break_mult=0.4,
        min_touches=2,
        min_line_bars=5,
        max_span_bars=150,
        stale_bars=50,
        max_total_lines=500,
        max_active_per_dir=50,
        merge_projection_bars=50,
        display_only_aligned=False,
    ),
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


eurgbp = MTRConfig(
    chart=Chart("EURGBP!", TimeFrame.one_minute),
    strategy=None,
    bar_between_signals=2,
    consider_position=False,
    mtr_indicator=AutoTrendlines(
        depth=15,
        backstep=2,
        atr_len=14,
        touch_mult=0.5,
        break_mult=0.4,
        min_touches=2,
        min_line_bars=5,
        max_span_bars=150,
        stale_bars=50,
        max_total_lines=500,
        max_active_per_dir=50,
        merge_projection_bars=50,
        display_only_aligned=False,
    ),
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


usdjpy = MTRConfig(
    chart=Chart("USDJPY!", TimeFrame.one_minute),
    strategy=None,
    bar_between_signals=2,
    consider_position=False,
    mtr_indicator=AutoTrendlines(
        depth=15,
        backstep=2,
        atr_len=14,
        touch_mult=0.5,
        break_mult=0.4,
        min_touches=2,
        min_line_bars=5,
        max_span_bars=150,
        stale_bars=50,
        max_total_lines=500,
        max_active_per_dir=50,
        merge_projection_bars=50,
        display_only_aligned=False,
    ),
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


eur = MTRConfig(
    chart=Chart("EURUSD!", TimeFrame.one_minute),
    strategy=None,
    bar_between_signals=2,
    consider_position=False,
    mtr_indicator=AutoTrendlines(
        depth=15,
        backstep=2,
        atr_len=14,
        touch_mult=0.5,
        break_mult=0.4,
        min_touches=2,
        min_line_bars=5,
        max_span_bars=150,
        stale_bars=50,
        max_total_lines=500,
        max_active_per_dir=50,
        merge_projection_bars=50,
        display_only_aligned=False,
    ),
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


usdchf = MTRConfig(
    chart=Chart("USDCHF!", TimeFrame.one_minute),
    strategy=None,
    bar_between_signals=2,
    consider_position=False,
    mtr_indicator=AutoTrendlines(
        depth=15,
        backstep=2,
        atr_len=14,
        touch_mult=0.5,
        break_mult=0.4,
        min_touches=2,
        min_line_bars=5,
        max_span_bars=150,
        stale_bars=50,
        max_total_lines=500,
        max_active_per_dir=50,
        merge_projection_bars=50,
        display_only_aligned=False,
    ),
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


btc = MTRConfig(
    chart=Chart("BTCUSD!", TimeFrame.one_minute),
    strategy=None,
    bar_between_signals=2,
    consider_position=False,
    mtr_indicator=AutoTrendlines(
        depth=15,
        backstep=2,
        atr_len=14,
        touch_mult=0.5,
        break_mult=0.4,
        min_touches=2,
        min_line_bars=5,
        max_span_bars=150,
        stale_bars=50,
        max_total_lines=500,
        max_active_per_dir=50,
        merge_projection_bars=50,
        display_only_aligned=False,
    ),
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


xau = MTRConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    strategy=None,
    bar_between_signals=2,
    consider_position=False,
    mtr_indicator=AutoTrendlines(
        depth=15,
        backstep=2,
        atr_len=14,
        touch_mult=0.5,
        break_mult=0.4,
        min_touches=2,
        min_line_bars=5,
        max_span_bars=150,
        stale_bars=50,
        max_total_lines=500,
        max_active_per_dir=50,
        merge_projection_bars=50,
        display_only_aligned=False,
    ),
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

TraderBot("Choch Bot", 
          [
            xau, 
            sol,
            audcad,
            eurgbp,
            usdjpy,
            eur,
            usdchf,
            btc,
            xau
        ], report_time={"h": 20, "m": 0})


if __name__ == "__main__":
    # from TradingModule.reporter import TelegramReporter
    # TelegramReporter().disable_reporting()

    asyncio.run(TraderBot().start())
