from Bots.ChochStrategy.choch import ChochQueueFilter
from Bots.CompositeStrategies.oscillator_diver_choch import OscillatorDiverChochBot

from ChartModule.Indicators import RSI
from Bots.DivergenceStrategy import OscillatorDivergence
from ChartModule.models import Chart, TimeFrame
from ExchangeAgents.MT5.agent import MT5Agent
from TraderBot.PositionHandlers.PositionGenerators import ForexStepping
from TraderBot.PositionHandlers import TradesManager
from TelegramBot import TelegramReporter
from Settings import settings

mt5_agent = MT5Agent(settings.METATRADER_TERMINAL_PATH)


#  ----------------------------------------------------------------
#  ----------------------------------------------------------------
#  Oscillator Diver Choch ----------------------------------
#  ----------------------------------------------------------------
#  ----------------------------------------------------------------


rsi_choch_reporter = TelegramReporter(
    "RSI_Diver_CHoCH", settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHANNEL_ID
)


xau_5m_rsi_choch = OscillatorDiverChochBot(
    chart=Chart("XAUUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("XAUUSD", TimeFrame.five_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)


xau_15m_rsi_choch = OscillatorDiverChochBot(
    chart=Chart("XAUUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("XAUUSD", TimeFrame.fifteen_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)

eurusd_5m_rsi_choch = OscillatorDiverChochBot(
    chart=Chart("EURUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("EURUSD", TimeFrame.five_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)

eurusd_15m_rsi_choch = OscillatorDiverChochBot(
    chart=Chart("EURUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("EURUSD", TimeFrame.fifteen_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)


usdjpy_5m_rsi_choch = OscillatorDiverChochBot(
    chart=Chart("USDJPY", TimeFrame.one_minute),
    oscillator_chart=Chart("USDJPY", TimeFrame.five_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)

usdjpy_15m_rsi_choch = OscillatorDiverChochBot(
    chart=Chart("USDJPY", TimeFrame.one_minute),
    oscillator_chart=Chart("USDJPY", TimeFrame.fifteen_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)


gbpusd_5m_rsi_choch = OscillatorDiverChochBot(
    chart=Chart("GBPUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("GBPUSD", TimeFrame.five_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)

gbpusd_15m_rsi_choch = OscillatorDiverChochBot(
    chart=Chart("GBPUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("GBPUSD", TimeFrame.fifteen_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)


usdchf_5m_rsi_choch = OscillatorDiverChochBot(
    chart=Chart("USDCHF", TimeFrame.one_minute),
    oscillator_chart=Chart("USDCHF", TimeFrame.five_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)

usdchf_15m_rsi_choch = OscillatorDiverChochBot(
    chart=Chart("USDCHF", TimeFrame.one_minute),
    oscillator_chart=Chart("USDCHF", TimeFrame.fifteen_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)


audusd_5m_rsi_choch = OscillatorDiverChochBot(
    chart=Chart("AUDUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("AUDUSD", TimeFrame.five_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)

audusd_15m_rsi_choch = OscillatorDiverChochBot(
    chart=Chart("AUDUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("AUDUSD", TimeFrame.fifteen_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)


usdcad_5m_rsi_choch = OscillatorDiverChochBot(
    chart=Chart("USDCAD", TimeFrame.one_minute),
    oscillator_chart=Chart("USDCAD", TimeFrame.five_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)

usdcad_15m_rsi_choch = OscillatorDiverChochBot(
    chart=Chart("USDCAD", TimeFrame.one_minute),
    oscillator_chart=Chart("USDCAD", TimeFrame.fifteen_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)


nzdusd_5m_rsi_choch = OscillatorDiverChochBot(
    chart=Chart("NZDUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("NZDUSD", TimeFrame.five_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)

nzdusd_15m_rsi_choch = OscillatorDiverChochBot(
    chart=Chart("NZDUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("NZDUSD", TimeFrame.fifteen_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)


#  ----------------------------------------------------------------
#  ----------------------------------------------------------------
#  Oscillator Dobule Diver Choch ----------------------------------
#  ----------------------------------------------------------------
#  ----------------------------------------------------------------


rsi_double_diver_choch_reporter = TelegramReporter(
    "RSI_double_Diver_CHoCH",
    "8470075659:AAHxX4BDBiUeKB85REsL8RB7jpe8XeubDbc",
    "@three_push",
)


xau_5m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("XAUUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("XAUUSD", TimeFrame.five_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


xau_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("XAUUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("XAUUSD", TimeFrame.fifteen_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)

eurusd_5m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("EURUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("EURUSD", TimeFrame.five_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)

eurusd_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("EURUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("EURUSD", TimeFrame.fifteen_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


usdjpy_5m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("USDJPY", TimeFrame.one_minute),
    oscillator_chart=Chart("USDJPY", TimeFrame.five_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)

usdjpy_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("USDJPY", TimeFrame.one_minute),
    oscillator_chart=Chart("USDJPY", TimeFrame.fifteen_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


gbpusd_5m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("GBPUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("GBPUSD", TimeFrame.five_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)

gbpusd_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("GBPUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("GBPUSD", TimeFrame.fifteen_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


usdchf_5m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("USDCHF", TimeFrame.one_minute),
    oscillator_chart=Chart("USDCHF", TimeFrame.five_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)

usdchf_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("USDCHF", TimeFrame.one_minute),
    oscillator_chart=Chart("USDCHF", TimeFrame.fifteen_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


audusd_5m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("AUDUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("AUDUSD", TimeFrame.five_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)

audusd_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("AUDUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("AUDUSD", TimeFrame.fifteen_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


usdcad_5m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("USDCAD", TimeFrame.one_minute),
    oscillator_chart=Chart("USDCAD", TimeFrame.five_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)

usdcad_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("USDCAD", TimeFrame.one_minute),
    oscillator_chart=Chart("USDCAD", TimeFrame.fifteen_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


nzdusd_5m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("NZDUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("NZDUSD", TimeFrame.five_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)

nzdusd_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("NZDUSD", TimeFrame.one_minute),
    oscillator_chart=Chart("NZDUSD", TimeFrame.fifteen_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
        inverse_diver_long=False,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=2,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)
