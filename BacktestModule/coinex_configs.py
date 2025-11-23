from Coinex import CoinexAgent, CoinexDiverTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule.position_handlers import RiskFreeCrypto
from TradingModule.Strategies.divergence import Divergence
from ChartModule.Indicators import EMA
from config import settings


coinex_agent = CoinexAgent(settings.COINEX_ACCESS_ID, settings.COINEX_SECRET_KEY)

coinex_five_m_diver = CoinexDiverTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.five_minutes),
    second_chart=Chart("BTCUSDT", TimeFrame.five_minutes),
    strategy=Divergence(3, 100, [EMA(10)], name="CoinexDiver", inverse_diver_long=True),
    position_handler=RiskFreeCrypto(
        coinex_agent,
        riskfree_trigger_percent=0.5,
        stoploss_percent=1,
        takeprofit_percent=1,
        leverage=10,
        initial_volume=10,
    ),
    agent=coinex_agent,
    heikingashi_chartdata=True,
)

coinex_one_h_diver = CoinexDiverTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.one_hour),
    second_chart=Chart("BTCUSDT", TimeFrame.one_hour),
    strategy=Divergence(2, 300, [EMA(10)], name="CoinexDiver", inverse_diver_long=True),
    position_handler=RiskFreeCrypto(
        coinex_agent,
        takeprofit_percent=2,
        stoploss_percent=2,
        initial_volume=20,
        riskfree_trigger_percent=1,
        leverage=20,
    ),
    agent=coinex_agent,
    heikingashi_chartdata=True,
)


coinex_4h_diver = CoinexDiverTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.four_hours),
    second_chart=Chart("BTCUSDT", TimeFrame.four_hours),
    strategy=Divergence(3, 100, [EMA(10)], name="CoinexDiver", inverse_diver_long=True),
    position_handler=RiskFreeCrypto(
        coinex_agent,
        riskfree_trigger_percent=3,
        stoploss_percent=7,
        takeprofit_percent=7,
        leverage=30,
        initial_volume=50,
    ),
    agent=coinex_agent,
    heikingashi_chartdata=True,
)
