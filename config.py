from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    def __new__(cls):
        if not hasattr(cls, "__instance"):
            cls.__instance = object.__new__(cls)
        return cls.__instance

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHANNEL_ID: str
    TELEGRAM_REPORT_CHANNEL: int
    TELEGRAM_BACKTEST_REPORT_CHANNEL: str

    # Coinex Exchange
    COINEX_ACCESS_ID: str
    COINEX_SECRET_KEY: str

    # Mt5
    METATRADER_TERMINAL_PATH: str

    # LocalBacktest DB 
    LOCAL_BACKTEST_DB_NAME: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()  # type: ignore
