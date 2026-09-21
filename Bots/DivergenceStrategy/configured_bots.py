from Bots.ChochStrategy.choch import ChochQueueFilter
from Bots.CompositeStrategies.oscillator_diver_choch import OscillatorDiverChochBot
from Bots.DivergenceStrategy.oscillator_double_divergence import (
    OscillatorDoubleDiverBot,
)
from ChartModule.Indicators.models import SupportCandlesPattern
from ChartModule.models import Chart, TimeFrame, ChartType
from ChartModule.Indicators import RSI, EMA, HMA
from Bots.DivergenceStrategy import (
    Divergence,
    DivergenceBot,
    OscillatorDivergence,
    OscillatorDiverBot,
)
from ExchangeAgents.MT5.agent import MT5Agent
from TraderBot.PositionHandlers.PositionGenerators import ForexStepping
from TraderBot.PositionHandlers import TradesManager
from TelegramBot import TelegramReporter
from Settings import settings

mt5_agent = MT5Agent(settings.METATRADER_TERMINAL_PATH)

reporter = TelegramReporter(
    "Divergence", settings.TELEGRAM_TEST_BOT, settings.TELEGRAM_TEST_CHANNEL
)

xau_jpy_1m = DivergenceBot(
    chart=Chart("XAUUSD", TimeFrame.one_minute, ChartType.Simple),
    second_chart=Chart("USDJPY", TimeFrame.one_minute, ChartType.Simple),
    agent=mt5_agent,
    strategy=Divergence(min_step=5, max_step=150, indicators=[EMA(50)]),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)


xau_dxy_1m = DivergenceBot(
    chart=Chart("XAUUSD", TimeFrame.one_minute, ChartType.Heikinashi),
    second_chart=Chart("DXY", TimeFrame.one_minute, ChartType.Heikinashi),
    agent=mt5_agent,
    strategy=Divergence(min_step=2, max_step=150, indicators=[EMA(50)]),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)

#  Crypto ---------------------------------------------------------

btc_sol_1m = DivergenceBot(
    chart=Chart("BTCUSD", TimeFrame.one_minute, ChartType.Simple),
    second_chart=Chart("SOLUSD", TimeFrame.one_minute, ChartType.Simple),
    agent=mt5_agent,
    strategy=Divergence(min_step=2, max_step=10, indicators=[HMA(20), EMA(50)]),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)

btc_eth_1m = DivergenceBot(
    chart=Chart("BTCUSD", TimeFrame.one_minute, ChartType.Simple),
    second_chart=Chart("ETHUSD", TimeFrame.one_minute, ChartType.Simple),
    agent=mt5_agent,
    strategy=Divergence(min_step=2, max_step=10, indicators=[EMA(50)]),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)

#  ----------------------------------------------------------------
#  ----------------------------------------------------------------
#  Oscillator -----------------------------------------------------
#  ----------------------------------------------------------------
#  ----------------------------------------------------------------

xau_rsi_1m = OscillatorDiverBot(
    chart=Chart("XAUUSD", TimeFrame.one_minute, ChartType.Simple),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        oscillator_indicator=RSI(20),
        min_step=2,
        max_step=150,
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
    n_candle_check=150,
    consider_position=False,
)


btc_rsi_1m = OscillatorDiverBot(
    chart=Chart("BTCUSD", TimeFrame.one_minute, ChartType.Simple),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        oscillator_indicator=RSI(20),
        min_step=2,
        max_step=10,
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
    n_candle_check=150,
    consider_position=False,
)


sol_rsi_1m = OscillatorDiverBot(
    chart=Chart("SOLUSD", TimeFrame.one_minute, ChartType.Simple),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        oscillator_indicator=RSI(20),
        min_step=2,
        max_step=10,
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
    n_candle_check=150,
    consider_position=False,
)


xau_rsi_1m = OscillatorDiverBot(
    chart=Chart("XAUUSD", TimeFrame.one_minute, ChartType.Simple),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        oscillator_indicator=RSI(20),
        min_step=2,
        max_step=150,
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
    n_candle_check=150,
    consider_position=False,
)


xau_rsi_1m = OscillatorDiverBot(
    chart=Chart("XAUUSD", TimeFrame.one_minute, ChartType.Simple),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        oscillator_indicator=RSI(20),
        min_step=2,
        max_step=150,
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
    n_candle_check=150,
    consider_position=False,
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
        reporter=reporter,
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
        reporter=reporter,
        agent_check=False,
    ),
    n_candle_check=150,
    consider_position=False,
)


#  ----------------------------------------------------------------
#  ----------------------------------------------------------------
#  Oscillator Double Diver ----------------------------------------
#  ----------------------------------------------------------------
#  ----------------------------------------------------------------


xau_rsi_double_diver_5m = OscillatorDoubleDiverBot(
    chart=Chart("XAUUSD!", TimeFrame.five_minutes),
    agent=mt5_agent,
    strategy=OscillatorDivergence(
        oscillator_indicator=RSI(20),
        min_step=2,
        max_step=150,
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
)
