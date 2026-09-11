from typing import Any
from telegram import Bot
import logging

from TradingModule.reporter import Reporter

logger = logging.getLogger("TelegramReporter")


class TelegramReporter(Reporter):
    def __init__(self, name:str, signal_channel, report_channel, bot_token):
            self.name = name
            self.bot = Bot(bot_token)
            self.signal_channel = signal_channel
            self.report_channel = report_channel
            self._reporting = True

    async def send_msg(
        self, msg, img_path: str | None = None, reply_id: None | int = None, channel_id: Any = None, file_path: str | None = None, 
    ):
        if not self._reporting:
            return False
        channel_id = channel_id if channel_id else self.signal_channel
        res = None
        if img_path:
            img = open(img_path, "rb")
            res = await self.bot.send_photo(
                chat_id=channel_id, photo=img, caption=msg, reply_to_message_id=reply_id
            )
            img.close()
            
        elif file_path:
            file = open(file_path, "rb")
            res = await self.bot.send_document(chat_id=channel_id,document=file,caption=msg,reply_to_message_id=reply_id)
            file.close()
           
        else:
            try:
                res = await self.bot.send_message(
                    chat_id=channel_id, text=msg, reply_to_message_id=reply_id
                )
            except Exception as e:
                logger.error(f"Error occurred while sending {msg=}: {e}")


        logger.debug(f"telegram response: {res}")
        return res
