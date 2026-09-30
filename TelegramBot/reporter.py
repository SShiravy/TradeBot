import asyncio
import logging
from typing import Any
from telegram import Bot
from telegram.error import BadRequest, NetworkError, RetryAfter, TimedOut
from telegram.request import HTTPXRequest
from ChartModule.models import MarketSide, Signal
from TraderBot.events import TakeProfitHit
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
            f"⛔️ SL = {position.stoploss.price}",
        ]
        if position.triggers:
            msg_list.append("🎯Triggers:")
            for i, trigger in enumerate(position.steps):
                name = (
                    "TakeProfit"
                    if isinstance(trigger.event, TakeProfitHit)
                    else trigger.event.name
                )
                tgr_msg = f"   {i + 1}-{name} {trigger.price}"
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
            close_type_msg = "⛔️ Loss"

        msg_list = [
            *self.identifier(position),
            close_type_msg,
            f"💵 PNL = {round(pnl_report.pnl_dollar, 3)}",
            f"⌛ Duration = {pnl_report.duration}",
        ]
        msg = "\n\n".join(msg_list)
        return msg

    def sl_trailed(self, position: Position) -> str:
        trail_type_msg = (
            "📝 Risk Free"
            if position.stoploss.price == position.entry_price
            else "📝 Trailing Stop"
        )
        msg_list = [
            trail_type_msg,
            f"💲 New SL = {position.stoploss.price}",
        ]
        msg = "\n\n".join(msg_list)
        return msg

    def trigger_hit(self, position: Position, pnl_report: PnLReport) -> str:
        if position.steps[-1].triggered_timestamp:
            return self.position_closed(position, pnl_report)
        triggers_msg = []
        for i, trigger in enumerate(position.steps):
            name = (
                "TakeProfit"
                if isinstance(trigger.event, TakeProfitHit)
                else trigger.event.name
            )
            if trigger.triggered_timestamp:
                msg = f"🎯 {i + 1}-{name} {trigger.price}"
                if trigger.volume:
                    msg += f"|{trigger.volume}💰"
                triggers_msg.append(msg)
        triggers_msg[-1] = triggers_msg[-1].replace("🎯", "✅")
        msg_list = [
            *self.identifier(position),
            *triggers_msg,
            f"💵 PNL = {round(pnl_report.pnl_dollar, 3)}",
            f"⌛ Duration = {pnl_report.duration}",
        ]
        msg = "\n\n".join(msg_list)
        return msg

    def new_signal(self, signal: Signal) -> str:
        msg_list = [
            f"🏷️ {signal.source}",
            f"📊 {signal.chart}",
            "🟢 Bullish" if signal.side is MarketSide.BULLISH else "🔴 Bearish",
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
        save_path: str = "",
    ):
        self.name = name
        # longer timeouts than the library's 5s: a slow route to telegram
        # (connect) or a big chart image (write) otherwise times out
        self.bot = Bot(
            bot_token,
            request=HTTPXRequest(
                connect_timeout=20,
                read_timeout=30,
                write_timeout=30,
                media_write_timeout=60,
                pool_timeout=30,
            ),
        )
        self.channel = channel
        self.enable = True
        self.msg_formater = msg_formater if msg_formater else TelegramMsgFormater()
        self.save_path = save_path

    # attempts of one send when telegram can't be reached / times out
    SEND_ATTEMPTS = 4

    async def send_msg(
        self,
        msg,
        img_path: str | None = None,
        reply_id: None | int = None,
        channel_id: Any = None,
        file_path: str | None = None,
    ):
        """
        Returns the sent message id. A network failure or timeout is retried
        (pause 3s, 6s, 12s) and a flood limit waited out, before giving up by
        raising (images/documents) - the text-only send keeps logging instead.
        """
        if not self.enable:
            return False
        channel_id = channel_id if channel_id else self.channel

        reply_to = reply_id

        async def send():
            if img_path:
                with open(img_path, "rb") as img:  # reopened on every attempt
                    return await self.bot.send_photo(
                        chat_id=channel_id, photo=img, caption=msg, reply_to_message_id=reply_to
                    )
            if file_path:
                with open(file_path, "rb") as file:
                    return await self.bot.send_document(
                        chat_id=channel_id,
                        document=file,
                        caption=msg,
                        reply_to_message_id=reply_to,
                    )
            return await self.bot.send_message(
                chat_id=channel_id, text=msg, reply_to_message_id=reply_to
            )

        res = None
        delay = 3.0
        for attempt in range(1, self.SEND_ATTEMPTS + 1):
            try:
                res = await send()
                break
            except RetryAfter as error:
                wait = error.retry_after
                wait = wait.total_seconds() if hasattr(wait, "total_seconds") else float(wait)
                logger.warning(f"telegram flood limit, waiting {wait:.0f}s")
                await asyncio.sleep(wait + 1)
            except BadRequest as error:  # a NetworkError subclass, but never temporary
                if reply_to is not None and "repl" in str(error).lower():
                    logger.warning(f"reply target {reply_to} rejected ({error}) - sending without the reply")
                    reply_to = None
                    continue
                if img_path or file_path:
                    raise
                logger.error(f"Error occurred while sending {msg=}: {error}")
                break
            except (TimedOut, NetworkError) as error:  # TimedOut is a NetworkError too
                if attempt == self.SEND_ATTEMPTS:
                    if img_path or file_path:
                        raise
                    logger.error(f"Error occurred while sending {msg=}: {error}")
                    break
                logger.warning(f"telegram send failed (attempt {attempt}): {error!r} - retrying in {delay:.0f}s")
                await asyncio.sleep(delay)
                delay *= 2
            except Exception as error:
                if img_path or file_path:
                    raise
                logger.error(f"Error occurred while sending {msg=}: {error}")
                break

        logger.debug(f"telegram response: {res}")
        return res.message_id if res else None
