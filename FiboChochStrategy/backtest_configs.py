from FiboChochStrategy.fibochoch import FiboChochConfig, FiboChoch
from Forex import ForexAgent
from TradingModule.PositionHandlers import (
    SimpleForex,
    SimpleCrypto,
)
from ChartModule.Indicators.fibonacci import FiboLevels
from Coinex import CoinexAgent
from ChartModule import Chart, TimeFrame
from config import settings


# COINEX ------------------------------------------------------

coinex_agent = CoinexAgent(settings.COINEX_ACCESS_ID, settings.COINEX_SECRET_KEY)

coinex_five_m = FiboChochConfig(
    chart=Chart("SOLUSDT", TimeFrame.five_minutes),
    agent=coinex_agent,
    strategy=FiboChoch(
        "CoinexFiboChochTest",
        short_pivot_right=2,
        short_pivot_left=10,
        short_fibo_level=FiboLevels.LEVEL_382,
    ),
    position_handler=SimpleCrypto(
        coinex_agent,
        stoploss_percent=0.5,
        takeprofit_percent=0.5,
        leverage=10,
        initial_volume=10,
    ),
    bar_between_signals=1,
    send_signal=False,
    short_signal=False,
)


coinex_one_h = FiboChochConfig(
    chart=Chart("SOLUSDT", TimeFrame.one_hour),
    agent=coinex_agent,
    strategy=FiboChoch("CoinexFiboChochTest", confirmation_indicators=[]),
    position_handler=SimpleCrypto(
        coinex_agent,
        stoploss_percent=1,
        takeprofit_percent=2,
        leverage=20,
        initial_volume=10,
    ),
    bar_between_signals=0,
    send_signal=False,
    long_signal=False,
)

# FOREX ------------------------------------------------------


forex_five_m = FiboChochConfig(
    chart=Chart("SOLUSD", TimeFrame.five_minutes),
    agent=ForexAgent(),
    strategy=FiboChoch("CoinexFiboChochTest"),
    position_handler=SimpleForex(
        ForexAgent(),
        stoploss_pip=5,
        takeprofit_pip=5,
        initial_volume=0.01,
    ),
    bar_between_signals=0,
    send_signal=False,
)

one_m_forex = FiboChochConfig(
    chart=Chart("SOLUSD", TimeFrame.one_minute),
    agent=ForexAgent(),
    strategy=FiboChoch("CoinexFiboChochTest"),
    position_handler=SimpleForex(
        ForexAgent(),
        stoploss_pip=5,
        takeprofit_pip=5,
        initial_volume=0.01,
    ),
    bar_between_signals=0,
    send_signal=False,
)
