from Forex import ForexAgent, CvdDiverTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule import TraderBot
from TradingModule.position_handlers import SimpleForexHandler
from TradingModule.Strategies.divergence import Divergence
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
    position_handler=SimpleForexHandler(
        ForexAgent(), stoploss_pip=10, takeprofit_pip=10
    ),
)

five_m_cvd = CvdDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    strategy=cvd_diver,
    position_handler=SimpleForexHandler(ForexAgent()),
)


TraderBot(
    "Gold CVD Bot",
    [one_m_cvd, five_m_cvd],
)


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
