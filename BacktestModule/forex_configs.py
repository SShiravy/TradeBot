from ChartModule import Chart, TimeFrame
from ChartModule.Indicators import EMA
from TradingModule.Strategies.divergence import Divergence
from Forex import ForexAgent, CvdDiverTradeConfig, ForexDiverTradeConfig
from TradingModule.position_handlers import (
    RiskFreeForex,
    LongShortForexHandler,
)

forex_one_m_diver = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_day),
    second_chart=Chart("SOLUSD", TimeFrame.one_day),
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
    heikingashi_chartdata=True,
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
