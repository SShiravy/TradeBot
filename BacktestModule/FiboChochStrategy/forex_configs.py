from TradingModule.Strategies.choch import FiboChoch, FiboChochConfig
from Forex import ForexAgent
from ChartModule import Chart, TimeFrame
from TradingModule.position_handlers import SimpleForexHandler


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
