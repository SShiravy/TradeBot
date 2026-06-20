from FiboChochStrategy.fibochoch import FiboChochConfig, FiboChoch
from Forex import ForexAgent
from TradingModule.PositionHandlers import (
    SimpleCrypto,
)
from ChartModule.Indicators.fibonacci import FiboLevels
from Coinex import CoinexAgent
from ChartModule import Chart, TimeFrame
from TradingModule.PositionHandlers.stepping_handler import SteppingHandlerForex
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
        long_trade=False,
        short_trade=False,
    ),
    bar_between_signals=1,
    send_signal=False,
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
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    agent=ForexAgent(),
    strategy=FiboChoch(
        "CoinexFiboChochTest",
        long_pivot_left=15,
        long_pivot_right=3,
        short_pivot_left=15,
        short_pivot_right=3,
    ),
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        targets_ratio=[1],
        stoploss_pip=10,
        targets_ratio_volumes=[0.01],
        long_trade=False,
        short_trade=False,
        trail_stop=True,
    ),
    bar_between_signals=1,
    send_signal=False,
    short_signal=False,
)
