from LocalBackTester.Database.create_db import create_db
from Bots.DivergenceStrategy.diver_backtester import TwoChartDiverBacktester
from Settings.custom_logger import build_logger, LoggerConfig
from Settings.config import settings
import asyncio

build_logger(LoggerConfig(name="root", log_file_name="Develop & Test"))


if __name__ == "__main__":
    settings.METATRADER_TERMINAL_PATH = ""
    from LocalBackTester.methods import *  # noqa: F403
    from LocalBackTester.Database.BacktesConfigs.two_chart_diver_configs import *  # noqa: F403
    from LocalBackTester.StatisticalMethods import *  # noqa: F403

    the_config = diver_forex_xau_1m_5000_test

    create_db()
    import cProfile
    import pstats

    profiler = cProfile.Profile()
    profiler.enable()

    # plot_csv_kline(the_config.chart) # type: ignore

    asyncio.run(diver_signal_local_backtest(the_config, show_plot=False))

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

    diver_backtester = TwoChartDiverBacktester(
        the_config, statistical_indicators, show_chartdata=True
    )
    asyncio.run(
        diver_backtester.positions_backtest(use_database=False, show_plots=False)
    )

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumtime")
    stats.print_stats(30)
