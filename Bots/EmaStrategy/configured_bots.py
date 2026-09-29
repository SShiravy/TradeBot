from Bots.EmaStrategy.ema_pivot_choch import EmaPivotChochBot, EmaPivotChochFilter
from Bots.EmaStrategy.ema_touch import EmaTouchBot, EmaTouchFilter
from ChartModule.models import Chart, TimeFrame
from ExchangeAgents.MT5.agent import MT5Agent
from ExchangeAgents.BitUnix.agent import BitUnixAgent
from TraderBot.PositionHandlers.PositionGenerators import ForexStepping, CryptoStepping
from TraderBot.PositionHandlers import TradesManager
from TelegramBot import TelegramReporter
from Settings import settings

mt5_agent = MT5Agent(settings.METATRADER_TERMINAL_PATH)
bitunix_agent = BitUnixAgent(settings.BITUNIX_API_KEY, settings.BITUNIX_API_SECRET_KEY)

ema_touch_reporter = TelegramReporter(
    "EMA_Touch",
    "8937168160:AAHtl4qXCSKXgT6YTSZEvYYDSHs3UcVqD5Y",
    "@crypto_result_1",
)

ema_pivot_choch_reporter = TelegramReporter(
    "EMA_Pivot_Choch",
    settings.TELEGRAM_BOT_TOKEN,
    settings.TELEGRAM_CRYPTO_CHANNEL_ID,
)

FOREX_MAJORS = [
    "EURUSD!",
    "USDJPY!",
    "GBPUSD!",
    "USDCHF!",
    "AUDUSD!",
    "USDCAD!",
    "NZDUSD!",
]

CRYPTO_SYMBOLS = [
    "ADAUSDT",
    "AAVEUSDT",
    "FILUSDT",
    "ATOMUSDT",
    "ZECUSDT",
    "IOTAUSDT",
    "XTZUSDT",
    "XRPUSDT",
    "XLMUSDT",
    "VETUSDT",
    "UNIUSDT",
    "SOLUSDT",
    "POLUSDT",
    "LTCUSDT",
    "LINKUSDT",
    "DOTUSDT",
    "DOGEUSDT",
    "BTCUSDT",
    "BSVUSDT",
    "BNBUSDT",
    "BCHUSDT",
]


# EmaTouch runs on 3 timeframes per symbol: 5m, 1h, 4h
EMA_TOUCH_TIMEFRAMES = [
    TimeFrame.five_minutes,
    TimeFrame.one_hour,
    TimeFrame.four_hours,
]


def _make_ema_touch_bot(symbol: str, timeframe: TimeFrame, agent, stepping) -> EmaTouchBot:
    return EmaTouchBot(
        chart=Chart(symbol, timeframe),
        agent=agent,
        strategy=EmaTouchFilter(
            ema_periods=[20, 50, 100],
            min_candles_between_touches=15,
            max_candles_between_touches=200,
            reanchor_invalid_touch=True,
            name="EmaTouch",
        ),
        trades_manager=TradesManager(
            agent,
            stepping,
            long_trade=True,
            short_trade=True,
            trading_constraints=[],
            reporter=ema_touch_reporter,
            agent_check=False,
        ),
        bar_between_signals=2,
        consider_position=False,
        n_candle_check=500,
    )


def _make_ema_touch_bots(symbol: str, agent, stepping) -> list[EmaTouchBot]:
    return [
        _make_ema_touch_bot(symbol, timeframe, agent, stepping)
        for timeframe in EMA_TOUCH_TIMEFRAMES
    ]


# EmaPivotChoch runs on 3 LTF/HTF pairs per symbol:
#   1m/5m, 5m/1h, 5m/4h
LTF_HTF_PAIRS = [
    (TimeFrame.one_minute, TimeFrame.five_minutes),
    (TimeFrame.five_minutes, TimeFrame.one_hour),
    (TimeFrame.five_minutes, TimeFrame.four_hours),
]


def _make_ema_pivot_choch_bot(
    symbol: str, ltf: TimeFrame, htf: TimeFrame, agent, stepping
) -> EmaPivotChochBot:
    return EmaPivotChochBot(
        chart=Chart(symbol, ltf),
        htf_chart=Chart(symbol, htf),
        n_ema_htf_candle_check=120,
        n_htf_candle_check=120,
        strategy=EmaPivotChochFilter(
            ema_periods=[20, 40, 60],
            htf_pivot_length=12,
            htf_backstep=2,
            atr_period=14,
            atr_multiplier=1.0,
            max_bars_after_pivot=100,
            choch_pivot_length=2,
            choch_backstep=2,
            retrace_fib=0.5,
            use_fibo_filter=False,
            use_bos=False,
            use_choch=False,
            name="EmaPivotChoch",
        ),
        trades_manager=TradesManager(
            agent,
            stepping,
            long_trade=True,
            short_trade=True,
            trading_constraints=[],
            reporter=ema_pivot_choch_reporter,
            agent_check=False,
        ),
        bar_between_signals=2,
        consider_position=False,
        agent=agent,
        n_candle_check=150,
    )


def _make_ema_pivot_choch_bots(symbol: str, agent, stepping) -> list[EmaPivotChochBot]:
    return [
        _make_ema_pivot_choch_bot(symbol, ltf, htf, agent, stepping)
        for ltf, htf in LTF_HTF_PAIRS
    ]


xau_ema_pivot_choch_bots = _make_ema_pivot_choch_bots(
    "XAUUSD", mt5_agent, ForexStepping()
)

xau_3m = xau_ema_pivot_choch_bots[0]


xau_ema_touch_bots = _make_ema_touch_bots("XAUUSD", mt5_agent, ForexStepping())

xau_ema_touch_1m = xau_ema_touch_bots[0]


forex_ema_touch_bots = [
    bot
    for symbol in FOREX_MAJORS
    for bot in _make_ema_touch_bots(symbol, mt5_agent, ForexStepping())
]
crypto_ema_touch_bots = [
    bot
    for symbol in CRYPTO_SYMBOLS
    for bot in _make_ema_touch_bots(
        symbol,
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.14,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[0.0003, 0.0003, 0.0003],
        ),
    )
]

forex_ema_pivot_choch_bots = [
    bot
    for symbol in FOREX_MAJORS
    for bot in _make_ema_pivot_choch_bots(symbol, mt5_agent, ForexStepping())
]
crypto_ema_pivot_choch_bots = [
    bot
    for symbol in CRYPTO_SYMBOLS
    for bot in _make_ema_pivot_choch_bots(
        symbol,
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.14,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[0.0003, 0.0003, 0.0003],
        ),
    )
]

ema_touch_bots = [*xau_ema_touch_bots, *forex_ema_touch_bots, *crypto_ema_touch_bots]
ema_pivot_choch_bots = [
    *xau_ema_pivot_choch_bots,
    *forex_ema_pivot_choch_bots,
    *crypto_ema_pivot_choch_bots,
]
