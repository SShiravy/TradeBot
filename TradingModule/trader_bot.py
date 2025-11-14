from TradingModule import ExchangeAgent, Position, OrderSide
from TradingModule.position_handlers import PositionHandler
from ChartModule.models import Chart, Candle, Signal, ChartData
from TradingModule.Strategies.model import Strategy
from datetime import datetime, timezone, timedelta
from ChartModule.plot import PlotChart
from TelegramModule import TelegramBot
from TradingModule import commands
from dataclasses import dataclass, field
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

    long_signal: bool = field(default=True)
    short_signal: bool = field(default=True)

    long_trade: bool = field(default=True)
    short_trade: bool = field(default=True)

    bar_between_signals: int = field(default=2)
    send_signal: bool = field(default=True)

    n_bar_check: int = field(default=100)

    heikingashi_chartdata: bool = field(default=False)

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

        logging.debug(
            f"{delay=}\n{last_candle.time=}\n{last_candle.time.astimezone(timezone.utc)=}\nnow={datetime.now(timezone.utc)}\n"
        )

        return (
            (delay + last_candle.time)
            - datetime.now(timezone.utc)
            + timedelta(seconds=1)
        )

    def get_chartdata(self) -> ChartData:
        chartdata = self.agent.get_chartdata(self.chart, n_bars=self.n_bar_check)
        if chartdata is None:
            raise ValueError(f"chart data is None from {self.agent.__name__}")
        if self.heikingashi_chartdata:
            chartdata = chartdata.give_heikingashi_chartdata()
        return chartdata

    def find_signal(
        self, chartdata: ChartData, *args, **kwargs
    ) -> None | tuple[Signal, Position]:
        signal = self.strategy.check_signal(
            chartdata, self.long_signal, self.short_signal
        )
        if signal is None:
            return None

        position = self.position_handler.generate_position(signal)

        if (self.long_trade and position.side is OrderSide.BUY) or (
            self.short_trade and position.side is OrderSide.SELL
        ):
            command = commands.OpenPosition(position)
            command.execute(self.agent)
        return signal, position

    async def task(
        self, telegram_bot: TelegramBot
    ) -> timedelta | tuple[timedelta, Signal, Position]:
        chartdata = self.get_chartdata()
        res = self.find_signal(chartdata)
        if res is None:
            return self.give_delay(chartdata[-1])
        signal, position = res
        if self.send_signal:
            plot = PlotChart(chartdata)
            self.strategy.draw(plot, signal, draw_indicators=True)
            position.draw(plot)
            img_path = plot.save_image()
            await telegram_bot.send_photo_to_channel(
                img_path, self.msg_generator(position)
            )

        return self.give_delay(signal.candle, jump=True), signal, position

    def save_as_json(self, name: str):
        # TODO: merge all sub obj attr in a single dict
        pass

    def load_from_json(self, path: str):
        pass

    def __str__(self) -> str:
        msg_list = [
            str(self.chart),
            self.agent.__class__.__name__,
            self.strategy.name,
            self.position_handler.__class__.__name__,
        ]
        return "|".join(msg_list)


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
        logging.debug(f"Task with config:{str(config)} initilized")
        error_number = 0
        while True:
            try:
                res = await config.task(self.telegram_bot)
                if isinstance(res, timedelta):
                    sleep_time = res
                else:
                    sleep_time = res[0]
                # TODO: Check sub chartdata in old code
                logging.debug(sleep_time)
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
                        f"Error:{e}\non {config}\nMore Than 6 Times\nTask removed"
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
        # TODO: add commend execute
        # TODO: add clear and report all
        # TODO: add other handlres and add get_chartdata_since
        await asyncio.gather(*tasks)
