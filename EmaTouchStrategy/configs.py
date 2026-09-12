from Forex import ForexAgent, ForexEmaTouchTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule.PositionHandlers.stepping_handler import SteppingHandlerForex
from EmaTouchStrategy.ema_touch import EmaTouchFilter


xau_5m = ForexEmaTouchTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

xau_1h = ForexEmaTouchTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

xau_4h = ForexEmaTouchTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)


eurusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("EURUSD!", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

usdjpy_1h = ForexEmaTouchTradeConfig(
    chart=Chart("USDJPY!", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

gbpusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("GBPUSD!", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

usdchf_1h = ForexEmaTouchTradeConfig(
    chart=Chart("USDCHF!", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

audusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("AUDUSD!", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

usdcad_1h = ForexEmaTouchTradeConfig(
    chart=Chart("USDCAD!", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

nzdusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("NZDUSD!", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

adausd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("ADAUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

aveusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("AVEUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

filusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("FILUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

atomusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("ATOMUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

apeusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("APEUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

zecusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("ZECUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

neousd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("NEOUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

iotausd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("IOTAUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

xtzusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("XTZUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

xrpusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("XRPUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

xmrusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("XMRUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

xlmusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("XLMUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

vetusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("VETUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

uniusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("UNIUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

solusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("SOLUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

mtcusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("MTCUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

ltcusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("LTCUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

lnkusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("LNKUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

dshusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("DSHUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

dotusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("DOTUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

dogusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("DOGUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

btcusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("BTCUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

bsvusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("BSVUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

bnbusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("BNBUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

bchusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("BCHUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

axsusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("AXSUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

avxusd_1h = ForexEmaTouchTradeConfig(
    chart=Chart("AVXUSD", TimeFrame.one_hour),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)


eurusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("EURUSD!", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

usdjpy_4h = ForexEmaTouchTradeConfig(
    chart=Chart("USDJPY!", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

gbpusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("GBPUSD!", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

usdchf_4h = ForexEmaTouchTradeConfig(
    chart=Chart("USDCHF!", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

audusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("AUDUSD!", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

usdcad_4h = ForexEmaTouchTradeConfig(
    chart=Chart("USDCAD!", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

nzdusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("NZDUSD!", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

adausd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("ADAUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

aveusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("AVEUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

filusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("FILUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

atomusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("ATOMUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

apeusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("APEUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

zecusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("ZECUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

neousd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("NEOUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

iotausd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("IOTAUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

xtzusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("XTZUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

xrpusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("XRPUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

xmrusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("XMRUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

xlmusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("XLMUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

vetusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("VETUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

uniusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("UNIUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

solusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("SOLUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

mtcusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("MTCUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

ltcusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("LTCUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

lnkusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("LNKUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

dshusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("DSHUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

dotusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("DOTUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

dogusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("DOGUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

btcusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("BTCUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

bsvusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("BSVUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

bnbusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("BNBUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

bchusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("BCHUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

axsusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("AXSUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)

avxusd_4h = ForexEmaTouchTradeConfig(
    chart=Chart("AVXUSD", TimeFrame.four_hours),
    n_candle_check=500,
    strategy=EmaTouchFilter(
        ema_periods=[20],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    bar_between_signals=2,
    consider_position=False,
    position_handler=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=1,
        targets_ratio=[1],
        targets_ratio_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=False,
)
