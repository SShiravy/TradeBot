from Forex import ForexAgent, CvdDiverTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule.PositionHandlers import RiskFreeForex
from DivergenceStrategy.divergence import Divergence
from TradingModule.trader_bot import TraderBot
from custom_logger import CustomLogger
import asyncio

CustomLogger(log_file=True, file_log_name="ForexCVDBot")


cvd_diver_one = Divergence(
    7,
    50,
    [],
    name="ForexCVD",
    long_second_line_validation=False,
    short_second_line_validation=False,
)

one_m_cvd = CvdDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    bar_between_signals=5,
    strategy=cvd_diver_one,
    position_handler=RiskFreeForex(
        ForexAgent(), stoploss_pip=30, takeprofit_pip=30, riskfree_trigger_pip=15
    ),
)

cvd_diver_five = Divergence(
    5,
    50,
    [],
    name="ForexCVD",
    long_second_line_validation=False,
    short_second_line_validation=False,
)
five_m_cvd = CvdDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    bar_between_signals=5,
    strategy=cvd_diver_five,
    position_handler=RiskFreeForex(
        ForexAgent(), stoploss_pip=70, takeprofit_pip=70, riskfree_trigger_pip=35
    ),
)


TraderBot("Gold CVD Bot", [one_m_cvd, five_m_cvd], report_time={"h": 23, "m": 58})


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
