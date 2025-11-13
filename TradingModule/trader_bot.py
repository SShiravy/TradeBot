from ChartModule.models import IndicatorBaseModel, Chart, ChartData, TimeFrame
from ChartModule.Indicators.models import SupportConditions
from TradingModule import ExchangeAgent, Position
from TradingModule.position_handlers import PositionHandler
from TradingModule.commands import TradeCommand
from TradingModule.Strategies.model import Strategy
from TelegramModule import TelegramBot
from datetime import datetime, timezone
from config import settings
import asyncio
from dataclasses import dataclass, asdict, field
import tracemalloc


@dataclass
class TraderBotConfig:
    chart: Chart
    agent: ExchangeAgent
    strategy: Strategy
    position_handler: PositionHandler

    def save_as_json(self, name: str):
        pass

    def load_from_json(self, path: str):
        pass


class TraderBot:
    def __new__(cls, name: str = "", configs: list[TraderBotConfig] = []):
        if not hasattr(cls, "_instance"):
            cls._instance = object.__new__(cls)
            cls.name = name
            cls.configs = configs
            cls.telegram_bot = TelegramBot(
                settings.TELEGRAM_BOT_TOKEN,
                settings.TELEGRAM_CHANNEL_ID,
                settings.TELEGRAM_REPORT_CHANNEL,
            )
            cls._start_time = datetime.now(tz=timezone.utc).replace(microsecond=0)
        return cls._instance

    async def heartbeat(self):
        while True:
            await asyncio.sleep(3)
            current, peak = tracemalloc.get_traced_memory()
            elapsed_time = str(
                datetime.now(tz=timezone.utc).replace(microsecond=0) - self._start_time
            )
            msg = f"{self.name}\n👋🤖\nLifespan⌛:\n{elapsed_time}\nMemory📝:\n{current / 1024 / 1024:.2f} MB\npeak: {peak / 1024 / 1024:.2f} MB"
            await self.telegram_bot.send_report(msg)

    async def start(self):
        tracemalloc.start()
        await self.telegram_bot.send_report(
            f"--{self.name}--\n⚡⚡\nStart at\n{self._start_time} utc\n⚡⚡"
        )
        tasks = [self.heartbeat()]

        await asyncio.gather(*tasks)
