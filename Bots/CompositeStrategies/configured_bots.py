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

rsi_choch_reporter = TelegramReporter(
    "Divergence", "8470075659:AAHxX4BDBiUeKB85REsL8RB7jpe8XeubDbc", "@three_push"
)

#  ----------------------------------------------------------------
#  ----------------------------------------------------------------
#  Oscillator Choch -----------------------------------------------
#  ----------------------------------------------------------------
#  ----------------------------------------------------------------

xau_5m_rsi_choch = OscillatorDiverChochBot(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    oscillator_chart=Chart("XAUUSD!", TimeFrame.five_minutes),
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
        choch_mode=1,
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
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    oscillator_chart=Chart("XAUUSD!", TimeFrame.five_minutes),
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
        choch_mode=1,
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
