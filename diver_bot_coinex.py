from Coinex import CoinexAgent, CoinexDiverTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule.trader_bot import TraderBot
from TradingModule.PositionHandlers import RiskFreeCrypto, SimpleCrypto
from DivergenceStrategy.divergence import Divergence
from custom_logger import CustomLogger
from config import settings
import asyncio

CustomLogger(log_file=True, file_log_name="CoinexDiverBot")

coinex_agent = CoinexAgent(settings.COINEX_ACCESS_ID, settings.COINEX_SECRET_KEY)

five_m_diver = CoinexDiverTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.five_minutes),
    second_chart=Chart("BTCUSDT", TimeFrame.five_minutes),
    strategy=Divergence(3, 100, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=SimpleCrypto(
        coinex_agent,
        stoploss_percent=1,
        takeprofit_percent=1,
        leverage=5,
        initial_volume=1,
        long_trade=False,
        short_trade=False,
    ),
    agent=coinex_agent,
    heikingashi_chartdata=True,
)

one_h_diver = CoinexDiverTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.one_hour),
    second_chart=Chart("BTCUSDT", TimeFrame.one_hour),
    strategy=Divergence(2, 300, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=RiskFreeCrypto(
        coinex_agent,
        takeprofit_percent=2,
        stoploss_percent=2,
        initial_volume=2,
        riskfree_trigger_percent=1,
        leverage=10,
        long_trade=False,
        short_trade=False,
    ),
    agent=coinex_agent,
    heikingashi_chartdata=True,
)

TraderBot("CoinexDiverBot", [five_m_diver, one_h_diver])


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
