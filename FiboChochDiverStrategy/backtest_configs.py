from ChartModule.Indicators.fibonacci import FiboLevels
from FiboChochDiverStrategy import FiboChochDiver
from Coinex import CoinexAgent, CoinexDiverTradeConfig
from ChartModule import Chart, TimeFrame
from DivergenceStrategy.divergence import Divergence
from FiboChochStrategy.fibochoch import FiboChoch
from TradingModule.PositionHandlers import (
    RiskFreeCrypto,
    SimpleForex,
    SlTpRatioCrypto,
    SlTpRatioForex,
)
from Forex import ForexAgent, ForexDiverTradeConfig
from config import settings


# Coinex ----------------------------------------------------------------

coinex_agent = CoinexAgent(settings.COINEX_ACCESS_ID, settings.COINEX_SECRET_KEY)

one_h_diver = CoinexDiverTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.one_hour),
    second_chart=Chart("BTCUSDT", TimeFrame.one_hour),
    strategy=Divergence(2, 300, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=RiskFreeCrypto(
        coinex_agent,
        long_trade=False,
        short_trade=False,
    ),
    agent=coinex_agent,
    heikingashi_chartdata=False,
    bar_between_signals=1,
    n_candle_check=5,
)


coinex_five_m = FiboChochDiver(
    divergence_config=one_h_diver,
    chart=Chart("SOLUSDT", TimeFrame.five_minutes),
    agent=coinex_agent,
    strategy=FiboChoch("CoinexFiboChochTest", pivot_right=10,fibo_level=FiboLevels.LEVEL_382),
    position_handler=SlTpRatioCrypto(
        coinex_agent,
        ratio=1.5,
        stoploss_percent=0.1,
        leverage=10,
        initial_volume=20,
    ),
    n_fich_signal_per_diver=4,
    bar_between_signals=1,
    send_signal=False,
    n_bar_support_range=500,
)


# FOREX ----------------------------------------------------------------


forex_diver_five_m = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    second_chart=Chart("SOLUSD", TimeFrame.five_minutes),
    strategy=Divergence(3, 300, [], name="ForexDiver"),
    position_handler=(SimpleForex(ForexAgent())),
    merge_two_chart_time=False,
    bar_between_signals=1,
)


forex_one_m = FiboChochDiver(
    divergence_config=forex_diver_five_m,
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    agent=ForexAgent(),
    strategy=FiboChoch("CoinexFiboChochTest", pivot_right=1, pivot_left=15),
    position_handler=SlTpRatioForex(
        ForexAgent(),
        ratio=0,
        stoploss_pip=1,
        initial_volume=0.01,
    ),
    bar_between_signals=1,
    send_signal=False,
    n_fich_signal_per_diver=1,
    n_bar_support_range=300,
    check_start_fibo=False,
)
