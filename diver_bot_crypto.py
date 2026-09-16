from ExchangeAgents.BitUnix.agent import BitUnixAgent
from ExchangeAgents.BitUnix.bot_configs import BitUnixDiverTradeConfig
from ChartModule import Chart, TimeFrame
from TraderBot.PositionHandlers.stepping_handler import SteppingHandlerCrypto
from TraderBot.reporter import TelegramReporter
from TraderBot.trader_bot import TraderBot
from Bots.DivergenceStrategy import Divergence
from Settings.custom_logger import build_logger, LoggerConfig
from Settings.config import settings
import asyncio


build_logger(LoggerConfig(name="root", log_file_name="CryptoDiverBot"))


bitunix_agent = BitUnixAgent(settings.BITUNIX_API_KEY, settings.BITUNIX_API_SECRET_KEY)

diver_five_m_sol = BitUnixDiverTradeConfig(
    chart=Chart("SOLUSDT", TimeFrame.five_minutes),
    second_chart=Chart("BTCUSDT", TimeFrame.five_minutes),
    strategy=Divergence(3, 100, [], name="BitUnixSolDiver", inverse_diver_long=True),
    position_handler=SteppingHandlerCrypto(
        bitunix_agent,
        leverage=30,
        stoploss_percent=0.7,
        targets_ratio=[1, 2, 3],
        initial_volume=0.1,
        trail_stop=True,
    ),
    agent=bitunix_agent,
)


TelegramReporter().signal_channel = settings.TELEGRAM_CRYPTO_CHANNEL_ID
TraderBot(
    "BitUnix Diver Bot",
    [diver_five_m_sol],
    report_time={"h": 20, "m": 15},
)


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
