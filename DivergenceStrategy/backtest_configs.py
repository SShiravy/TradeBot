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

# FOREX ----------------------------------------------------------------

forex_one_m_diver = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    second_chart=Chart("SOLUSD", TimeFrame.one_minute),
    strategy=Divergence(3, 100, [], name="ForexDiver"),
    position_handler=LongShortForexHandler(
        ForexAgent(),
        long_takeprofit_pip=3,
        long_stoploss_pip=3,
        long_riskfree_trigger_pip=1,
        short_takeprofit_pip=3,
        short_stoploss_pip=3,
        short_riskfree_trigger_pip=1,
    ),
    merge_two_chart_time=True,
    heikingashi_chartdata=False,
)


forex_five_m_diver = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    second_chart=Chart("SOLUSD", TimeFrame.five_minutes),
    strategy=Divergence(3, 100, [EMA(100)], name="ForexDiver"),
    position_handler=(
        RiskFreeForex(
            ForexAgent(), stoploss_pip=10, takeprofit_pip=10, riskfree_trigger_pip=5
        )
    ),
    merge_two_chart_time=True,
)

forex_fifteen_m_diver = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.fifteen_minutes),
    second_chart=Chart("SOLUSD", TimeFrame.fifteen_minutes),
    strategy=Divergence(5, 100, [EMA(200)], name="ForexDiver"),
    position_handler=RiskFreeForex(
        ForexAgent(), stoploss_pip=10, takeprofit_pip=10, riskfree_trigger_pip=5
    ),
    merge_two_chart_time=True,
)

cvd_diver = Divergence(
    5,
    100,
    [EMA(100)],
    name="ForexCVD",
    long_second_line_validation=False,
    short_second_line_validation=False,
)

forex_one_m_cvd = CvdDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    strategy=cvd_diver,
    position_handler=RiskFreeForex(
        ForexAgent(), stoploss_pip=5, takeprofit_pip=5, riskfree_trigger_pip=2
    ),
)

forex_five_m_cvd = CvdDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    strategy=cvd_diver,
    position_handler=RiskFreeForex(
        ForexAgent(), stoploss_pip=10, takeprofit_pip=10, riskfree_trigger_pip=5
    ),
)
