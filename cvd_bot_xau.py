from Forex import ForexAgent, CvdDiverTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule.position_handlers import RiskFreeForex
from DivergenceStrategy.divergence import Divergence
from TradingModule import TraderBot
from custom_logger import CustomLogger
import asyncio

CustomLogger(log_file=True, file_log_name="ForexCVDBot")


cvd_diver = Divergence(
    3,
    100,
    [],
    name="ForexCVD",
    long_second_line_validation=False,
    short_second_line_validation=False,
)

one_m_cvd = CvdDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    strategy=cvd_diver,
    position_handler=RiskFreeForex(
        ForexAgent(), stoploss_pip=5, takeprofit_pip=5, riskfree_trigger_pip=2
    ),
)

five_m_cvd = CvdDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    strategy=cvd_diver,
    position_handler=RiskFreeForex(
        ForexAgent(), stoploss_pip=10, takeprofit_pip=10, riskfree_trigger_pip=5
    ),
)


TraderBot(
    "Gold CVD Bot",
    [one_m_cvd, five_m_cvd],
)


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
