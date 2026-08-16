from config import settings

settings.TELEGRAM_BOT_TOKEN = "8470075659:AAHxX4BDBiUeKB85REsL8RB7jpe8XeubDbc"
from ChartModule.Indicators.models import SupportCandleConditions
from ChartModule.Indicators.rsi import RSI
from ChartModule.models import Chart, TimeFrame
from ChochQueueStrategy.choch_queue import ChochQueueFilter
from CompositeStrategies.rsi_3push_choch import Rsi3PushChochConfig
from DivergenceStrategy.oscillator_divergence import OscillatorDivergence
from Forex.agent import ForexAgent
from TradingModule.PositionHandlers.stepping_handler import SteppingHandlerForex
from TradingModule.reporter import TelegramReporter
from TradingModule.trader_bot import TraderBot
from custom_logger import CustomLogger
import asyncio
import logging


CustomLogger(
    log_file=True, file_log_name="RSI_3Push_Choch", consol_log_level=logging.DEBUG
)

xau = Rsi3PushChochConfig(
    rsi_chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    agent=ForexAgent(),
    strategy=OscillatorDivergence(
        RSI(),
        3,
        150,
        [],
        name="RSI_Double_Diver",
        long_support_conditions=SupportCandleConditions.RED_GREEN,
        short_support_conditions=SupportCandleConditions.GREEN_RED,
        body_candle=True,
        ignore_shadow_cross=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,  # True -> wait for price to retrace to the fib level | False -> signal as soon as the CHoCH/BOS break happens
        name="ChochQueue",
    ),
    bar_between_signals=2,
    same_line_source=True,
    n_candle_confirmation=100,
    n_candle_check=200,
    consider_position=True,
    position_handler=(
        SteppingHandlerForex(
            ForexAgent(),
            targets_ratio=[],
            targets_ratio_volumes=[],
            stoploss_pip=30,
            targets_in_pip=[20],
            targets_in_pip_volumes=[0.01],
            long_trade=True,
            short_trade=True,
            trail_stop=True,
        )
    ),
    heikingashi_chartdata=False,
)


audcad = Rsi3PushChochConfig(
    rsi_chart=Chart("AUDCAD!", TimeFrame.five_minutes),
    chart=Chart("AUDCAD!", TimeFrame.one_minute),
    agent=ForexAgent(),
    strategy=OscillatorDivergence(
        RSI(),
        3,
        150,
        [],
        name="RSI_Double_Diver",
        long_support_conditions=SupportCandleConditions.RED_GREEN,
        short_support_conditions=SupportCandleConditions.GREEN_RED,
        body_candle=True,
        ignore_shadow_cross=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,  # True -> wait for price to retrace to the fib level | False -> signal as soon as the CHoCH/BOS break happens
        name="ChochQueue",
    ),
    bar_between_signals=2,
    same_line_source=True,
    n_candle_confirmation=100,
    n_candle_check=200,
    consider_position=True,
    position_handler=(
        SteppingHandlerForex(
            ForexAgent(),
            targets_ratio=[],
            targets_ratio_volumes=[],
            stoploss_pip=5,
            targets_in_pip=[5],
            targets_in_pip_volumes=[0.01],
            long_trade=True,
            short_trade=True,
            trail_stop=True,
        )
    ),
    heikingashi_chartdata=False,
)


usdjpy = Rsi3PushChochConfig(
    rsi_chart=Chart("USDJPY!", TimeFrame.five_minutes),
    chart=Chart("USDJPY!", TimeFrame.one_minute),
    agent=ForexAgent(),
    strategy=OscillatorDivergence(
        RSI(),
        3,
        150,
        [],
        name="RSI_Double_Diver",
        long_support_conditions=SupportCandleConditions.RED_GREEN,
        short_support_conditions=SupportCandleConditions.GREEN_RED,
        body_candle=True,
        ignore_shadow_cross=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,  # True -> wait for price to retrace to the fib level | False -> signal as soon as the CHoCH/BOS break happens
        name="ChochQueue",
    ),
    bar_between_signals=2,
    same_line_source=True,
    n_candle_confirmation=100,
    n_candle_check=200,
    consider_position=True,
    position_handler=(
        SteppingHandlerForex(
            ForexAgent(),
            targets_ratio=[],
            targets_ratio_volumes=[],
            stoploss_pip=5,
            targets_in_pip=[5],
            targets_in_pip_volumes=[0.01],
            long_trade=True,
            short_trade=True,
            trail_stop=True,
        )
    ),
    heikingashi_chartdata=False,
)


eurgbp = Rsi3PushChochConfig(
    rsi_chart=Chart("EURGBP!", TimeFrame.five_minutes),
    chart=Chart("EURGBP!", TimeFrame.one_minute),
    agent=ForexAgent(),
    strategy=OscillatorDivergence(
        RSI(),
        3,
        150,
        [],
        name="RSI_Double_Diver",
        long_support_conditions=SupportCandleConditions.RED_GREEN,
        short_support_conditions=SupportCandleConditions.GREEN_RED,
        body_candle=True,
        ignore_shadow_cross=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,  # True -> wait for price to retrace to the fib level | False -> signal as soon as the CHoCH/BOS break happens
        name="ChochQueue",
    ),
    bar_between_signals=2,
    same_line_source=True,
    n_candle_confirmation=100,
    n_candle_check=200,
    consider_position=True,
    position_handler=(
        SteppingHandlerForex(
            ForexAgent(),
            targets_ratio=[],
            targets_ratio_volumes=[],
            stoploss_pip=5,
            targets_in_pip=[5],
            targets_in_pip_volumes=[0.01],
            long_trade=True,
            short_trade=True,
            trail_stop=True,
        )
    ),
    heikingashi_chartdata=False,
)


eurusd = Rsi3PushChochConfig(
    rsi_chart=Chart("EURUSD!", TimeFrame.five_minutes),
    chart=Chart("EURUSD!", TimeFrame.one_minute),
    agent=ForexAgent(),
    strategy=OscillatorDivergence(
        RSI(),
        3,
        150,
        [],
        name="RSI_Double_Diver",
        long_support_conditions=SupportCandleConditions.RED_GREEN,
        short_support_conditions=SupportCandleConditions.GREEN_RED,
        body_candle=True,
        ignore_shadow_cross=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,  # True -> wait for price to retrace to the fib level | False -> signal as soon as the CHoCH/BOS break happens
        name="ChochQueue",
    ),
    bar_between_signals=2,
    same_line_source=True,
    n_candle_confirmation=100,
    n_candle_check=200,
    consider_position=True,
    position_handler=(
        SteppingHandlerForex(
            ForexAgent(),
            targets_ratio=[],
            targets_ratio_volumes=[],
            stoploss_pip=7,
            targets_in_pip=[7],
            targets_in_pip_volumes=[0.01],
            long_trade=True,
            short_trade=True,
            trail_stop=True,
        )
    ),
    heikingashi_chartdata=False,
)


usdchf = Rsi3PushChochConfig(
    rsi_chart=Chart("USDCHF!", TimeFrame.five_minutes),
    chart=Chart("USDCHF!", TimeFrame.one_minute),
    agent=ForexAgent(),
    strategy=OscillatorDivergence(
        RSI(),
        3,
        150,
        [],
        name="RSI_Double_Diver",
        long_support_conditions=SupportCandleConditions.RED_GREEN,
        short_support_conditions=SupportCandleConditions.GREEN_RED,
        body_candle=True,
        ignore_shadow_cross=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,  # True -> wait for price to retrace to the fib level | False -> signal as soon as the CHoCH/BOS break happens
        name="ChochQueue",
    ),
    bar_between_signals=2,
    same_line_source=True,
    n_candle_confirmation=100,
    n_candle_check=200,
    consider_position=True,
    position_handler=(
        SteppingHandlerForex(
            ForexAgent(),
            targets_ratio=[],
            targets_ratio_volumes=[],
            stoploss_pip=4,
            targets_in_pip=[4],
            targets_in_pip_volumes=[0.01],
            long_trade=True,
            short_trade=True,
            trail_stop=True,
        )
    ),
    heikingashi_chartdata=False,
)


btc = Rsi3PushChochConfig(
    rsi_chart=Chart("BTCUSD", TimeFrame.five_minutes),
    chart=Chart("BTCUSD", TimeFrame.one_minute),
    agent=ForexAgent(),
    strategy=OscillatorDivergence(
        RSI(),
        3,
        150,
        [],
        name="RSI_Double_Diver",
        long_support_conditions=SupportCandleConditions.RED_GREEN,
        short_support_conditions=SupportCandleConditions.GREEN_RED,
        body_candle=True,
        ignore_shadow_cross=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,  # True -> wait for price to retrace to the fib level | False -> signal as soon as the CHoCH/BOS break happens
        name="ChochQueue",
    ),
    bar_between_signals=2,
    same_line_source=True,
    n_candle_confirmation=100,
    n_candle_check=200,
    consider_position=True,
    position_handler=(
        SteppingHandlerForex(
            ForexAgent(),
            targets_ratio=[],
            targets_ratio_volumes=[],
            stoploss_pip=60,
            targets_in_pip=[60],
            targets_in_pip_volumes=[0.01],
            long_trade=True,
            short_trade=True,
            trail_stop=True,
        )
    ),
    heikingashi_chartdata=False,
)


TelegramReporter().main_channel = "@three_push"
TraderBot(
    "RSI_3Push_Choch",
    [xau, audcad, usdjpy, eurgbp, eurusd, usdchf, btc],
    report_time={"h": 20, "m": 20},
)


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
