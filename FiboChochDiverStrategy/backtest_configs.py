from FiboChochDiverStrategy import FiboChochDiver
from Coinex import CoinexAgent, CoinexDiverTradeConfig
from ChartModule import Chart, TimeFrame
from DivergenceStrategy.divergence import Divergence
from FiboChochStrategy.fibochoch import FiboChoch
from TradingModule.position_handlers import (
    RiskFreeCrypto,
    SimpleCryptoHandler,
    SimpleForexHandler,
)
from Forex import ForexAgent, ForexDiverTradeConfig
from config import settings


# Coinex ----------------------------------------------------------------

coinex_agent = CoinexAgent(settings.COINEX_ACCESS_ID, settings.COINEX_SECRET_KEY)

one_h_diver = CoinexDiverTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.one_hour),
    second_chart=Chart("BTCUSDT", TimeFrame.one_hour),
    strategy=Divergence(5, 300, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=RiskFreeCrypto(
        coinex_agent,
        long_trade=False,
        short_trade=False,
    ),
    agent=coinex_agent,
    heikingashi_chartdata=True,
)


coinex_five_m = FiboChochDiver(
    divergence_config=one_h_diver,
    chart=Chart("SOLUSDT", TimeFrame.five_minutes),
    agent=coinex_agent,
    strategy=FiboChoch("CoinexFiboChochTest"),
    position_handler=SimpleCryptoHandler(
        coinex_agent,
        stoploss_percent=0.1,
        takeprofit_percent=0.25,
        leverage=10,
        initial_volume=10,
    ),
    bar_between_signals=0,
    send_signal=False,
)


# FOREX ----------------------------------------------------------------


forex_diver_five_m = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    second_chart=Chart("SOLUSD", TimeFrame.five_minutes),
    strategy=Divergence(15, 50, [], name="ForexDiver"),
    bar_between_signals=5,
    position_handler=(SimpleForexHandler(ForexAgent())),
    merge_two_chart_time=False,
)


forex_one_m = FiboChochDiver(
    divergence_config=forex_diver_five_m,
    chart=Chart("SOLUSD", TimeFrame.one_minute),
    agent=ForexAgent(),
    strategy=FiboChoch("CoinexFiboChochTest", pivot_right=2, pivot_left=10),
    position_handler=SimpleForexHandler(
        ForexAgent(),
        stoploss_pip=1,
        takeprofit_pip=8,
        initial_volume=0.01,
    ),
    bar_between_signals=1,
    send_signal=False,
)
