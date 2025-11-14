from Forex import ForexAgent, CvdDiverTradeConfig, ForexDiverTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule import TraderBot
from TradingModule.position_handlers import SimpleForexHandler
from TradingModule.Strategies.divergence import Divergence
from custom_logger import CustomLogger
import asyncio

CustomLogger(log_file=True, file_log_name="ForexBot")


one_m_diver = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    second_chart=Chart("SOLUSD", TimeFrame.one_minute),
    strategy=Divergence(3, 100, [], name="ForexDiver"),
    position_handler=SimpleForexHandler(ForexAgent()),
)


five_m_diver = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    second_chart=Chart("SOLUSD", TimeFrame.five_minutes),
    strategy=Divergence(3, 100, [], name="ForexDiver"),
    position_handler=SimpleForexHandler(ForexAgent()),
)

fifteen_m_diver = ForexDiverTradeConfig(
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

one_m_cvd = CvdDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    strategy=cvd_diver,
    position_handler=SimpleForexHandler(ForexAgent()),
)

five_m_cvd = CvdDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    strategy=cvd_diver,
    position_handler=SimpleForexHandler(ForexAgent()),
)


TraderBot(
    "ForexBot", [one_m_diver, five_m_diver, fifteen_m_diver, one_m_cvd, five_m_cvd]
)


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
