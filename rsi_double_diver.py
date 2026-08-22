from config import settings

settings.TELEGRAM_BOT_TOKEN = "8470075659:AAHxX4BDBiUeKB85REsL8RB7jpe8XeubDbc"
from TradingModule.reporter import TelegramReporter
from ChartModule.Indicators.models import SupportCandleConditions
from ChartModule.Indicators.rsi import RSI
from DivergenceStrategy.oscillator_divergence import OscillatorDivergence
from DivergenceStrategy.oscillator_double_divergence import OscillatorDoubleDiverConfig
from Forex import ForexAgent
from ChartModule import Chart, TimeFrame
from TradingModule.PositionHandlers.stepping_handler import SteppingHandlerForex
from TradingModule.trader_bot import TraderBot
from custom_logger import CustomLogger
import asyncio
import logging


CustomLogger(
    log_file=True,
    file_log_name="ForexDoubleDiverBot(RSI)",
    consol_log_level=logging.DEBUG,
)

xau_double_diver_five_m = OscillatorDoubleDiverConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    consider_position=False,
    agent=ForexAgent(),
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
    position_handler=(
        SteppingHandlerForex(
            ForexAgent(),
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
    heikingashi_chartdata=False,
)

audcad_double_diver_five_m = OscillatorDoubleDiverConfig(
    chart=Chart("AUDCAD!", TimeFrame.five_minutes),
    consider_position=False,
    agent=ForexAgent(),
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
    position_handler=(
        SteppingHandlerForex(
            ForexAgent(),
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
    heikingashi_chartdata=False,
)

usdjpy_double_diver_five_m = OscillatorDoubleDiverConfig(
    chart=Chart("USDJPY!", TimeFrame.five_minutes),
    consider_position=False,
    agent=ForexAgent(),
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
    position_handler=(
        SteppingHandlerForex(
            ForexAgent(),
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
    heikingashi_chartdata=False,
)
eurgbp_double_diver_five_m = OscillatorDoubleDiverConfig(
    chart=Chart("EURGBP!", TimeFrame.five_minutes),
    consider_position=False,
    agent=ForexAgent(),
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
    position_handler=(
        SteppingHandlerForex(
            ForexAgent(),
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
    heikingashi_chartdata=False,
)
TelegramReporter().main_channel = "@three_push"
TraderBot(
    "3 diver RSI",
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
