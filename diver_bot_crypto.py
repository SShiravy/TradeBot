from BitUnix.agent import BitUnixAgent
from BitUnix.bot_configs import BitUnixDiverTradeConfig
from ChartModule import Chart, TimeFrame
from TradingModule.PositionHandlers.stepping_handler import SteppingHandlerCrypto
from TradingModule.reporter import TelegramReporter
from TradingModule.trader_bot import TraderBot
from DivergenceStrategy.divergence import Divergence
from custom_logger import CustomLogger
from config import settings
import asyncio
import logging

CustomLogger(
    log_file=True, file_log_name="CryptoDiverBot", consol_log_level=logging.DEBUG
)

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
    heikingashi_chartdata=True,
)


diver_five_m_near = BitUnixDiverTradeConfig(
    chart=Chart("NEARUSDT", TimeFrame.five_minutes),
    second_chart=Chart("BTCUSDT", TimeFrame.five_minutes),
    strategy=Divergence(3, 100, [], name="BitUnixNearDiver", inverse_diver_long=True),
    position_handler=SteppingHandlerCrypto(
        bitunix_agent,
        leverage=30,
        stoploss_percent=0.7,
        targets_ratio=[1, 2, 3],
        initial_volume=5,
        trail_stop=True,
    ),
    agent=bitunix_agent,
    heikingashi_chartdata=True,
)

TelegramReporter().main_channel = settings.TELEGRAM_CRYPTO_CHANNEL_ID
TraderBot("BitUnix Diver Bot", [diver_five_m_sol], report_time={"h": 20, "m": 1})


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
