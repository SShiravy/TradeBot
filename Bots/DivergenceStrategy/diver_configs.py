from ChartModule.Indicators.moving_avg import EMA
from ChartModule.models import Chart, TimeFrame, ChartType
from Bots.DivergenceStrategy.divergence import Divergence, DivergenceBot
from ExchangeAgents.MT5.agent import MT5Agent
from TraderBot.PositionHandlers.PositionGenerators import ForexStepping
from TraderBot.PositionHandlers import TradesManager
from TelegramBot import TelegramReporter
from Settings import settings

mt5_agent = MT5Agent(settings.METATRADER_TERMINAL_PATH)
reporter = TelegramReporter(
    "Divergence", settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHANNEL_ID
)

xau_jpy_1m = DivergenceBot(
    chart=Chart("XAUUSD", TimeFrame.one_minute, ChartType.Simple),
    second_chart=Chart("USDJPY", TimeFrame.one_minute, ChartType.Heikinashi),
    agent=mt5_agent,
    strategy=Divergence(min_step=2, max_step=200, indicators=[]),
    trades_manager=TradesManager(
        mt5_agent,
        ForexStepping(),
        long_trade=True,
        short_trade=True,
        trading_constraints=[],
        reporter=reporter,
        agent_check=False,
    ),
    consider_position=False,
)
