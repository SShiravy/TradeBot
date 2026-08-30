from config import settings

settings.TELEGRAM_BOT_TOKEN = "8937168160:AAHtl4qXCSKXgT6YTSZEvYYDSHs3UcVqD5Y"
from DivergenceStrategy.two_chart_divergence import Divergence
from Forex.bot_config import ForexDiverTradeConfig
from TradingModule.reporter import TelegramReporter
from ChartModule.Indicators.models import SupportCandleConditions
from ChartModule.Indicators.rsi import RSI
from DivergenceStrategy.oscillator_divergence import (
    OscillatorDiverConfig,
    OscillatorDivergence,
)
from DivergenceStrategy.oscillator_double_divergence import OscillatorDoubleDiverConfig
from Forex import ForexAgent
from ChartModule import Chart, TimeFrame
from TradingModule.PositionHandlers.stepping_handler import SteppingHandlerForex
from TradingModule.trader_bot import TraderBot
from custom_logger import LoggerConfig, build_logger
import asyncio


build_logger(LoggerConfig(name="root", log_file_name="Develop & Test"))


xau_jpy_1m = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    second_chart=Chart("USDJPY!", TimeFrame.one_minute),
    strategy=Divergence(5, 100, [], name="ForexDiver", inverse_diver_long=True),
    bar_between_signals=2,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=30,
        targets_ratio=[1, 2, 3],
        targets_ratio_volumes=[0.01, 0.01, 0.01],
        targets_in_pip=[20],
        targets_in_pip_volumes=[0.01],
        trail_stop=True,
        pip_trail_stop_under_entry=False,
        trading_constraints=[
            # SideConstraint(n_pos_each_side=1, n_bar=30, check_closed_positions=False),
            # LoseInRowConstraint(n_long_lose=1, n_short_lose=1, n_bar=30),
        ],
        check_with_agent=False,
    ),
    merge_two_chart_time=False,
)

xau_dxy_1m = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    consider_position=False,
    second_chart=Chart("DXY!", TimeFrame.one_minute),
    strategy=Divergence(5, 100, [], name="DXY_divergence"),
    bar_between_signals=2,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=5,
        targets_ratio=[],
        targets_ratio_volumes=[],
        targets_in_pip=[20],
        targets_in_pip_volumes=[0.01],
        trail_stop=False,
        pip_trail_stop_under_entry=False,
        long_trade=False,
        short_trade=False,
    ),
    merge_two_chart_time=False,
)

xau_double_diver_rsi_1m = OscillatorDoubleDiverConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
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
)

audcad_double_diver_rsi_1m = OscillatorDoubleDiverConfig(
    chart=Chart("AUDCAD!", TimeFrame.one_minute),
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
)

usdjpy_double_diver_rsi_1m = OscillatorDoubleDiverConfig(
    chart=Chart("USDJPY!", TimeFrame.one_minute),
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
)
eurgbp_double_diver_rsi_1m = OscillatorDoubleDiverConfig(
    chart=Chart("EURGBP!", TimeFrame.one_minute),
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
)

xau_rsi_1m = OscillatorDiverConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    consider_position=False,
    agent=ForexAgent(),
    strategy=OscillatorDivergence(
        RSI(),
        3,
        200,
        [],
        name="RSI_Divergence",
        long_support_conditions=SupportCandleConditions.RED_GREEN,
        short_support_conditions=SupportCandleConditions.GREEN_RED,
        body_candle=True,
        ignore_shadow_cross=True,
        inverse_diver_long=False,
    ),
    bar_between_signals=2,
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
)
TelegramReporter().main_channel = "@result_forex_crypto"
TraderBot(
    "Develop & Test",
    [
        xau_double_diver_rsi_1m,
        audcad_double_diver_rsi_1m,
        usdjpy_double_diver_rsi_1m,
        eurgbp_double_diver_rsi_1m,
        xau_jpy_1m,
        xau_dxy_1m,
        xau_rsi_1m,
    ],
    report_time={"h": 20, "m": 10},
)


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
