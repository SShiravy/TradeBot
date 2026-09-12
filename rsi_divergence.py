from config import settings

settings.TELEGRAM_BOT_TOKEN = "8470075659:AAHxX4BDBiUeKB85REsL8RB7jpe8XeubDbc"
from TraderBot.reporter import TelegramReporter
from ChartModule.Indicators.models import SupportCandleConditions
from ChartModule.Indicators.rsi import RSI
from Bots.DivergenceStrategy.oscillator_divergence import OscillatorDivergence
from Bots.DivergenceStrategy.oscillator_double_divergence import (
    OscillatorDoubleDiverConfig,
)
from ExchangeAgents.MT5 import MT5Agent
from ChartModule import Chart, TimeFrame
from TraderBot.PositionHandlers.stepping_handler import SteppingHandlerForex
from TraderBot.trader_bot import TraderBot
from custom_logger import build_logger, LoggerConfig
import asyncio

build_logger(LoggerConfig(name="root", log_file_name="ForexDiverBot(RSI)"))


xau_double_diver_five_m = OscillatorDoubleDiverConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    consider_position=False,
    agent=MT5Agent(),
    strategy=OscillatorDivergence(
        RSI(),
        3,
        200,
        [],
        name="RSI_Double_Diver",
        long_support_conditions=SupportCandleConditions.RED_GREEN,
        short_support_conditions=SupportCandleConditions.GREEN_RED,
        body_candle=True,
        ignore_shadow_cross=True,
        inverse_diver_long=False,
    ),
    bar_between_signals=2,
    same_line_source=True,
    position_generator=(
        SteppingHandlerForex(
            MT5Agent(),
            targets_ratio=[],
            targets_ratio_volumes=[],
            stoploss_pip=30,
            targets_in_pip=[20],
            targets_in_pip_volumes=[0.01],
            long_trade=False,
            short_trade=False,
            trail_stop=True,
        )
    ),
)

audcad_double_diver_five_m = OscillatorDoubleDiverConfig(
    chart=Chart("AUDCAD!", TimeFrame.five_minutes),
    consider_position=False,
    agent=MT5Agent(),
    strategy=OscillatorDivergence(
        RSI(),
        3,
        200,
        [],
        name="RSI_Double_Diver",
        long_support_conditions=SupportCandleConditions.RED_GREEN,
        short_support_conditions=SupportCandleConditions.GREEN_RED,
        body_candle=True,
        ignore_shadow_cross=True,
        inverse_diver_long=False,
    ),
    bar_between_signals=2,
    same_line_source=True,
    position_generator=(
        SteppingHandlerForex(
            MT5Agent(),
            targets_ratio=[],
            targets_ratio_volumes=[],
            stoploss_pip=10,
            targets_in_pip=[10],
            targets_in_pip_volumes=[0.01],
            long_trade=False,
            short_trade=False,
            trail_stop=True,
        )
    ),
)

usdjpy_double_diver_five_m = OscillatorDoubleDiverConfig(
    chart=Chart("USDJPY!", TimeFrame.five_minutes),
    consider_position=False,
    agent=MT5Agent(),
    strategy=OscillatorDivergence(
        RSI(),
        3,
        200,
        [],
        name="RSI_Double_Diver",
        long_support_conditions=SupportCandleConditions.RED_GREEN,
        short_support_conditions=SupportCandleConditions.GREEN_RED,
        body_candle=True,
        ignore_shadow_cross=True,
        inverse_diver_long=False,
    ),
    bar_between_signals=2,
    same_line_source=True,
    position_generator=(
        SteppingHandlerForex(
            MT5Agent(),
            targets_ratio=[],
            targets_ratio_volumes=[],
            stoploss_pip=9,
            targets_in_pip=[9],
            targets_in_pip_volumes=[0.01],
            long_trade=False,
            short_trade=False,
            trail_stop=True,
        )
    ),
)
eurgbp_double_diver_five_m = OscillatorDoubleDiverConfig(
    chart=Chart("EURGBP!", TimeFrame.five_minutes),
    consider_position=False,
    agent=MT5Agent(),
    strategy=OscillatorDivergence(
        RSI(),
        3,
        200,
        [],
        name="RSI_Double_Diver",
        long_support_conditions=SupportCandleConditions.RED_GREEN,
        short_support_conditions=SupportCandleConditions.GREEN_RED,
        body_candle=True,
        ignore_shadow_cross=True,
        inverse_diver_long=False,
    ),
    bar_between_signals=2,
    same_line_source=True,
    position_generator=(
        SteppingHandlerForex(
            MT5Agent(),
            targets_ratio=[],
            targets_ratio_volumes=[],
            stoploss_pip=5,
            targets_in_pip=[5],
            targets_in_pip_volumes=[0.01],
            long_trade=False,
            short_trade=False,
            trail_stop=True,
        )
    ),
)
TelegramReporter().signal_channel = "@three_push"
TraderBot(
    "3 Push RSI",
    [
        xau_double_diver_five_m,
        audcad_double_diver_five_m,
        usdjpy_double_diver_five_m,
        eurgbp_double_diver_five_m,
    ],
    report_time={"h": 20, "m": 10},
)


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
