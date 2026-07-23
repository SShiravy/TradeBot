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
    log_file=True, file_log_name="ForexDiverBot", consol_log_level=logging.DEBUG
)

one_m = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute, precision=2, pip_factor=0.1),
    second_chart=Chart("SOLUSD", TimeFrame.one_minute),
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
        check_with_agent=True
    ),
    merge_two_chart_time=False,
    heikingashi_chartdata=True,
)

dxy_1m = ForexDiverTradeConfig(
    chart=Chart("XAUUSD", TimeFrame.one_minute),
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
    heikingashi_chartdata=False,
)


TraderBot("Gold Diver Bot", [one_m, dxy_1m], report_time={"h": 20, "m": 0})


if __name__ == "__main__":
    # from TradingModule.reporter import TelegramReporter
    # TelegramReporter().disable_reporting()

    asyncio.run(TraderBot().start())
