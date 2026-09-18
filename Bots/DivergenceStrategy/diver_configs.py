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

mt5_agent = MT5Agent(settings.METATRADER_TERMINAL_PATH,utc_shift=settings.BROKER_UTC_SHIFT)

reporter = TelegramReporter(
    "Divergence", settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHANNEL_ID
)

xau_jpy_1m = DivergenceBot(
    chart=Chart("XAUUSD", TimeFrame.one_minute, ChartType.Simple),
    second_chart=Chart("USDJPY", TimeFrame.one_minute, ChartType.Simple),
    agent=mt5_agent,
    strategy=Divergence(min_step=2, max_step=150, indicators=[EMA(20)]),
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
    chart=Chart("XAUUSD", TimeFrame.one_minute, ChartType.Simple),
    second_chart=Chart("DXY", TimeFrame.one_minute, ChartType.Simple),
    agent=mt5_agent,
    strategy=Divergence(min_step=2, max_step=150, indicators=[HMA(20),EMA(50)]),
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
