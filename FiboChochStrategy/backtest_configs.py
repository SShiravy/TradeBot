from FiboChochStrategy.choch import FiboChochConfig, FiboChoch
from Forex import ForexAgent
from TradingModule.position_handlers import SimpleForexHandler, RiskFreeCrypto
from Coinex import CoinexAgent
from ChartModule import Chart, TimeFrame
from config import settings


# COINEX ------------------------------------------------------

coinex_agent = CoinexAgent(settings.COINEX_ACCESS_ID, settings.COINEX_SECRET_KEY)

five_m = FiboChochConfig(
    Chart("SOLUSDT", TimeFrame.five_minutes),
    coinex_agent,
    FiboChoch("CoinexFiboChochTest"),
    RiskFreeCrypto(
        coinex_agent,
        riskfree_trigger_percent=0.5,
        stoploss_percent=1,
        takeprofit_percent=1,
        leverage=10,
        initial_volume=10,
    ),
    bar_between_signals=0,
    send_signal=False,
)

# FOREX ------------------------------------------------------


five_m = FiboChochConfig(
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
