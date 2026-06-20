from LocalBackTester.Database.create_db import create_db
from LocalBackTester.diver_backtester import DiverBacktester
from custom_logger import CustomLogger
from config import settings
import asyncio
import logging


CustomLogger(True, consol_log_level=logging.DEBUG)

if __name__ == "__main__":
    settings.METATRADER_TERMINAL_PATH = ""
    from LocalBackTester.methods import *  # noqa: F403
    from LocalBackTester.local_backtest_configs import *  # noqa: F403
    from LocalBackTester.StatisticalMethods import *  # noqa: F403

    the_config = diver_avaxbtc_5m_test

    create_db()
    import cProfile
    import pstats

    profiler = cProfile.Profile()
    profiler.enable()

    # plot_csv_kline(the_config.chart) # type: ignore

    # asyncio.run(diver_signal_local_backtest(the_config, show_plot=True))

    statistical_indicators = [
        WeekdayPnLHistogram(),
        HourlyPnLHistogram(),
        SessionPnLHistogram(),
        PipPnlDistribution(
            candles_range=200,
        ),
        PipAfterSLDistribution(candles_range=200, tolerance_pip=30),
        RiskAnalysis(),
    ]

    diver_backtester = DiverBacktester(
        the_config, statistical_indicators, show_chartdata=True
    )
    asyncio.run(
        diver_backtester.positions_backtest(use_database=False, show_plots=False)
    )

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumtime")
    stats.print_stats(30)
