from Bots.EmaStrategy.ema_pivot_choch import EmaPivotChochBot, EmaPivotChochFilter
from ChartModule.models import Chart, TimeFrame, ChartType
from ExchangeAgents.MT5.agent import MT5Agent
from TraderBot.PositionHandlers.PositionGenerators import ForexStepping
from TraderBot.PositionHandlers import TradesManager
from TelegramBot import TelegramReporter
from Settings import settings

mt5_agent = MT5Agent(settings.METATRADER_TERMINAL_PATH)

reporter = TelegramReporter(
    "EMA_Touch", "8937168160:AAHtl4qXCSKXgT6YTSZEvYYDSHs3UcVqD5Y", "@crypto_result_1"
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
        reporter=reporter,
        agent_check=False,
    ),
    bar_between_signals=2,
    consider_position=False,
    agent=mt5_agent,
    n_candle_check=150,
)
