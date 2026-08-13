from ChartModule import Chart, TimeFrame
from ChochQueueStrategy.choch_queue import ChochQueueFilter
from Forex import ForexAgent, ForexChochQueueTradeConfig
from BitUnix import BitUnixAgent, BitUnixChochQueueTradeConfig
from TradingModule.PositionHandlers import SteppingHandlerForex, SteppingHandlerCrypto
from config import settings

# Forex ----------------------------------------------------------------

choch_queue_xau_one_m = ForexChochQueueTradeConfig(
    chart=Chart("XAUUSD", TimeFrame.one_minute),
    strategy=ChochQueueFilter(
        pivot_length=50,
        backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=True,  # False -> confirm signal on the CHoCH break itself
        name="ChochQueue",
    ),
    bar_between_signals=2,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        targets_ratio=[1, 2, 3],
        stoploss_pip=15,
        targets_ratio_volumes=[0.01, 0.01, 0.01],
        long_trade=False,
        short_trade=False,
        trail_stop=True,
    ),
    heikingashi_chartdata=False,
)


# Crypto -----------------------------------------------------------------

bitunix_agent = BitUnixAgent(settings.BITUNIX_API_KEY, settings.BITUNIX_API_SECRET_KEY)

choch_queue_five_m_sol = BitUnixChochQueueTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.five_minutes),
    strategy=ChochQueueFilter(
        pivot_length=30,
        backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="ChochQueue",
    ),
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
    heikingashi_chartdata=False,
)
