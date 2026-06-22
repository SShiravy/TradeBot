from Coinex import CoinexAgent, CoinexDiverTradeConfig
from ChartModule import Chart, TimeFrame
from DivergenceStrategy.divergence import Divergence
from ChartModule.Indicators import EMA
from Forex import ForexAgent, CvdDiverTradeConfig, ForexDiverTradeConfig
from TradingModule.PositionHandlers import (
    RiskFreeForex,
    SlTpRatioCrypto,
    SlTpRatioForex,
    SteppingHandlerForex,
    SteppingHandlerCrypto,
)
from config import settings
# Coinex ----------------------------------------------------------------


coinex_agent = CoinexAgent(settings.COINEX_ACCESS_ID, settings.COINEX_SECRET_KEY)

crypto_diver_five_m = CoinexDiverTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.five_minutes),
    second_chart=Chart("BTCUSDT", TimeFrame.five_minutes),
    strategy=Divergence(2, 500, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=SteppingHandlerCrypto(
        coinex_agent,
        leverage=30,
        stoploss_percent=0.25,
        initial_volume=1,
        long_trade=False,
        short_trade=False,
        trail_stop=True,
    ),
    agent=coinex_agent,
    heikingashi_chartdata=True,
)

# one_h_diver = CoinexDiverTradeConfig(
#     chart=Chart("SOLUSDT", TimeFrame.one_hour),
#     second_chart=Chart("BTCUSDT", TimeFrame.one_hour),
#     strategy=Divergence(5, 500, name="CoinexDiver", inverse_diver_long=True),
#     position_handler=SteppingCrypto(
#         coinex_agent,
#         stoploss_percent=5,
#         initial_volume=10,
#         leverage=10,
#         long_trade=False,
#         short_trade=False,
#     ),
#     agent=coinex_agent,
#     heikingashi_chartdata=True,
# )


coinex_4h_diver = CoinexDiverTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.four_hours),
    second_chart=Chart("BTCUSDT", TimeFrame.four_hours),
    strategy=Divergence(3, 100, [], name="CoinexDiver", inverse_diver_long=False),
    position_handler=SlTpRatioCrypto(
        coinex_agent,
        ratio=1,
        stoploss_percent=2,
        initial_volume=10,
        leverage=10,
        long_trade=False,
        short_trade=False,
    ),
    agent=coinex_agent,
    heikingashi_chartdata=True,
)

# FOREX ----------------------------------------------------------------


forex_diver_one_m = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    second_chart=Chart("SOLUSD", TimeFrame.one_minute),
    strategy=Divergence(5, 200, [], name="ForexDiver", body_candle=True),
    bar_between_signals=2,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        targets_ratio=[1, 2, 3],
        stoploss_pip=15,
        targets_ratio_volumes=[0.01, 0.01, 0.01],
        targets_in_pip=[10],
        targets_in_pip_volumes=[0.01],
        long_trade=False,
        short_trade=False,
        trail_stop=True,
    ),
    merge_two_chart_time=False,
    heikingashi_chartdata=True,
)


# forex_diver_five_m = ForexDiverTradeConfig(
#     chart=Chart("XAUUSD!", TimeFrame.five_minutes),
#     second_chart=Chart("SOLUSD", TimeFrame.five_minutes),
#     strategy=Divergence(5, 50, [], name="ForexDiver"),
#     bar_between_signals=5,
#     position_handler=(
#         SteppingHandlerForex(
#             ForexAgent(),
#             targets_ratio= [1,2,3]
#             targets_ratio_volumes=[0.01, 0.01, 0.01],
#             stoploss_pip=50,
#             targets_in_pip=[50, 100, 150],
#             long_trade=False,
#             short_trade=False,
#             trail_stop=True,
#         )
#     ),
#     merge_two_chart_time=True,
#     heikingashi_chartdata=True,
# )

# CVD ----

diver_one_cvd = Divergence(
    7,
    100,
    [EMA(30)],
    name="ForexCVD",
    long_second_line_validation=False,
    short_second_line_validation=False,
)

cvd_diver_one_m_cvd = CvdDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    bar_between_signals=5,
    strategy=diver_one_cvd,
    position_handler=SlTpRatioForex(
        ForexAgent(),
        2,
        stoploss_pip=20,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

diver_five_cvd = Divergence(
    5,
    50,
    [],
    name="ForexCVD",
    long_second_line_validation=False,
    short_second_line_validation=False,
)
cvd_diver_five_m_cvd = CvdDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    bar_between_signals=5,
    strategy=diver_five_cvd,
    position_handler=RiskFreeForex(
        ForexAgent(), stoploss_pip=70, takeprofit_pip=70, riskfree_trigger_pip=35
    ),
)
