from ChartModule.Indicators.models import SupportCandleConditions
from ChartModule.Indicators.rsi import RSI
from ChochQueueStrategy.choch_queue import ChochQueueFilter
from DivergenceStrategy.oscillator_divergence import OscillatorDivergence
from config import settings

settings.METATRADER_TERMINAL_PATH = settings.SECOND_METATRADER_TERMINAL_PATH
from Forex import ForexAgent
from ChartModule import Chart, TimeFrame
from CompositeStrategies.rsi_diver_choch import RsiDiverChochConfig
from TradingModule.PositionHandlers.stepping_handler import SteppingHandlerForex
from TradingModule.trader_bot import TraderBot
from custom_logger import CustomLogger
import asyncio
import logging


CustomLogger(
    log_file=True, file_log_name="ForexDiverBot", consol_log_level=logging.DEBUG
)
xau_5m = RsiDiverChochConfig(
        rsi_chart=Chart("XAUUSD!", TimeFrame.five_minutes),
        chart=Chart("XAUUSD!", TimeFrame.one_minute),
        agent=ForexAgent(),
        double_diver=False,
        strategy=OscillatorDivergence(
            RSI(),
            3,
            100,
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
            choch_mode=1,
            retrace_fib=0.5,
            use_fibo_filter=True,
            name="Choch",
        ),
        bar_between_signals=2,
        same_line_source=True,
        n_candle_confirmation=60,
        n_candle_check=200,
        consider_position=True,
        position_handler=(
            SteppingHandlerForex(
                ForexAgent(),
                targets_ratio=[1],
                targets_ratio_volumes=[0.01],
                stoploss_pip=5,
                targets_in_pip=[],
                targets_in_pip_volumes=[],
                long_trade=True,
                short_trade=True,
                trail_stop=True,
            )
        ),
        heikingashi_chartdata=False,
    )

xau_15m = RsiDiverChochConfig(
        rsi_chart=Chart("XAUUSD!", TimeFrame.fifteen_minutes),
        chart=Chart("XAUUSD!", TimeFrame.one_minute),
        agent=ForexAgent(),
        double_diver=False,
        strategy=OscillatorDivergence(
            RSI(),
            3,
            100,
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
            choch_mode=1,
            retrace_fib=0.5,
            use_fibo_filter=True,
            name="Choch",
        ),
        bar_between_signals=2,
        same_line_source=True,
        n_candle_confirmation=60,
        n_candle_check=200,
        consider_position=True,
        position_handler=(
            SteppingHandlerForex(
                ForexAgent(),
                targets_ratio=[2],
                targets_ratio_volumes=[0.01],
                stoploss_pip=5,
                targets_in_pip=[],
                targets_in_pip_volumes=[],
                long_trade=True,
                short_trade=True,
                trail_stop=True,
            )
        ),
        heikingashi_chartdata=False,
    )

TraderBot("Gold Diver Bot", [xau_5m,xau_15m], report_time={"h": 20, "m": 0})


if __name__ == "__main__":
    # from TradingModule.reporter import TelegramReporter
    # TelegramReporter().disable_reporting()

    asyncio.run(TraderBot().start())
