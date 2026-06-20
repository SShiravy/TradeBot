import logging
from logging.handlers import RotatingFileHandler
import colorlog
import asyncio
from telegram import Bot


class TelegramLogHandler(logging.Handler):
    def __init__(self, bot_token: str, chat_id: int, level=logging.WARNING):
        super().__init__(level)
        self.chat_id = chat_id
        self.bot = Bot(token=bot_token)

    def emit(self, record: logging.LogRecord):
        try:
            log_entry = self.format(record)
            try:
                asyncio.get_event_loop().create_task(self._send(log_entry))
            except Exception as e:
                logging.debug(e)

        except Exception:
            self.handleError(record)

    async def _send(self, text: str):
        try:
            async with self.bot:
                await self.bot.send_message(self.chat_id, text)
        except Exception as e:
            logging.debug(e)


class CustomLogger:
    def __new__(
        cls,
        consol_log: bool = True,
        consol_log_level=logging.INFO,
        log_file: bool = False,
        file_log_level=logging.DEBUG,
        file_log_name: str = "app",
        telegram_report_channel=None,
        telegram_bot_token=None,
        telegram_report_log_level=logging.WARNING,
    ):
        if not hasattr(cls, "_instance"):
            cls._instance = logging.getLogger()
            cls._instance.setLevel(logging.DEBUG)
            if consol_log:
                cls._instance.addHandler(cls.__consol_handler(consol_log_level))
            if log_file:
                cls._instance.addHandler(
                    cls.__file_handler(file_log_level, file_log_name)
                )
            if telegram_report_channel and telegram_bot_token:
                cls._instance.addHandler(
                    cls.__telegram_reporter(
                        telegram_report_log_level,
                        telegram_bot_token,
                        telegram_report_channel,
                    )
                )

        return cls._instance

    @classmethod
    def __consol_handler(cls, log_level):
        formatter = colorlog.ColoredFormatter(
            "{log_color}#{asctime}# {name}:\n --*{levelname}*->|[{message}]|\n\n",
            style="{",
            datefmt='%H:%M:%S"',
            log_colors={
                "DEBUG": "white",
                "INFO": "cyan",
                "WARNING": "yellow",
                "ERROR": "bold_red",
                "CRITICAL": "bold_purple",
            },
        )
        consol_handler = logging.StreamHandler()
        consol_handler.setFormatter(formatter)
        consol_handler.setLevel(log_level)
        return consol_handler

    @classmethod
    def __file_handler(cls, log_level, file_log_name: str):
        file_formatter = logging.Formatter(
            "#{asctime}#{name}# --*{levelname}*->|[{message}]|",
            style="{",
            datefmt='%D;%H:%M:%S"',
        )
        file_handler = RotatingFileHandler(
            filename=f"{file_log_name}.log",
            mode="a",
            encoding="utf-8",
            maxBytes=int(1e6),
            backupCount=1,
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(log_level)
        return file_handler

    @classmethod
    def __telegram_reporter(cls, log_level, bot_token, channel_id):
        tg_handler = TelegramLogHandler(
            bot_token=bot_token, chat_id=channel_id, level=log_level
        )
        tg_handler.setFormatter(
            logging.Formatter(
                "{asctime}\n{levelname}\n🚫🚫🚫\n{message}\n🚫🚫🚫",
                style="{",
                datefmt='%D;%H:%M:%S"',
            )
        )
        return tg_handler


logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("matplotlib.category").setLevel(logging.WARNING)
logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)
logging.getLogger("matplotlib.pyplot").setLevel(logging.WARNING)


if __name__ == "__main__":
    CustomLogger().debug("mio")
    CustomLogger().info("mio")
    CustomLogger().warning("mio")
    CustomLogger().error("mio")
    CustomLogger().critical("mio")
    CustomLogger().exception("mio")

    import logging

    logging.warning("1")
    logging.info("2")
    logging.debug("3")
    logging.error("4")
    logging.critical("5")

    other_logger = logging.getLogger("test_not_root")
    other_logger.error("not roooooottt")
