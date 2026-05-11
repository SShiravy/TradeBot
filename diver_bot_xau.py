from Forex import ForexAgent, ForexDiverTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule.PositionHandlers.ratio_stepping import RatioSteppingForex
from TradingModule.trader_bot import TraderBot
from DivergenceStrategy.divergence import Divergence
from custom_logger import CustomLogger
import asyncio
import logging

CustomLogger(
    log_file=True, file_log_name="ForexDiverBot", consol_log_level=logging.DEBUG
)

one_m = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    second_chart=Chart("SOLUSD", TimeFrame.one_minute),
    strategy=Divergence(2, 300, [], name="ForexDiver"),
    bar_between_signals=2,
    position_handler=RatioSteppingForex(
        ForexAgent(),
        stoploss_pip=30,
        targets_ratio=[1, 1.5, 2],
        initial_volume=[0.02, 0.01, 0.01],
        trail_stop=True,
    ),
    merge_two_chart_time=True,
    heikingashi_chartdata=True,
    send_signal=False,
)


# five_m = ForexDiverTradeConfig(
#     chart=Chart("XAUUSD!", TimeFrame.five_minutes),
#     second_chart=Chart("SOLUSD", TimeFrame.five_minutes),
#     strategy=Divergence(5, 50, [], name="ForexDiver"),
#     bar_between_signals=2,
#     position_handler=(
#         SlTpRatioForex(
#             ForexAgent(), 1.5, stoploss_pip=10, long_trade=False, short_trade=False
#         )
#     ),
#     merge_two_chart_time=True,
#     heikingashi_chartdata=True,
# )


TraderBot("Gold Diver Bot", [one_m], report_time={"h": 12, "m": 55})


if __name__ == "__main__":
    from TradingModule.reporter import TelegramReporter

    TelegramReporter().disable_reporting()
    asyncio.run(TraderBot().start())
