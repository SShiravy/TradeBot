from TradingModule import ExchangeAgent, Position, OrderSide
from TradingModule.position_handlers import PositionHandler
from TradingModule.Strategies.model import Strategy
from datetime import datetime, timezone, timedelta
from ChartModule.models import Chart, Candle
from ChartModule.plot import PlotChart
from TelegramModule import TelegramBot
from TradingModule import commands
from dataclasses import dataclass
from config import settings
import tracemalloc
import asyncio
import logging


@dataclass
class TradeConfig:
    chart: Chart
    agent: ExchangeAgent
    strategy: Strategy
    position_handler: PositionHandler

    long_signal = True
    short_signal = True

    long_trade = True
    short_trade = True

    bar_between_signals = 2
    send_signal = True

    def msg_generator(self, position: Position):
        msg_list = [
            position.source,
            f"📊 {position.chart.symbol}",
            f"⌛ Timeframe: {position.chart.timeframe.value}",
            "🟢 LONG" if position.side is OrderSide.BUY else "🔴 SHORT",
            f"📣 Entry = {position.entry_price}",
            f"🎯 TP =  {position.takeprofit}",
            f"⛔️ SL = {position.stoploss}",
            f"⚡Volume: {position.volume}",
        ]

        msg = "\n\n".join(msg_list)

        if position.leverage not in [1, 0]:
            msg += f"\n\n⚡Leverage: {position.leverage}"
        return msg

    def give_delay(self, last_candle: Candle, jump=False) -> timedelta:
        delay = self.chart.timeframe.time_delta
        if jump:
            delay *= self.bar_between_signals

        return (
            (delay + last_candle.time)
            - datetime.now(timezone.utc)
            - timedelta(seconds=1)
        )

    async def task(self, telegram_bot: TelegramBot) -> timedelta:
        chartdata = self.agent.get_chartdata(self.chart, n_bars=200)
        if chartdata is None:
            raise ValueError(f"chart data is None from {self.agent.__name__}")

        signal = self.strategy.check_signal(
            chartdata, self.long_signal, self.short_signal
        )
        if signal is None:
            return self.give_delay(chartdata[-1])

        position = self.position_handler.generate_position(signal)

        if (self.long_trade and position.side is OrderSide.BUY) or (
            self.short_trade and position.side is OrderSide.SELL
        ):
            command = commands.OpenPosition(position)
            command.execute(self.agent)

        if self.send_signal:
            plot = PlotChart(chartdata)
            self.strategy.draw(plot, signal, draw_indicators=True)
            position.draw(plot)
            img_path = plot.save_image()
            await telegram_bot.send_photo_to_channel(
                img_path, self.msg_generator(position)
            )

        return self.give_delay(signal.candle, jump=True)

    def save_as_json(self, name: str):
        # TODO: merge all sub obj attr in a single dict
        pass

    def load_from_json(self, path: str):
        pass

    def __str__(self) -> str:
        return ""


class TraderBot:
    def __new__(cls, name: str = "", configs: list[TradeConfig] = []):
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

    async def trade_task(self, config: TradeConfig):
        error_number = 0
        while True:
            try:
                sleep_time = await config.task(self.telegram_bot)
                # TODO: Check sub chartdata in old code
                await asyncio.sleep(sleep_time.seconds)

            except Exception as e:
                error_number += 1
                logging.error(f"{error_number} Times Error:{e}\non {config}")
                if error_number == 3:
                    await self.telegram_bot.send_report(
                        f"3 Times Error:{e}\non {config}"
                    )
                elif error_number > 6:
                    await self.telegram_bot.send_report(
                        f"Error:{e}\non {config}\nMore Than 6 Times\n Task removed"
                    )
                    break
                continue

    async def heartbeat(self):
        while True:
            await asyncio.sleep(360)
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
        tasks = [self.trade_task(config) for config in self.configs]
        tasks.append(self.heartbeat())

        await asyncio.gather(*tasks)
