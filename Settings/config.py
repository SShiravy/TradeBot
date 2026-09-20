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
    TELEGRAM_CRYPTO_CHANNEL_ID: str
    TELEGRAM_TEST_BOT: str
    TELEGRAM_TEST_CHANNEL: str

    # Bitunix Exchange
    BITUNIX_API_KEY: str
    BITUNIX_API_SECRET_KEY: str

    # Mt5
    METATRADER_TERMINAL_PATH: str
    SECOND_METATRADER_TERMINAL_PATH: str
    BROKER_UTC_SHIFT: int

    # LocalBacktest DB
    LOCAL_BACKTEST_DB_NAME: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()  # type: ignore
