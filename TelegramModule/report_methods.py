from telegram import Bot
from config import settings
from datetime import datetime
import logging

logger = logging.getLogger("Telegram")

bot = Bot(settings.TELEGRAM_BOT_TOKEN)


async def send_message_to_channel(msg):
    await bot.send_message(chat_id=settings.TELEGRAM_CHANNEL_ID, text=msg)
    logger.debug("Msg Sended to Channel")


async def send_photo_to_channel(photo_path, caption=None):
    with open(photo_path, "rb") as photo:
        await bot.send_photo(
            chat_id=settings.TELEGRAM_CHANNEL_ID, photo=photo, caption=caption
        )

    logger.debug("IMG Sended")


async def send_report(report: str):
    await bot.send_message(
        chat_id=settings.TELEGRAM_REPORT_CHANNEL, text=f"{datetime.now()}\n{report}"
    )
    logger.debug("Report Channel")


async def get_chat_info(link):
    info = await bot.get_chat(link)
    logger.info(f"{info=}| {info.id=}")
    return info
