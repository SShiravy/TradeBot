from ChartModule.plot import PlotChart
from TradingModule import Position, OrderSide
from config import settings
from datetime import datetime, timezone
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
            cls.msg_id_dict = {}
        return cls._instance

    async def send_msg(
        self, channel_id, msg, img_path: str | None = None, reply_id: None | int = None
    ):
        if img_path:
            img = open(img_path, "rb")
            res = await self.bot.send_photo(
                chat_id=channel_id, photo=img, caption=msg, reply_to_message_id=reply_id
            )
            img.close()
        else:
            res = await self.bot.send_message(
                chat_id=channel_id, text=msg, reply_to_message_id=reply_id
            )
        return res

    async def log_report(self, msg):
        await self.send_msg(self._log_channel, msg)

    async def new_position(self, position: Position, plot: PlotChart):
        msg_list = [
            position.source,
            f"📊 {position.chart}",
            "🟢 LONG" if position.side is OrderSide.BUY else "🔴 SHORT",
            f"📣 Entry = {position.entry_price}",
            f"🎯 TP =  {position.takeprofit}",
            f"⛔️ SL = {position.stoploss}",
            f"💰 Volume: {position.volume}",
        ]

        msg = "\n\n".join(msg_list)
        if position.leverage not in [1, 0]:
            msg += f"\n\n⚡Leverage: {position.leverage}"

        position.draw(plot)
        img_path = plot.save_image(position.source + str(position.chart))

        res = await self.send_msg(self._public_channel, msg, img_path)
        self.msg_id_dict[position.id] = res.message_id

    async def position_closed(self, position: Position, filled_price=None):
        close_time = position.closed if position.closed else datetime.now(timezone.utc)
        duration = close_time.replace(
            microsecond=0, second=0
        ) - position.open_time.replace(microsecond=0, second=0)

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
            f"💵 PNL = {round(position.pnl, 5)}",
            f"⌛ Duration = {duration}",
        ]
        msg = "\n\n".join(msg_list)
        await self.send_msg(
            self._public_channel, msg, reply_id=self.msg_id_dict.get(position.id)
        )
        if self.msg_id_dict.get(position.id):
            self.msg_id_dict.pop(position.id)

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

        await self.send_msg(
            self._public_channel, msg, reply_id=self.msg_id_dict.get(position.id)
        )

    async def public_report(self, msg: str):
        await self.send_msg(self._public_channel, msg)
