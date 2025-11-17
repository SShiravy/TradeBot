from Forex import ForexAgent, CvdDiverTradeConfig, ForexDiverTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule import TraderBot
from TradingModule.position_handlers import SimpleForexHandler, RiskFreeForex
from TradingModule.Strategies.divergence import Divergence
from custom_logger import CustomLogger
import asyncio

CustomLogger(log_file=True, file_log_name="ForexBot")


forex_one_m_diver = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    second_chart=Chart("SOLUSD", TimeFrame.one_minute),
    strategy=Divergence(3, 100, [], name="ForexDiver"),
    position_handler=SimpleForexHandler(
        ForexAgent(), takeprofit_pip=10, stoploss_pip=10
    )
)


forex_five_m_diver = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    second_chart=Chart("SOLUSD", TimeFrame.five_minutes),
    strategy=Divergence(3, 100, [], name="ForexDiver"),
    position_handler=(RiskFreeForex(ForexAgent()))
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
    )
)

forex_five_m_cvd = CvdDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    strategy=cvd_diver,
    position_handler=SimpleForexHandler(ForexAgent())
)



TraderBot(
    "ForexBot", [forex_one_m_cvd, forex_five_m_cvd, forex_one_m_diver, forex_five_m_diver]
)

# TODO: fix forex diver two chart get chart problem on live 
# TODO: Trailing Stop when its Trade off
# TODO: sl tp msg


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
