from Coinex import CoinexAgent, CoinexDiverTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule import TraderBot
from TradingModule.position_handlers import SimpleForexHandler
from TradingModule.Strategies import Divergence
from custom_logger import CustomLogger
from config import settings
import asyncio

CustomLogger(log_file=True, file_log_name="CoinexBot")

coinex_agent = CoinexAgent(settings.COINEX_ACCESS_ID, settings.COINEX_SECRET_KEY)

five_m_diver = CoinexDiverTradeConfig(
    chart=Chart("BTCUSDT", TimeFrame.five_minutes),
    second_chart=Chart("SOLUSDT", TimeFrame.five_minutes),
    strategy=Divergence(3, 100, [], name="CoinexDiver"),
    position_handler=SimpleForexHandler(coinex_agent),
    agent=coinex_agent,
)

one_h_diver = CoinexDiverTradeConfig(
    chart=Chart("BTCUSDT", TimeFrame.one_hour),
    second_chart=Chart("SOLUSDT", TimeFrame.one_hour),
    strategy=Divergence(2, 100, [], name="CoinexDiver"),
    position_handler=SimpleForexHandler(coinex_agent),
    agent=coinex_agent,
)


TraderBot("CoinexBot", [five_m_diver, one_h_diver])


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
