from typing import Any
from abc import ABC, abstractmethod
from ChartModule.models import MarketSide, Signal
from ChartModule.timing import TimeHandler
from TradingModule import Position, PositionSide
from datetime import timedelta
import logging

from TradingModule.models import Trigger


logger = logging.getLogger("Reporter")

class Reporter(ABC):
    def __init__(self, name:str, signal_channel, report_channel):
        self.name = name
        self.signal_channel = signal_channel
        self.report_channel = report_channel
        self._reporting = True
    
    def disable_reporting(self):
            self._reporting = False
            logger.info(f"⚠️ {self.name} Reporting Disabled")
    
    def enable_reporting(self):
        self._reporting = True
        logger.info(f"👍 {self.name} Reporting Enabled")

    @abstractmethod
    async def send_msg(
            self, msg, file_path: str | None = None, img_path: str | None = None, channel_id: Any = None, *args, **kwargs
        )-> Any:...
    
    async def new_position(self, position: Position, img_path:str|None=None):
        msg_list = [
            position.source,
            f"📊 {position.chart}",
            "🟢 Long" if position.side is PositionSide.LONG else "🔴 Short",
            f"🧾 {position.type.value}"
            f"📣 Entry = {position.entry_price}",
            f"💰 Entry Volume: {position.entry_volume}",
            f"⛔️ SL = {position.stoploss}"
        ]
        if position.triggers:
            msg_list.append("🎯Triggers:")
            for trigger in position.steps:
                tgr_msg = f"  {trigger.type} {trigger.price}"
                if trigger.volume:
                    tgr_msg += f"|{trigger.volume}💰"
                msg_list.append(tgr_msg)

        if position.leverage not in [1, 0]:
            msg_list.append(f"⚡Leverage: {position.leverage}")

        msg = "\n\n".join(msg_list)
        res = await self.send_msg(msg=msg,img_path=img_path)
        position.msg_id = res.message_id if res else 0

    async def position_closed(self, position: Position):
        duration = timedelta(seconds=(TimeHandler.elapsed_since(position.defined_timestamp)))

        close_type_msg = "⭕ Flat Close"
        if position.pnl_dollar > 0:
            close_type_msg = "✅ TP Triggered"
        elif position.pnl_dollar < 0:
            close_type_msg = "⛔️ SL Triggered"

        msg_list = [
            close_type_msg,
            position.source,
            f"📊 {position.chart}",
            f"💵 PNL = {position.pnl_dollar}",
            f"⌛ Duration = {duration}",
        ]
        msg = "\n\n".join(msg_list)
        await self.send_msg(msg=msg, reply_id=position.msg_id)

    async def sl_trailed(self, position: Position):
        trail_type_msg = (
            "📝 Risk Free"
            if position.stoploss == position.entry_price
            else "📝 Trailing Stop"
        )
        msg_list = [
            position.source,
            trail_type_msg,
            f"📊 {position.chart}",
            f"💲 New SL = {position.stoploss}",
        ]
        msg = "\n\n".join(msg_list)
        await self.send_msg(msg, reply_id=position.msg_id)

    async def triggered_step(self, position: Position, trigger:Trigger):
        duration = timedelta(
            seconds=TimeHandler.elapsed_since(Trigger.defined_timestamp))

        msg_list = [
            position.source,
            f"📊 {position.chart}",
            f"✅ {Trigger.type} Triggered",
            f"💲 Triggered Price = {trigger.price}",
            f"⌛ Duration = {duration}",
        ]
        if trigger.volume:
            msg_list.insert(-2,f"💰 Volume: {trigger.volume}")
        msg = "\n\n".join(msg_list)
        await self.send_msg(msg, reply_id=position.msg_id)

    async def new_signal(self, signal: Signal, img_path:str|None=None):
        msg_list = [
            signal.source,
            f"📊 {signal.chart}",
            "🟢 Bullish" if signal.side is MarketSide.BULLISH else "🔴 Bearish",
        ]
        msg = "\n\n".join(msg_list)
        await self.send_msg(msg, img_path=img_path)

    async def report(self, msg, file_path: str | None = None):
        await self.send_msg(msg,channel_id=self.report_channel, file_path=file_path)

