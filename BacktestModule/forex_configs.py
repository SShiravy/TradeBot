from ChartModule import Chart, TimeFrame
from TradingModule.Strategies.divergence import Divergence
from Forex import ForexAgent, CvdDiverTradeConfig, ForexDiverTradeConfig
from TradingModule.position_handlers import SimpleForexHandler, RiskFreeForex

from ChartModule.Indicators import EMA

forex_one_m_diver = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    second_chart=Chart("SOLUSD", TimeFrame.one_minute),
    strategy=Divergence(3, 100, [], name="ForexDiver"),
    position_handler=SimpleForexHandler(
        ForexAgent(), takeprofit_pip=10, stoploss_pip=10
    ),
    merge_two_chart_time=True,
)


forex_five_m_diver = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    second_chart=Chart("SOLUSD", TimeFrame.five_minutes),
    strategy=Divergence(3, 100, name="ForexDiver", confirmation_indicators=[EMA(20)]),
    position_handler=(RiskFreeForex(ForexAgent())),
    merge_two_chart_time=True,
)

forex_fifteen_m_diver = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.fifteen_minutes),
    second_chart=Chart("SOLUSD", TimeFrame.fifteen_minutes),
    strategy=Divergence(3, 100, [], name="ForexDiver"),
    position_handler=SimpleForexHandler(
        ForexAgent(),
        stoploss_pip=40,
        takeprofit_pip=40,
    ),
    merge_two_chart_time=True,
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
    position_handler=SimpleForexHandler(
        ForexAgent(), stoploss_pip=10, takeprofit_pip=10
    ),
)

forex_five_m_cvd = CvdDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    strategy=cvd_diver,
    position_handler=SimpleForexHandler(ForexAgent()),
)
