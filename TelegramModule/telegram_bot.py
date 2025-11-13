from telegram import Bot
from datetime import datetime
import logging

logger = logging.getLogger("Telegram")


class TelegramBot:
    def __init__(self, bot_token, public_channel_id, report_channel_id=None) -> None:
        self.bot = Bot(bot_token)
        self.public_channel_id = public_channel_id
        self.report_channel_id = report_channel_id
        logger.info("Telegram Bot Initialized")

    async def send_message_to_channel(self, msg):
        await self.bot.send_message(chat_id=self.public_channel_id, text=msg)
        logger.debug("Msg Sended to Channel")

    async def send_photo_to_channel(self, photo_path, caption=None):
        with open(photo_path, "rb") as photo:
            await self.bot.send_photo(
                chat_id=self.public_channel_id, photo=photo, caption=caption
            )

        logger.debug("IMG Sended")

    async def send_report(self, report: str, add_time=False):
        if not self.report_channel_id:
            logger.warning("No Report Channel Defined")
            return
        if add_time:
            report = f"{datetime.now()}\n" + report
        await self.bot.send_message(chat_id=self.report_channel_id, text=report)
        logger.debug("Report Channel")

    async def get_chat_info(self, link):
        info = await self.bot.get_chat(link)
        logger.info(f"{info=}| {info.id=}")
        return info
