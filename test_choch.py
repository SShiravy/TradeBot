from config import settings

settings.TELEGRAM_BOT_TOKEN = "8937168160:AAHtl4qXCSKXgT6YTSZEvYYDSHs3UcVqD5Y"
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
    log_file=True, file_log_name="ChochBot", consol_log_level=logging.DEBUG
)


solusd = ForexChochQueueTradeConfig(
    chart=Chart("SOLUSD", TimeFrame.one_minute),
    n_candle_check=100,
    strategy=ChochQueueFilter(
        use_bos=False,
        pivot_length=2,
        confirmation_indicators=[],
        backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,
        name="Choch",
        min_choch_candles=2
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=10,
        targets_ratio=[],
        targets_in_pip=[10],
        targets_in_pip_volumes=[0.01],
        targets_ratio_volumes=[],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)


audcad = ForexChochQueueTradeConfig(
    chart=Chart("AUDCAD!", TimeFrame.one_minute),
    n_candle_check=100,
    strategy=ChochQueueFilter(
        use_bos=False,
        pivot_length=2,
        confirmation_indicators=[],
        backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,
        name="Choch",
        min_choch_candles=2
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=10,
        targets_ratio=[],
        targets_in_pip=[10],
        targets_in_pip_volumes=[0.01],
        targets_ratio_volumes=[],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

eurgbp = ForexChochQueueTradeConfig(
    chart=Chart("EURGBP!", TimeFrame.one_minute),
    n_candle_check=100,
    strategy=ChochQueueFilter(
        use_bos=False,
        pivot_length=2,
        confirmation_indicators=[],
        backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,
        name="Choch",
        min_choch_candles=2
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=10,
        targets_ratio=[],
        targets_in_pip=[10],
        targets_in_pip_volumes=[0.01],
        targets_ratio_volumes=[],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)


usdjpy = ForexChochQueueTradeConfig(
    chart=Chart("USDJPY!", TimeFrame.one_minute),
    n_candle_check=100,
    strategy=ChochQueueFilter(
        use_bos=False,
        pivot_length=2,
        confirmation_indicators=[],
        backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,
        name="Choch",
        min_choch_candles=2
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=10,
        targets_ratio=[],
        targets_in_pip=[10],
        targets_in_pip_volumes=[0.01],
        targets_ratio_volumes=[],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

eurusd = ForexChochQueueTradeConfig(
    chart=Chart("EURUSD!", TimeFrame.one_minute),
    n_candle_check=100,
    strategy=ChochQueueFilter(
        use_bos=False,
        pivot_length=2,
        confirmation_indicators=[],
        backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,
        name="Choch",
        min_choch_candles=2
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=10,
        targets_ratio=[],
        targets_in_pip=[10],
        targets_in_pip_volumes=[0.01],
        targets_ratio_volumes=[],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)


usdchf = ForexChochQueueTradeConfig(
    chart=Chart("USDCHF!", TimeFrame.one_minute),
    n_candle_check=100,
    strategy=ChochQueueFilter(
        use_bos=False,
        pivot_length=2,
        confirmation_indicators=[],
        backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,
        name="Choch",
        min_choch_candles=2
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=10,
        targets_ratio=[],
        targets_in_pip=[10],
        targets_in_pip_volumes=[0.01],
        targets_ratio_volumes=[],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)


btc = ForexChochQueueTradeConfig(
    chart=Chart("BTCUSD", TimeFrame.one_minute),
    n_candle_check=100,
    strategy=ChochQueueFilter(
        use_bos=False,
        pivot_length=2,
        confirmation_indicators=[],
        backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,
        name="Choch",
        min_choch_candles=2
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=10,
        targets_ratio=[],
        targets_in_pip=[10],
        targets_in_pip_volumes=[0.01],
        targets_ratio_volumes=[],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

xau = ForexChochQueueTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    strategy=ChochQueueFilter(
        use_bos=False,
        pivot_length=2,
        confirmation_indicators=[],
        backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,
        name="Choch",
        min_choch_candles=2
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=10,
        targets_ratio=[],
        targets_in_pip=[10],
        targets_in_pip_volumes=[0.01],
        targets_ratio_volumes=[],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

TelegramReporter().main_channel = "@crypto_result_1"
TraderBot(
    "Choch Queue Bot",
    [solusd, audcad, eurgbp, usdjpy, eurusd, usdchf, btc, xau],
    report_time={"h": 20, "m": 0},
)


if __name__ == "__main__":
    # from TradingModule.reporter import TelegramReporter
    # TelegramReporter().disable_reporting()

    asyncio.run(TraderBot().start())
