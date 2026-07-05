from ChartModule.Indicators.models import SupportCandleConditions
from ChartModule.Indicators.rsi import RSI
from DivergenceStrategy.oscillator_divergence import OscillatorDivergence
from DivergenceStrategy.oscillator_double_divergence import OscillatorDoubleDiverConfig
from Forex import ForexAgent, ForexDiverTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule.PositionHandlers.stepping_handler import SteppingHandlerForex
from TradingModule.PositionHandlers.trading_constraints import (
    LoseInRowConstraint,
    SideConstraint,
)
from TradingModule.trader_bot import TraderBot
from DivergenceStrategy import Divergence
from custom_logger import CustomLogger
import asyncio
import logging


CustomLogger(
    log_file=True, file_log_name="ForexDiverBot(RSI)", consol_log_level=logging.DEBUG
)

forex_rsi_double_diver_five_m = OscillatorDoubleDiverConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    agent=ForexAgent(),
    strategy=OscillatorDivergence(
        RSI(),
        3,
        200,
        [],
        name="RSI_Double_Diver",
        long_support_conditions=SupportCandleConditions.RED_GREEN,
        short_support_conditions=SupportCandleConditions.GREEN_RED,
        body_candle=False,
        inverse_diver_long=False,
    ),
    bar_between_signals=2,
    position_handler=(
        SteppingHandlerForex(
            ForexAgent(),
            targets_ratio=[1, 2, 3],
            targets_ratio_volumes=[0.01, 0.01, 0.01],
            stoploss_pip=30,
            targets_in_pip=[],
            targets_in_pip_volumes=[],
            long_trade=False,
            short_trade=False,
            trail_stop=True,
        )
    ),
    heikingashi_chartdata=False,
)


TraderBot("3 Push RSI", [forex_rsi_double_diver_five_m], report_time={"h": 20, "m": 10})


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
