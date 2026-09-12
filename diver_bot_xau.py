from ExchangeAgents.MT5 import MT5Agent, ForexDiverTradeConfig
from ChartModule import Chart, TimeFrame
from TraderBot.PositionHandlers.stepping_handler import SteppingHandlerForex
from TraderBot.PositionHandlers.trading_constraints import (
    LoseInRowConstraint,
    SideConstraint,
)
from TraderBot.trader_bot import TraderBot
from Bots.DivergenceStrategy import Divergence
from custom_logger import LoggerConfig, build_logger
import asyncio

build_logger(LoggerConfig(name="root", log_file_name="ForexDiverBot"))


one_m = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    second_chart=Chart("USDJPY!", TimeFrame.one_minute),
    strategy=Divergence(5, 100, [], name="ForexDiver", inverse_diver_long=True),
    bar_between_signals=2,
    position_generator=SteppingHandlerForex(
        MT5Agent(),
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

dxy_1m = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    consider_position=False,
    second_chart=Chart("DXY!", TimeFrame.one_minute),
    strategy=Divergence(5, 100, [], name="DXY_divergence"),
    bar_between_signals=2,
    position_generator=SteppingHandlerForex(
        MT5Agent(),
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


TraderBot("Gold Diver Bot", [one_m, dxy_1m], report_time={"h": 20, "m": 0})


if __name__ == "__main__":
    # from TradingModule.reporter import TelegramReporter
    # TelegramReporter().disable_reporting()

    asyncio.run(TraderBot().start())
