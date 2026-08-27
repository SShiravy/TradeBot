from config import settings
settings.TELEGRAM_BOT_TOKEN = "8937168160:AAHtl4qXCSKXgT6YTSZEvYYDSHs3UcVqD5Y"
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


xau = ForexEmaPivotChochTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    htf_chart=Chart("XAUUSD!", TimeFrame.one_hour),
    n_candle_check=1000,
    strategy=EmaPivotChochFilter(
        ema_periods=[20, 40, 60],
        htf_pivot_length=2,
        htf_backstep=2,
        atr_period=14,
        atr_multiplier=3.0,
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

audcad = ForexEmaPivotChochTradeConfig(
    chart=Chart("AUDCAD!", TimeFrame.five_minutes),
    htf_chart=Chart("AUDCAD!", TimeFrame.one_hour),
    n_candle_check=1000,
    strategy=EmaPivotChochFilter(
        ema_periods=[20, 40, 60],
        htf_pivot_length=2,
        htf_backstep=2,
        atr_period=14,
        atr_multiplier=3.0,
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

usdjpy = ForexEmaPivotChochTradeConfig(
    chart=Chart("USDJPY!", TimeFrame.five_minutes),
    htf_chart=Chart("USDJPY!", TimeFrame.one_hour),
    n_candle_check=1000,
    strategy=EmaPivotChochFilter(
        ema_periods=[20, 40, 60],
        htf_pivot_length=2,
        htf_backstep=2,
        atr_period=14,
        atr_multiplier=3.0,
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


eurgbp = ForexEmaPivotChochTradeConfig(
    chart=Chart("EURGBP!", TimeFrame.five_minutes),
    htf_chart=Chart("EURGBP!", TimeFrame.one_hour),
    n_candle_check=1000,
    strategy=EmaPivotChochFilter(
        ema_periods=[20, 40, 60],
        htf_pivot_length=2,
        htf_backstep=2,
        atr_period=14,
        atr_multiplier=3.0,
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


eurusd = ForexEmaPivotChochTradeConfig(
    chart=Chart("EURUSD!", TimeFrame.five_minutes),
    htf_chart=Chart("EURUSD!", TimeFrame.one_hour),
    n_candle_check=1000,
    strategy=EmaPivotChochFilter(
        ema_periods=[20, 40, 60],
        htf_pivot_length=2,
        htf_backstep=2,
        atr_period=14,
        atr_multiplier=3.0,
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


btc = ForexEmaPivotChochTradeConfig(
    chart=Chart("BTCUSD", TimeFrame.five_minutes),
    htf_chart=Chart("BTCUSD", TimeFrame.one_hour),
    n_candle_check=1000,
    strategy=EmaPivotChochFilter(
        ema_periods=[20, 40, 60],
        htf_pivot_length=2,
        htf_backstep=2,
        atr_period=14,
        atr_multiplier=3.0,
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


usdchf = ForexEmaPivotChochTradeConfig(
    chart=Chart("USDCHF!", TimeFrame.five_minutes),
    htf_chart=Chart("USDCHF!", TimeFrame.one_hour),
    n_candle_check=1000,
    strategy=EmaPivotChochFilter(
        ema_periods=[20, 40, 60],
        htf_pivot_length=2,
        htf_backstep=2,
        atr_period=14,
        atr_multiplier=3.0,
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


TelegramReporter().main_channel = "@crypto_result_1"
TraderBot("Ema Pivot Choch Bot", [xau,audcad,usdjpy,eurgbp,eurusd,btc,usdchf], report_time={"h": 20, "m": 0})


if __name__ == "__main__":
    # from TradingModule.reporter import TelegramReporter
    # TelegramReporter().disable_reporting()

    asyncio.run(TraderBot().start())
