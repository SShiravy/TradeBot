from Bots.ChochStrategy.choch import ChochBot, ChochQueueFilter
from ChartModule.models import Chart, TimeFrame
from ExchangeAgents.MT5.agent import MT5Agent
from TelegramBot.reporter import TelegramReporter
from TraderBot.PositionHandlers.PositionGenerators.stepping import ForexStepping
from TraderBot.PositionHandlers.manager import TradesManager
from Settings import settings


mt5_agent = MT5Agent(settings.METATRADER_TERMINAL_PATH)


reporter = TelegramReporter(
    "Choch", settings.TELEGRAM_TEST_BOT, settings.TELEGRAM_TEST_CHANNEL
)


xau_choch_1m = ChochBot(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    agent=mt5_agent,
    strategy=ChochQueueFilter(
        pivot_length=2, backstep=2, choch_mode=1, retrace_fib=0.5, use_fibo_filter=True
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
    n_candle_check=200,
    consider_position=False,
)
