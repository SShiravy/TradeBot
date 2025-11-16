from Coinex import CoinexAgent, CoinexDiverTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule.position_handlers import RiskFreeCrypto
from TradingModule.Strategies.divergence import Divergence
from config import settings


coinex_agent = CoinexAgent(settings.COINEX_ACCESS_ID, settings.COINEX_SECRET_KEY)

coinex_five_m_diver = CoinexDiverTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.five_minutes),
    second_chart=Chart("BTCUSDT", TimeFrame.five_minutes),
    strategy=Divergence(3, 100, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=RiskFreeCrypto(
        coinex_agent,
        riskfree_trigger_percent=0.25,
        stoploss_percent=0.5,
        takeprofit_percent=0.5,
        leverage=5,
        initial_volume=10,
    ),
    agent=coinex_agent,
    long_trade=False,
    short_trade=False,
    heikingashi_chartdata=True,
)

coinex_one_h_diver = CoinexDiverTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.one_hour),
    second_chart=Chart("BTCUSDT", TimeFrame.one_hour),
    strategy=Divergence(2, 300, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=RiskFreeCrypto(
        coinex_agent,
        takeprofit_percent=2,
        stoploss_percent=2,
        initial_volume=20,
        riskfree_trigger_percent=1,
        leverage=10,
    ),
    agent=coinex_agent,
    long_trade=False,
    short_trade=False,
    heikingashi_chartdata=True,
)
