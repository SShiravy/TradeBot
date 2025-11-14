from Coinex import CoinexAgent, CoinexDiverTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule.position_handlers import SimpleCryptoHandler
from TradingModule.Strategies.divergence import Divergence
from Forex import ForexAgent, CvdDiverTradeConfig, ForexDiverTradeConfig
from TradingModule.position_handlers import SimpleForexHandler
from config import settings


coinex_agent = CoinexAgent(settings.COINEX_ACCESS_ID, settings.COINEX_SECRET_KEY)

coinex_five_m_diver = CoinexDiverTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.five_minutes),
    second_chart=Chart("BTCUSDT", TimeFrame.five_minutes),
    strategy=Divergence(3, 100, [], name="CoinexDiver"),
    position_handler=SimpleCryptoHandler(coinex_agent),
    agent=coinex_agent,
    long_trade=False,
    short_trade=False,
    heikingashi_chartdata=True,
)

coinex_one_h_diver = CoinexDiverTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.one_hour),
    second_chart=Chart("BTCUSDT", TimeFrame.one_hour),
    strategy=Divergence(2, 100, [], name="CoinexDiver"),
    position_handler=SimpleCryptoHandler(coinex_agent),
    agent=coinex_agent,
    long_trade=False,
    short_trade=False,
    heikingashi_chartdata=True,
)

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

forex_one_m_diver = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    second_chart=Chart("SOLUSD", TimeFrame.one_minute),
    strategy=Divergence(3, 100, [], name="ForexDiver"),
    position_handler=SimpleForexHandler(ForexAgent()),
)


forex_five_m_diver = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    second_chart=Chart("SOLUSD", TimeFrame.five_minutes),
    strategy=Divergence(3, 100, [], name="ForexDiver"),
    position_handler=SimpleForexHandler(ForexAgent()),
)

forex_fifteen_m_diver = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.fifteen_minutes),
    second_chart=Chart("SOLUSD", TimeFrame.fifteen_minutes),
    strategy=Divergence(3, 100, [], name="ForexDiver"),
    position_handler=SimpleForexHandler(ForexAgent()),
)

cvd_diver = Divergence(
    3,
    100,
    [],
    name="ForexCVD",
    long_second_line_validation=False,
    short_second_line_validation=False,
)

forex_one_m_cvd = CvdDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    strategy=cvd_diver,
    position_handler=SimpleForexHandler(ForexAgent()),
)

forex_five_m_cvd = CvdDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    strategy=cvd_diver,
    position_handler=SimpleForexHandler(ForexAgent()),
)
