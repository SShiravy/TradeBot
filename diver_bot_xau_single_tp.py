from config import settings

settings.METATRADER_TERMINAL_PATH = settings.SECOND_METATRADER_TERMINAL_PATH
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
    log_file=True,
    file_log_name="ForexDiverBot(Single TP)",
    consol_log_level=logging.DEBUG,
)
one_m = ForexDiverTradeConfig(
    chart=Chart("XAUUSD", TimeFrame.one_minute),
    second_chart=Chart("USDJPY", TimeFrame.one_minute),
    strategy=Divergence(
        5, 100, [], name="ForexDiver(Single TP)", inverse_diver_long=True
    ),
    bar_between_signals=2,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=5,
        targets_ratio=[],
        targets_ratio_volumes=[],
        targets_in_pip=[20],
        targets_in_pip_volumes=[0.01],
        trail_stop=True,
        pip_trail_stop_under_entry=False,
        trading_constraints=[
            # SideConstraint(n_pos_each_side=1, n_bar=30, check_closed_positions=False),
            # LoseInRowConstraint(n_long_lose=1, n_short_lose=1, n_bar=30),
        ],
        send_report=False,
        long_trade=True,
        short_trade=True,
    ),
    merge_two_chart_time=False,
    heikingashi_chartdata=True,
)


TraderBot(
    "Gold Diver Bot (Single TP)",
    [one_m],
    report_time={"h": 20, "m": 5},
    commands_report=False,
)


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
