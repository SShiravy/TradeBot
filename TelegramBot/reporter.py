import logging
from typing import Any
from telegram import Bot
from ChartModule.models import MarketSide, Signal
from TraderBot.models import (
    PnLReport,
    Position,
    PositionSide,
    ReportMsgFormater,
    ReporterBot,
)

logger = logging.getLogger("TelegramReporter")


class TelegramMsgFormater(ReportMsgFormater):
    def identifier(self, position: Position) -> list[str]:
        return [f"🏷️ {position.source}", f"📊 {position.chart}"]

    def new_position(self, position: Position) -> str:
        msg_list = [
            *self.identifier(position),
            "🟢 Long "
            if position.side is PositionSide.LONG
            else "🔴 Short " + position.type.value,
            f"📣 Entry = {position.entry_price}",
            f"💰 Entry Volume: {position.volume}",
            f"⛔️ SL = {position.stoploss}",
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
        return msg

    def position_closed(self, position: Position, pnl_report: PnLReport) -> str:
        close_type_msg = "⭕ Flat Close"
        if pnl_report.pnl_dollar > 0:
            close_type_msg = "✅ Profitable Close"
        elif pnl_report.pnl_dollar < 0:
            close_type_msg = "⛔️ "

        msg_list = [
            *self.identifier(position),
            close_type_msg,
            f"💵 PNL = {pnl_report.pnl_dollar}",
            f"⌛ Duration = {pnl_report.duration}",
        ]
        msg = "\n\n".join(msg_list)
        return msg

    def sl_trailed(self, position: Position) -> str:
        trail_type_msg = (
            "📝 Risk Free"
            if position.stoploss == position.entry_price
            else "📝 Trailing Stop"
        )
        msg_list = [
            trail_type_msg,
            f"💲 New SL = {position.stoploss}",
        ]
        msg = "\n\n".join(msg_list)
        return msg

    def trigger_hit(self, position: Position, pnl_report: PnLReport) -> str:
        if position.steps[-1].triggered_timestamp:
            return self.position_closed(position, pnl_report)
        triggers_msg = []
        for trigger in position.steps:
            if trigger.triggered_timestamp:
                msg = f"🎯 {trigger.type} {trigger.price}"
                if trigger.volume:
                    msg += f"|{trigger.volume}💰"
                triggers_msg.append(msg)
        triggers_msg[-1] = triggers_msg[-1].replace("🎯", "✅")
        msg_list = [
            *self.identifier(position),
            *triggers_msg,
            f"💵 PNL = {pnl_report.pnl_dollar}",
            f"⌛ Duration = {pnl_report.duration}",
        ]
        msg = "\n\n".join(msg_list)
        return msg

    def new_signal(self, signal: Signal) -> str:
        msg_list = [
            f"🏷️ {signal.source}",
            f"📊 {signal.chart}🟢 Bullish"
            if signal.side is MarketSide.BULLISH
            else "🔴 Bearish",
        ]
        msg = "\n\n".join(msg_list)
        return msg


class TelegramReporter(ReporterBot):
    def __init__(
        self,
        name: str,
        bot_token: str,
        channel: str | int,
        msg_formater: ReportMsgFormater | None = None,
    ):
        self.name = name
        self.bot = Bot(bot_token)
        self.channel = channel
        self.enable = True
        self.msg_formater = msg_formater if msg_formater else TelegramMsgFormater()

    async def send_msg(
        self,
        msg,
        img_path: str | None = None,
        reply_id: None | int = None,
        channel_id: Any = None,
        file_path: str | None = None,
    ):
        if not self.enable:
            return False
        channel_id = channel_id if channel_id else self.channel
        res = None
        if img_path:
            img = open(img_path, "rb")
            res = await self.bot.send_photo(
                chat_id=channel_id, photo=img, caption=msg, reply_to_message_id=reply_id
            )
            img.close()

        elif file_path:
            file = open(file_path, "rb")
            res = await self.bot.send_document(
                chat_id=channel_id,
                document=file,
                caption=msg,
                reply_to_message_id=reply_id,
            )
            file.close()

        else:
            try:
                res = await self.bot.send_message(
                    chat_id=channel_id, text=msg, reply_to_message_id=reply_id
                )
            except Exception as e:
                logger.error(f"Error occurred while sending {msg=}: {e}")

        logger.debug(f"telegram response: {res}")
        return res.message_id if res else None
