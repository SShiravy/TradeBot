from Forex import ForexAgent, ForexDiverTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule.PositionHandlers.ratio_stepping import RatioSteppingForex
from TradingModule.PositionHandlers.trading_constraints import SideConstraint
from TradingModule.trader_bot import TraderBot
from DivergenceStrategy.divergence import Divergence
from custom_logger import CustomLogger
import asyncio
import logging

CustomLogger(
    log_file=True, file_log_name="ForexDiverBot", consol_log_level=logging.DEBUG
)

one_m = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    second_chart=Chart("SOLUSD", TimeFrame.one_minute),
    strategy=Divergence(2, 300, [], name="ForexDiver"),
    bar_between_signals=2,
    position_handler=RatioSteppingForex(
        ForexAgent(),
        stoploss_pip=30,
        targets_ratio=[1, 2, 3],
        initial_volume=[0.01, 0.01, 0.01],
        trail_stop=True,
        trading_constraints=[SideConstraint(n_pos_each_side=1, n_bar=30)],
    ),
    merge_two_chart_time=False,
    heikingashi_chartdata=True,
)


five_m = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    second_chart=Chart("SOLUSD", TimeFrame.five_minutes),
    strategy=Divergence(2, 100, [], name="ForexDiver"),
    bar_between_signals=2,
    position_handler=RatioSteppingForex(
        ForexAgent(),
        stoploss_pip=50,
        targets_ratio=[1, 2, 3],
        initial_volume=[0.01, 0.01, 0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    merge_two_chart_time=True,
    heikingashi_chartdata=True,
)


TraderBot("Gold Diver Bot", [one_m], report_time={"h": 20, "m": 0})


if __name__ == "__main__":
    # from TradingModule.reporter import TelegramReporter
    # TelegramReporter().disable_reporting()

    asyncio.run(TraderBot().start())
