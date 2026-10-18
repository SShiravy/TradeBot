from BackTest.models import CsvChart
from Database import store_signals, store_trader_bot, backtest_db_engine
from Settings import TimeHandler
from TraderBot.Commands.db_commands import DatabaseCommand
from TraderBot import TraderBot
from TraderBot.models import Command, Event
from TraderBot.PositionHandlers.Statistics import StatisticsSuite
from TraderBot.PositionHandlers.Statistics.base import DEFAULT_PLOTS_DIR
from BackTest import BacktestAgent, BacktestReporter
from pathlib import Path
import cProfile
import pstats
import logging


logger = logging.getLogger("Backtest")


class SignalBacktest:
    def __init__(
        self, bot: TraderBot, backtest_agent: BacktestAgent, store_in_db: bool = True
    ) -> None:
        if not isinstance(bot.chart, CsvChart):
            raise ValueError(f"bot's chart is not a csv chart: {bot.chart}")

        self.store_in_db = store_in_db

        chartdata = backtest_agent.first_n_candle(
            bot.chart, n_candle=bot.n_candle_check
        )
        start_time = chartdata.timestamps[-1]
        TimeHandler.set_time(int(start_time))

        self.backtest_agent = backtest_agent

        backtest_reporter = BacktestReporter()
        backtest_reporter.save_path += bot.identifier + "/"
        self.reporter = backtest_reporter

        bot.trades_manager.reporter = backtest_reporter
        bot.agent = backtest_agent
        bot.trades_manager.exchange_agent = backtest_agent
        bot.consider_position = False
        self.bot = bot
        DatabaseCommand.db_engine = None
        Event.consider_db_record = False

    def conclusion(self):
        if self.store_in_db:
            store_trader_bot(self.bot, db_engine=backtest_db_engine)
            store_signals(
                self.reporter.all_signals, self.bot, db_engine=backtest_db_engine
            )

        logger.info(Command.close_records())

    async def step(self):
        delay = await self.bot.task()
        if delay <= 0:
            delay = 5
        TimeHandler.advance(delay)
        await Command.execute_pending_commands()

    async def run(self):
        end_timestamp = self.backtest_agent.last_timestamp(self.bot.chart)
        profiler = cProfile.Profile()
        profiler.enable()

        while TimeHandler.now() < end_timestamp:
            await self.step()

        profiler.disable()
        stats = pstats.Stats(profiler)
        stats.sort_stats("cumtime")
        stats.print_stats(30)

        self.conclusion()


class PositionBacktest(SignalBacktest):
    """
    SignalBacktest that trades: the bot's positions are filled at the open of
    the running candle and managed on the csv candles (TradesManager's ochl
    check, no spread). At the end the closed positions are analysed by
    `statistics` and its plots are saved under `plots_dir`.
    """

    def __init__(
        self,
        bot: TraderBot,
        backtest_agent: BacktestAgent,
        statistics: StatisticsSuite | None = None,
        plots_dir: str | Path | None = DEFAULT_PLOTS_DIR,
        store_in_db: bool = True,
    ) -> None:
        super().__init__(bot, backtest_agent, store_in_db)
        # precision, pip_factor and contract_size, the pnl depends on them
        bot.post_init()
        bot.consider_position = True
        bot.trades_manager.agent_check = False
        self.statistics = statistics or StatisticsSuite.standard()
        self.plots_dir = plots_dir
        self.plot_paths: list[Path] = []

    async def step(self):
        delay = await self.bot.task()
        # open the new positions at the price their triggers were set from
        await Command.execute_pending_commands()
        if delay <= 0:
            delay = 5
        TimeHandler.advance(delay)
        self.bot.trades_manager.manage_positions()
        await Command.execute_pending_commands()

    def conclusion(self):
        super().conclusion()
        manager = self.bot.trades_manager
        self.statistics.analyze(manager.closed_positions + manager.current_positions)
        logger.info(f"\n{self.statistics}")
        self.plot_paths = self.statistics.plot(
            label=self.bot.identifier, show=False, save_dir=self.plots_dir
        )
        logger.info(f"{len(self.plot_paths)} statistics plots saved")
