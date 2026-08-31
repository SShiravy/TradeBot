from ChartModule import Chart, TimeFrame
from EmaPivotChochStrategy.ema_pivot_choch import EmaPivotChochFilter
from Forex import ForexAgent, ForexEmaPivotChochTradeConfig
from BitUnix import BitUnixAgent, BitUnixEmaPivotChochTradeConfig
from TradingModule.PositionHandlers import SteppingHandlerForex, SteppingHandlerCrypto
from config import settings

# Forex ----------------------------------------------------------------
# HTF (1h) pivots + 3 EMAs decide the zone/direction, LTF (5m) looks for the
# CHoCH/BOS entry trigger within the next 100 candles.

ema_pivot_choch_xau_five_m = ForexEmaPivotChochTradeConfig(
    chart=Chart("XAUUSD", TimeFrame.five_minutes),
    htf_chart=Chart("XAUUSD", TimeFrame.one_hour),
    strategy=EmaPivotChochFilter(
        ema_periods=[21, 55, 89],
        htf_pivot_length=15,
        htf_backstep=2,
        atr_period=14,
        atr_multiplier=1.0,
        max_bars_after_pivot=100,
        choch_pivot_length=12,
        choch_backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=True,  # False -> confirm entry on the CHoCH/BOS break itself
        name="EmaPivotChoch",
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

ema_pivot_choch_fifteen_m_sol = BitUnixEmaPivotChochTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.fifteen_minutes),
    htf_chart=Chart("SOLUSDT", TimeFrame.four_hours),
    strategy=EmaPivotChochFilter(
        ema_periods=[21, 55, 89],
        htf_pivot_length=10,
        htf_backstep=2,
        atr_period=14,
        atr_multiplier=1.0,
        max_bars_after_pivot=100,
        choch_pivot_length=10,
        choch_backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="EmaPivotChoch",
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
