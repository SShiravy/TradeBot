from Forex.agent import ForexAgent
from ChartModule import Chart, TimeFrame
from TradingModule import TraderBotConfig, TraderBot
from TradingModule.position_handlers import SimpleForexHandler
from TradingModule.Strategies import Divergence
from custom_logger import CustomLogger
import asyncio

CustomLogger(log_file=True, file_log_name="ForexBot")
one_m_diver = TraderBotConfig(
    Chart("XAUUSD!", TimeFrame.one_minute),
    ForexAgent(),
    Divergence(3, 3, [], name="ForexDivergence", inverse_diver_long=True),
    SimpleForexHandler(ForexAgent()),
)


TraderBot("ForexTraderBot", [one_m_diver])


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
