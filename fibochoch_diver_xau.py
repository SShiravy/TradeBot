from ChartModule.Indicators.fibonacci import FiboLevels
from FiboChochDiverStrategy import FiboChochDiver
from FiboChochStrategy import FiboChoch
from TradingModule.position_handlers import SimpleForexHandler
from DivergenceStrategy.divergence import Divergence
from Forex import ForexAgent
from ChartModule import Chart, TimeFrame
from TradingModule import TraderBot
from custom_logger import CustomLogger
import logging
import asyncio


CustomLogger(
    log_file=True,
    file_log_name="ForexFiboChochDiverBot",
    consol_log_level=logging.DEBUG,
)


one_five_m = FiboChochDiver(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    agent=ForexAgent(),
    position_handler=SimpleForexHandler(ForexAgent()),
    diver_base_chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    diver_second_chart=Chart("SOLUSD", TimeFrame.five_minutes),
    diver_strategy=Divergence(3, 10, []),
    strategy=FiboChoch(pivot_left=10, pivot_right=5, fibo_level=FiboLevels.LEVEL_5),
)

TraderBot(
    "Gold FiboChochDiver Bot",
    [one_five_m],
)


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
