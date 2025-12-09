from Forex import ForexAgent, ForexDiverTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule import TraderBot
from TradingModule.position_handlers import RiskFreeForex
from DivergenceStrategy.divergence import Divergence
from custom_logger import CustomLogger
import asyncio


CustomLogger(log_file=True, file_log_name="ForexDiverBot")


one_m = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    second_chart=Chart("SOLUSD", TimeFrame.one_minute),
    strategy=Divergence(7, 50, [], name="ForexDiver"),
    bar_between_signals=5,
    position_handler=RiskFreeForex(
        ForexAgent(), takeprofit_pip=30, stoploss_pip=30, riskfree_trigger_pip=15
    ),
)


five_m = ForexDiverTradeConfig(
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


TraderBot(
    "Gold Diver Bot",
    [one_m, five_m],
)


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
