from Forex import ForexAgent, ForexDiverTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule import TraderBot
from TradingModule.position_handlers import SimpleForexHandler, RiskFreeForex
from TradingModule.Strategies.divergence import Divergence
from custom_logger import CustomLogger
import asyncio


CustomLogger(log_file=True, file_log_name="ForexDiverBot")


one_m = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    second_chart=Chart("SOLUSD", TimeFrame.one_minute),
    strategy=Divergence(3, 100, [], name="ForexDiver"),
    position_handler=RiskFreeForex(
        ForexAgent(), takeprofit_pip=5, stoploss_pip=5, riskfree_trigger_pip=2
    ),
)


five_m = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    second_chart=Chart("SOLUSD", TimeFrame.five_minutes),
    strategy=Divergence(3, 100, [], name="ForexDiver"),
    position_handler=(
        RiskFreeForex(
            ForexAgent(), stoploss_pip=10, takeprofit_pip=10, riskfree_trigger_pip=5
        )
    ),
)


TraderBot(
    "Gold Diver Bot",
    [one_m, five_m],
)


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
