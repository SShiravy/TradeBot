from Settings.custom_logger import build_logger, LoggerConfig
from Settings import settings
import logging
import asyncio

logger = build_logger(
    LoggerConfig(
        name="root",
        log_file_name="SR_CHoCH",
        file_level=logging.DEBUG,
        telegram_channel=settings.TELEGRAM_TEST_CHANNEL,
        telegram_token=settings.TELEGRAM_TEST_BOT,
    )
)

def initialize_DBs():
    from Database import engine,backtest_engine,create_db
    create_db(backtest_engine)
    create_db(engine)


if __name__ == "__main__":
    import cProfile
    import pstats

    profiler = cProfile.Profile()
    profiler.enable()

    # --------------------------------------

    initialize_DBs()
    

    # --------------------------------------

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumtime")
    stats.print_stats(30)
