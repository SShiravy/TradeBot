from Bots.ChochStrategy.choch import ChochQueueFilter
from Bots.CompositeStrategies.oscillator_diver_choch import OscillatorDiverChochBot

from ChartModule.Indicators import RSI
from Bots.DivergenceStrategy import OscillatorDivergence
from ChartModule.models import Chart, TimeFrame
from ExchangeAgents.MT5.agent import MT5Agent
from ExchangeAgents.BitUnix.agent import BitUnixAgent
from TraderBot.PositionHandlers.PositionGenerators import (
    ForexStepping,
    CryptoStepping,
)
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=True,
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
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
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
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=True,
)


#  ----------------------------------------------------------------
#  ----------------------------------------------------------------
#  Bitunix Oscillator Double Diver Choch ----------------------------------
#  ----------------------------------------------------------------
#  ----------------------------------------------------------------


bitunix_agent = BitUnixAgent(settings.BITUNIX_API_KEY, settings.BITUNIX_API_SECRET_KEY)


ada_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("ADAUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("ADAUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.41,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[82, 82, 82],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


ada_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("ADAUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("ADAUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.12,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[82, 82, 82],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


aave_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("AAVEUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("AAVEUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.38,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[0.2, 0.2, 0.2],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


aave_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("AAVEUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("AAVEUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.1,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[0.2, 0.2, 0.2],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


fil_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("FILUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("FILUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.44,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[19, 19, 19],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


fil_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("FILUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("FILUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.13,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[19, 19, 19],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


atom_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("ATOMUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("ATOMUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.41,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[11.59, 11.59, 11.59],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


atom_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("ATOMUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("ATOMUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.12,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[11.59, 11.59, 11.59],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


zec_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("ZECUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("ZECUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.42,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[0.014, 0.014, 0.014],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


zec_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("ZECUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("ZECUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.15,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[0.014, 0.014, 0.014],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


iota_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("IOTAUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("IOTAUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.98,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[362, 362, 362],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


iota_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("IOTAUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("IOTAUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.27,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[362, 362, 362],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


xtz_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("XTZUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("XTZUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.29,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[64.4, 64.4, 64.4],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


xtz_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("XTZUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("XTZUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.07,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[64.4, 64.4, 64.4],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


xrp_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("XRPUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("XRPUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.33,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[13.4, 13.4, 13.4],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


xrp_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("XRPUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("XRPUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.09,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[13.4, 13.4, 13.4],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


xlm_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("XLMUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("XLMUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.57,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[88, 88, 88],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


xlm_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("XLMUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("XLMUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.18,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[88, 88, 88],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


vet_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("VETUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("VETUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.36,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[2258, 2258, 2258],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


vet_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("VETUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("VETUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.1,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[2258, 2258, 2258],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


uni_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("UNIUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("UNIUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.44,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[3, 3, 3],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


uni_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("UNIUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("UNIUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.12,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[3, 3, 3],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


sol_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("SOLUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("SOLUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.26,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[0.17, 0.17, 0.17],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


sol_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("SOLUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("SOLUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.07,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[0.17, 0.17, 0.17],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


pol_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("POLUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("POLUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.43,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[172, 172, 172],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


pol_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("POLUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("POLUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.11,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[172, 172, 172],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


ltc_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("LTCUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("LTCUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.39,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[0.29, 0.29, 0.29],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


ltc_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("LTCUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("LTCUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.09,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[0.29, 0.29, 0.29],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


link_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("LINKUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("LINKUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.57,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[1.3, 1.3, 1.3],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


link_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("LINKUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("LINKUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.21,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[1.3, 1.3, 1.3],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


dot_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("DOTUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("DOTUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.46,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[17, 17, 17],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


dot_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("DOTUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("DOTUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.11,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[17, 17, 17],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


doge_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("DOGEUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("DOGEUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.32,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[214, 214, 214],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


doge_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("DOGEUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("DOGEUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.09,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[214, 214, 214],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


btc_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("BTCUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("BTCUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.14,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[0.0003, 0.0003, 0.0003],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


btc_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("BTCUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("BTCUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.03,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[0.0003, 0.0003, 0.0003],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


bsv_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("BSVUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("BSVUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.35,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[1, 1, 1],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


bsv_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("BSVUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("BSVUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.1,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[1, 1, 1],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


bnb_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("BNBUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("BNBUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.15,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[0.03, 0.03, 0.03],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


bnb_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("BNBUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("BNBUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.04,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[0.03, 0.03, 0.03],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


bch_1h_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("BCHUSDT", TimeFrame.five_minutes),
    oscillator_chart=Chart("BCHUSDT", TimeFrame.one_hour),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.33,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[0.1, 0.1, 0.1],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


bch_15m_rsi_double_diver_choch = OscillatorDiverChochBot(
    chart=Chart("BCHUSDT", TimeFrame.one_minute),
    oscillator_chart=Chart("BCHUSDT", TimeFrame.fifteen_minutes),
    agent=bitunix_agent,
    strategy=OscillatorDivergence(
        RSI(),
        3,
        100,
        [],
        name="RSI_Double_Diver",
        body_candle=True,
    ),
    choch_strategy=ChochQueueFilter(
        pivot_length=2,
        backstep=2,
        choch_mode=1,
        use_bos=False,
        retrace_fib=0.5,
        use_fibo_filter=True,
        name="Choch",
    ),
    trades_manager=TradesManager(
        bitunix_agent,
        CryptoStepping(
            leverage=10,
            sl_percent=0.09,
            tp_ratio=[1, 2, 3],
            tp_ratio_volumes=[0.1, 0.1, 0.1],
        ),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=rsi_double_diver_choch_reporter,
        agent_check=True,
    ),
    n_candle_check=150,
    double_diver=True,
    consider_position=False,
)


bitunix_rsi_double_diver_choch_bots = [
    ada_1h_rsi_double_diver_choch,
    ada_15m_rsi_double_diver_choch,
    aave_1h_rsi_double_diver_choch,
    aave_15m_rsi_double_diver_choch,
    fil_1h_rsi_double_diver_choch,
    fil_15m_rsi_double_diver_choch,
    atom_1h_rsi_double_diver_choch,
    atom_15m_rsi_double_diver_choch,
    zec_1h_rsi_double_diver_choch,
    zec_15m_rsi_double_diver_choch,
    iota_1h_rsi_double_diver_choch,
    iota_15m_rsi_double_diver_choch,
    xtz_1h_rsi_double_diver_choch,
    xtz_15m_rsi_double_diver_choch,
    xrp_1h_rsi_double_diver_choch,
    xrp_15m_rsi_double_diver_choch,
    xlm_1h_rsi_double_diver_choch,
    xlm_15m_rsi_double_diver_choch,
    vet_1h_rsi_double_diver_choch,
    vet_15m_rsi_double_diver_choch,
    uni_1h_rsi_double_diver_choch,
    uni_15m_rsi_double_diver_choch,
    sol_1h_rsi_double_diver_choch,
    sol_15m_rsi_double_diver_choch,
    pol_1h_rsi_double_diver_choch,
    pol_15m_rsi_double_diver_choch,
    ltc_1h_rsi_double_diver_choch,
    ltc_15m_rsi_double_diver_choch,
    link_1h_rsi_double_diver_choch,
    link_15m_rsi_double_diver_choch,
    dot_1h_rsi_double_diver_choch,
    dot_15m_rsi_double_diver_choch,
    doge_1h_rsi_double_diver_choch,
    doge_15m_rsi_double_diver_choch,
    btc_1h_rsi_double_diver_choch,
    btc_15m_rsi_double_diver_choch,
    bsv_1h_rsi_double_diver_choch,
    bsv_15m_rsi_double_diver_choch,
    bnb_1h_rsi_double_diver_choch,
    bnb_15m_rsi_double_diver_choch,
    bch_1h_rsi_double_diver_choch,
    bch_15m_rsi_double_diver_choch,
]
