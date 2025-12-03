from TradingModule.Strategies.choch import FiboChochConfig, FiboChoch
from Coinex import CoinexAgent
from ChartModule import Chart, TimeFrame
from TradingModule.position_handlers import RiskFreeCrypto
from config import settings

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
