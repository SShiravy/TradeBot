from Coinex import CoinexAgent, CoinexDiverTradeConfig
from ChartModule import Chart, TimeFrame
from DivergenceStrategy.divergence import Divergence
from ChartModule.Indicators import EMA
from Forex import ForexAgent, CvdDiverTradeConfig, ForexDiverTradeConfig
from TradingModule.position_handlers import (
    RiskFreeForex,
    LongShortForexHandler,
    RiskFreeCrypto,
)
from config import settings
# Coinex ----------------------------------------------------------------


coinex_agent = CoinexAgent(settings.COINEX_ACCESS_ID, settings.COINEX_SECRET_KEY)

five_m_diver = CoinexDiverTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.five_minutes),
    second_chart=Chart("BTCUSDT", TimeFrame.five_minutes),
    strategy=Divergence(3, 100, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=RiskFreeCrypto(
        coinex_agent,
        riskfree_trigger_percent=0.5,
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

# FOREX ----------------------------------------------------------------


forex_diver_one_m = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    second_chart=Chart("SOLUSD", TimeFrame.one_minute),
    strategy=Divergence(7, 50, [], name="ForexDiver"),
    bar_between_signals=5,
    position_handler=RiskFreeForex(
        ForexAgent(), takeprofit_pip=30, stoploss_pip=30, riskfree_trigger_pip=15
    ),
)


forex_diver_five_m = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    second_chart=Chart("SOLUSD", TimeFrame.five_minutes),
    strategy=Divergence(5, 50, [], name="ForexDiver"),
    bar_between_signals=5,
    position_handler=(
        RiskFreeForex(
            ForexAgent(), stoploss_pip=70, takeprofit_pip=70, riskfree_trigger_pip=35
        )
    ),
)

# CVD ----

diver_one_cvd = Divergence(
    7,
    50,
    [],
    name="ForexCVD",
    long_second_line_validation=False,
    short_second_line_validation=False,
)

cvd_diver_one_m_cvd = CvdDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    bar_between_signals=5,
    strategy=diver_one_cvd,
    position_handler=RiskFreeForex(
        ForexAgent(), stoploss_pip=30, takeprofit_pip=30, riskfree_trigger_pip=15
    ),
)

diver_five_cvd = Divergence(
    5,
    50,
    [],
    name="ForexCVD",
    long_second_line_validation=False,
    short_second_line_validation=False,
)
cvd_diver_five_m_cvd = CvdDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    bar_between_signals=5,
    strategy=diver_five_cvd,
    position_handler=RiskFreeForex(
        ForexAgent(), stoploss_pip=70, takeprofit_pip=70, riskfree_trigger_pip=35
    ),
)
