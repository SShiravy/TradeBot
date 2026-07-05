from ChartModule import Chart, TimeFrame
from ChartModule.Indicators.models import SupportCandleConditions
from ChartModule.Indicators.rsi import RSI
from DivergenceStrategy import Divergence
from ChartModule.Indicators import EMA
from DivergenceStrategy.oscillator_divergence import (
    OscillatorDiverConfig,
    OscillatorDivergence,
)
from DivergenceStrategy.oscillator_double_divergence import OscillatorDoubleDiverConfig
from Forex import ForexAgent, ForexDiverTradeConfig
from BitUnix import BitUnixAgent, BitUnixDiverTradeConfig
from TradingModule.PositionHandlers import (
    RiskFreeForex,
    SlTpRatioForex,
    SteppingHandlerForex,
    SteppingHandlerCrypto,
)
from config import settings

# Crypto ----------------------------------------------------------------


# coinex_agent = CoinexAgent(settings.COINEX_ACCESS_ID, settings.COINEX_SECRET_KEY)
bitunix_agent = BitUnixAgent(settings.BITUNIX_API_KEY, settings.BITUNIX_API_SECRET_KEY)

crypto_diver_five_m_sol = BitUnixDiverTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.five_minutes),
    second_chart=Chart("BTCUSDT", TimeFrame.five_minutes),
    strategy=Divergence(2, 500, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=SteppingHandlerCrypto(
        bitunix_agent,
        leverage=30,
        stoploss_percent=0.7,
        targets_ratio=[1, 2, 3],
        initial_volume=0.1,
        long_trade=False,
        short_trade=False,
        trail_stop=True,
    ),
    agent=bitunix_agent,
    heikingashi_chartdata=True,
)


crypto_diver_five_m_near = BitUnixDiverTradeConfig(
    chart=Chart("NEARUSDT", TimeFrame.five_minutes),
    second_chart=Chart("BTCUSDT", TimeFrame.five_minutes),
    strategy=Divergence(3, 100, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=SteppingHandlerCrypto(
        bitunix_agent,
        leverage=30,
        stoploss_percent=0.7,
        targets_ratio=[1, 2, 3],
        initial_volume=4,
        long_trade=False,
        short_trade=False,
        trail_stop=True,
    ),
    agent=bitunix_agent,
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


forex_rsi_diver_five_m = OscillatorDiverConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    agent=ForexAgent(),
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="ForexOscillatorDiver",
        long_support_conditions=SupportCandleConditions.LOWER_LOW,
        short_support_conditions=SupportCandleConditions.HIGHER_HIGH,
        inverse_diver_long=False,
    ),
    bar_between_signals=2,
    position_handler=(
        SteppingHandlerForex(
            ForexAgent(),
            targets_ratio=[1, 2, 3],
            targets_ratio_volumes=[0.01, 0.01, 0.01],
            stoploss_pip=50,
            targets_in_pip=[],
            long_trade=False,
            short_trade=False,
            trail_stop=True,
        )
    ),
    heikingashi_chartdata=False,
)


forex_rsi_double_diver_five_m = OscillatorDoubleDiverConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    agent=ForexAgent(),
    strategy=OscillatorDivergence(
        RSI(),
        3,
        200,
        [],
        name="ForexOscillatorDiver",
        long_support_conditions=SupportCandleConditions.RED_GREEN,
        short_support_conditions=SupportCandleConditions.GREEN_RED,
        body_candle=False,
        inverse_diver_long=False,
    ),
    bar_between_signals=2,
    position_handler=(
        SteppingHandlerForex(
            ForexAgent(),
            targets_ratio=[1, 2, 3],
            targets_ratio_volumes=[0.01, 0.01, 0.01],
            stoploss_pip=50,
            targets_in_pip=[],
            long_trade=False,
            short_trade=False,
            trail_stop=True,
        )
    ),
    heikingashi_chartdata=False,
)
# CVD ----


# diver_five_cvd = Divergence(
#     5,
#     50,
#     [],
#     name="ForexCVD",
#     long_other_chart_line_validation=False,
#     short_other_chart_line_validation=False,
# )
# cvd_diver_five_m_cvd = CvdDiverTradeConfig(
#     chart=Chart("XAUUSD!", TimeFrame.five_minutes),
#     bar_between_signals=5,
#     strategy=diver_five_cvd,
#     position_handler=RiskFreeForex(
#         ForexAgent(), stoploss_pip=70, takeprofit_pip=70, riskfree_trigger_pip=35
#     ),
# )
