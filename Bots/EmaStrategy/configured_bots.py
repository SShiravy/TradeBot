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

# same bot token, two separate channels - one per strategy
_BOT_TOKEN = "8937168160:AAHtl4qXCSKXgT6YTSZEvYYDSHs3UcVqD5Y"
ema_touch_reporter = TelegramReporter("EMA_Touch", _BOT_TOKEN, "@crypto_result_1")
ema_pivot_choch_reporter = TelegramReporter(
    "EMA_Pivot_Choch", _BOT_TOKEN, "@crypto_trader_robot"
)

# the same forex majors + crypto symbols already traded by the other
# strategies (Bots/CompositeStrategies/configured_bots/sr_choch_bots.py) -
# XAUUSD is handled separately below with its own tuned parameters.
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


def _make_ema_touch_bot(symbol: str, agent, stepping) -> EmaTouchBot:
    return EmaTouchBot(
        chart=Chart(symbol, TimeFrame.five_minutes),
        agent=agent,
        strategy=EmaTouchFilter(
            ema_periods=[20, 50, 100],
            min_candles_between_touches=15,
            max_candles_between_touches=200,
            reanchor_invalid_touch=False,
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


def _make_ema_pivot_choch_bot(symbol: str, agent, stepping) -> EmaPivotChochBot:
    return EmaPivotChochBot(
        chart=Chart(symbol, TimeFrame.five_minutes),
        htf_chart=Chart(symbol, TimeFrame.one_hour),
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


xau_3m = EmaPivotChochBot(
    chart=Chart("XAUUSD", TimeFrame.one_minute),
    htf_chart=Chart("XAUUSD", TimeFrame.three_minutes),
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
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=ema_pivot_choch_reporter,
        agent_check=False,
    ),
    bar_between_signals=2,
    consider_position=False,
    agent=mt5_agent,
    n_candle_check=150,
)


xau_ema_touch_1m = EmaTouchBot(
    chart=Chart("XAUUSD", TimeFrame.one_minute),
    agent=mt5_agent,
    strategy=EmaTouchFilter(
        ema_periods=[20, 50, 100],
        min_candles_between_touches=15,
        max_candles_between_touches=200,
        reanchor_invalid_touch=False,
        name="EmaTouch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
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


# forex majors (MT5) + crypto (BitUnix), same symbol universe the other
# strategies already trade
forex_ema_touch_bots = [
    _make_ema_touch_bot(symbol, mt5_agent, ForexStepping()) for symbol in FOREX_MAJORS
]
crypto_ema_touch_bots = [
    _make_ema_touch_bot(
        symbol,
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.14,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[0.0003, 0.0003, 0.0003],
        ),
    )
    for symbol in CRYPTO_SYMBOLS
]

forex_ema_pivot_choch_bots = [
    _make_ema_pivot_choch_bot(symbol, mt5_agent, ForexStepping())
    for symbol in FOREX_MAJORS
]
crypto_ema_pivot_choch_bots = [
    _make_ema_pivot_choch_bot(
        symbol,
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.14,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[0.0003, 0.0003, 0.0003],
        ),
    )
    for symbol in CRYPTO_SYMBOLS
]

ema_touch_bots = [xau_ema_touch_1m, *forex_ema_touch_bots, *crypto_ema_touch_bots]
ema_pivot_choch_bots = [xau_3m, *forex_ema_pivot_choch_bots, *crypto_ema_pivot_choch_bots]
