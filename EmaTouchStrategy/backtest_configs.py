from ChartModule import Chart, TimeFrame
from EmaTouchStrategy.ema_touch import EmaTouchFilter
from Forex import ForexAgent, ForexEmaTouchTradeConfig
from BitUnix import BitUnixAgent, BitUnixEmaTouchTradeConfig
from TradingModule.PositionHandlers import SteppingHandlerForex, SteppingHandlerCrypto
from config import settings

# Forex ----------------------------------------------------------------

ema_touch_xau_five_m = ForexEmaTouchTradeConfig(
    chart=Chart("XAUUSD", TimeFrame.five_minutes),
    strategy=EmaTouchFilter(
        ema_periods=[20, 40, 60, 80],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    n_candle_check=500,
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

ema_touch_five_m_sol = BitUnixEmaTouchTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.five_minutes),
    strategy=EmaTouchFilter(
        ema_periods=[20, 40, 60, 80],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    n_candle_check=500,
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
