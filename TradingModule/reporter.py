from TradingModule import Position, OrderSide
from config import settings
from datetime import datetime, timedelta, timezone
from telegram import Bot
import logging


logger = logging.getLogger("TelegramReporter")


class TelegramReporter:
    def __new__(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = object.__new__(cls)
            cls.bot = Bot(settings.TELEGRAM_BOT_TOKEN)
            cls._public_channel = settings.TELEGRAM_CHANNEL_ID
            cls._log_channel = settings.TELEGRAM_REPORT_CHANNEL
            cls._reporting = True
        return cls._instance

    def disable_reporting(self):
        self._reporting = False
        logger.info("⚠️ Telegram Reporting Disabled")

    def enable_reporting(self):
        self._reporting = True
        logger.info("👍 Telegram Reporting Enabled")

    async def send_msg(
        self, channel_id, msg, img_path: str | None = None, reply_id: None | int = None
    ):
        if not self._reporting:
            return False

        if img_path:
            img = open(img_path, "rb")
            res = await self.bot.send_photo(
                chat_id=channel_id, photo=img, caption=msg, reply_to_message_id=reply_id
            )
            img.close()
            logger.debug(
                f"response from telegram for new position: {res} , id: {res.message_id if res else None}"
            )
            return res
        else:
            try:
                res = await self.bot.send_message(
                    chat_id=channel_id, text=msg, reply_to_message_id=reply_id
                )
                logger.debug(
                    f"response from telegram for new position: {res} , id: {res.message_id if res else None}"
                )
                return res
            except Exception as e:
                logger.error(f"Error occurred while sending {msg=}: {e}")

    async def log_report(self, msg):
        if not self._reporting:
            return True

        await self.send_msg(self._log_channel, msg)

    async def new_position(self, position: Position):
        msg_list = [
            position.source,
            f"📊 {position.chart}",
            "🟢 LONG" if position.side is OrderSide.BUY else "🔴 SHORT",
            f"📣 Entry = {position.entry_price}",
        ]

        if len(position.steps) > 2:
            i = 1
            for trigger in position.steps[1:]:
                msg_list.append(f"🎯 TP {i} =  {trigger.price} with {trigger.volume}💰")
                i += 1
        else:
            msg_list.append(f"🎯 TP =  {position.takeprofit}")

        msg_list.append(f"⛔️ SL = {position.stoploss}")
        msg_list.append(f"💰 Volume: {position.volume}")

        if position.leverage not in [1, 0]:
            msg_list.append(f"⚡Leverage: {position.leverage}")

        if position.spread:
            msg_list.append(f"🧾 Spread = {position.spread}")

        img_path = None
        if position.plot:
            position.draw()
            img_path = position.plot.save_image(position.source + str(position.chart))

        msg = "\n\n".join(msg_list)
        res = await self.send_msg(self._public_channel, msg, img_path)
        position.msg_id = res.message_id if res else 0

    async def position_closed(self, position: Position, filled_price=None):
        end_timestamp = datetime.now(timezone.utc).timestamp()
        duration = timedelta(
            seconds=int(end_timestamp) - int(position.initial_timestamp)
        )
        logger.debug(
            f"Duration in reporter position close: {duration=} | {end_timestamp=} | {position.initial_timestamp=}"
        )

        close_type_msg = "⭕ Flat Close"
        close_price = filled_price if filled_price else position.entry_price
        if position.pnl > 0:
            close_type_msg = "✅ TP Triggered"
            close_price = position.takeprofit
        elif position.pnl < 0:
            close_type_msg = "⛔️ SL Triggered"
            close_price = position.stoploss

        msg_list = [
            close_type_msg,
            position.source,
            f"📊 {position.chart}",
            f"💲 Close Price = {close_price}",
            f"💵 PNL = {round(position.pnl, 2)}",
            f"⌛ Duration = {duration}",
        ]
        msg = "\n\n".join(msg_list)
        await self.send_msg(self._public_channel, msg, reply_id=position.msg_id)

    async def trailing_sl(self, position: Position):
        trail_type_msg = (
            "📝 Risk Free"
            if position.stoploss == position.entry_price
            else "📝 Trailing Stop"
        )
        msg_list = [
            trail_type_msg,
            position.source,
            f"📊 {position.chart}",
            f"💲 New SL = {position.stoploss}",
        ]
        msg = "\n\n".join(msg_list)

        await self.send_msg(self._public_channel, msg, reply_id=position.msg_id)

    async def public_report(self, msg: str):
        await self.send_msg(self._public_channel, msg)

    async def triggered_step(self, position: Position):
        if position.closed:
            trigger = position.steps[-1]
            triggered_id = len(position.steps) - 1
        else:
            trigger = position.previous_step
            triggered_id = position._current_step_index - 1
        end_timestamp = (
            trigger.triggered_time
            if trigger.triggered_time
            else datetime.now(tz=timezone.utc)
        ).timestamp()
        duration = timedelta(
            seconds=int(end_timestamp) - int(trigger.defined_time.timestamp())
        )
        logger.debug(
            f"Duration in reporter Trigger step: {duration=} | {end_timestamp=} | {trigger.defined_time.timestamp()=}"
        )

        msg_list = [
            f"✅ TP {triggered_id} Triggered",
            position.source,
            f"📊 {position.chart}",
            f"💲 Triggered Price = {trigger.price}",
            f"💰 Volume: {trigger.volume}",
            f"💵 PNL = {round(position.pnl, 2)}",
            f"⌛ Duration = {duration}",
        ]
        msg = "\n\n".join(msg_list)
        await self.send_msg(self._public_channel, msg, reply_id=position.msg_id)
