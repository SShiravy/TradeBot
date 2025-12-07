from FiboChochStrategy.fibochoch import FiboChochConfig, FiboChoch
from ChartModule.Indicators import EMA
from Forex import ForexAgent
from TradingModule.position_handlers import (
    SimpleForexHandler,
    RiskFreeCrypto,
    SimpleCryptoHandler,
)
from Coinex import CoinexAgent
from ChartModule import Chart, TimeFrame
from config import settings


# COINEX ------------------------------------------------------

coinex_agent = CoinexAgent(settings.COINEX_ACCESS_ID, settings.COINEX_SECRET_KEY)

coinex_five_m = FiboChochConfig(
    Chart("SOLUSDT", TimeFrame.five_minutes),
    coinex_agent,
    FiboChoch("CoinexFiboChochTest"),
    SimpleCryptoHandler(
        coinex_agent,
        stoploss_percent=0.5,
        takeprofit_percent=0.5,
        leverage=10,
        initial_volume=10,
    ),
    bar_between_signals=0,
    send_signal=False,
)


coinex_one_h = FiboChochConfig(
    Chart("SOLUSDT", TimeFrame.one_hour),
    coinex_agent,
    FiboChoch("CoinexFiboChochTest", confirmation_indicators=[]),
    SimpleCryptoHandler(
        coinex_agent,
        stoploss_percent=1,
        takeprofit_percent=2,
        leverage=20,
        initial_volume=10,
    ),
    bar_between_signals=0,
    send_signal=False,
)

# FOREX ------------------------------------------------------


forex_five_m = FiboChochConfig(
    Chart("SOLUSD", TimeFrame.five_minutes),
    ForexAgent(),
    FiboChoch("CoinexFiboChochTest"),
    SimpleForexHandler(
        ForexAgent(),
        stoploss_pip=5,
        takeprofit_pip=5,
        initial_volume=0.01,
    ),
    bar_between_signals=0,
    send_signal=False,
)
