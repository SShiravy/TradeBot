from ChartModule.Indicators.fibonacci import FiboLevels
from FiboChochDiverStrategy import FiboChochDiver
from FiboChochStrategy import FiboChoch
from TradingModule.position_handlers import SimpleForexHandler
from DivergenceStrategy.divergence import Divergence
from ChartModule import Chart, TimeFrame
from TradingModule.trader_bot import TraderBot
from Forex import ForexAgent, ForexDiverTradeConfig
from custom_logger import CustomLogger
import logging
import asyncio


CustomLogger(
    log_file=True,
    file_log_name="ForexFiboChochDiverBot",
    consol_log_level=logging.DEBUG,
)


forex_diver_five_m = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    second_chart=Chart("SOLUSD", TimeFrame.five_minutes),
    strategy=Divergence(15, 50, [], name="ForexDiver"),
    bar_between_signals=5,
    position_handler=(SimpleForexHandler(ForexAgent())),
    merge_two_chart_time=False,
)


one_m = FiboChochDiver(
    divergence_config=forex_diver_five_m,
    chart=Chart("SOLUSD", TimeFrame.one_minute),
    agent=ForexAgent(),
    strategy=FiboChoch(
        "CoinexFiboChochTest",
        pivot_right=5,
        pivot_left=10,
        fibo_level=FiboLevels.LEVEL_5,
    ),
    position_handler=SimpleForexHandler(
        ForexAgent(),
        stoploss_pip=2,
        takeprofit_pip=1,
        initial_volume=0.01,
    ),
    bar_between_signals=0,
    send_signal=False,
)

TraderBot(
    "Gold FiboChochDiver Bot",
    [one_m],
)


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
