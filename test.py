from Settings.custom_logger import build_logger, LoggerConfig
import logging
import asyncio

logger = build_logger(
    LoggerConfig(
        name="root",
        log_file_name="Test",
        file_level=logging.DEBUG,
    )
)


def initialize_DBs():
    from Database import live_db_engine, backtest_db_engine, create_db

    create_db(backtest_db_engine)
    create_db(live_db_engine)


async def test_positions():
    from TraderBot.PositionHandlers import TradesManager
    from ChartModule import Signal, Chart, TimeFrame, MarketSide
    from TraderBot.models import Command, ReportCommandContext, TradeCommandContext
    from TraderBot.events import NewPosition
    from BackTest import BacktestReporter

    from TraderBot.PositionHandlers.PositionGenerators import ForexStepping
    from ExchangeAgents import MT5Agent
    from Settings import settings

    agent = MT5Agent(settings.METATRADER_TERMINAL_PATH)
    generator = ForexStepping(sl_pip=20)
    chart = Chart("ETHUSD", TimeFrame.one_minute)
    side = MarketSide.BULLISH

    manager = TradesManager(
        agent, generator, reporter=BacktestReporter(), agent_check=True
    )
    agent.prepare_chart(chart)
    logger.info(f"{chart.precision=}")
    chartdata = agent.get_chartdata(chart, 2)
    if not chartdata:
        raise ValueError("No Chartdata")
    candle = chartdata[-1]
    signal = Signal(chart, candle, side, "Test")

    pos = manager.generate_position(signal)
    if not pos:
        raise ValueError("No Position Generated")
    for step in pos.steps:
        logger.info(str(step))
    logger.info(pos.stoploss)
    NewPosition(
        trade_context=TradeCommandContext(pos, agent),
        report_context=ReportCommandContext(manager.reporter),
    ).occur()

    while True:
        logger.info(agent.get_current_tick(chart, pos.side))
        manager.manage_positions()
        await Command.execute_pending_commands()
        await asyncio.sleep(5)


if __name__ == "__main__":
    import cProfile
    import pstats

    profiler = cProfile.Profile()
    profiler.enable()

    # --------------------------------------

    # initialize_DBs()
    asyncio.run(test_positions())

    # --------------------------------------

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumtime")
    stats.print_stats(30)
