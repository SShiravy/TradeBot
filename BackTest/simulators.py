from BackTest.models import CsvChart
from Database import store_signals, store_trader_bot, backtest_db_engine
from Settings import TimeHandler
from TraderBot.Commands.db_commands import DatabaseCommand
from TraderBot import TraderBot
from TraderBot.models import Command, Event
from BackTest import BacktestAgent, BacktestReporter
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

    async def run(self):
        end_timestamp = self.backtest_agent.last_timestamp(self.bot.chart)
        profiler = cProfile.Profile()
        profiler.enable()

        while TimeHandler.now() < end_timestamp:
            delay = await self.bot.task()
            if delay <= 0:
                delay = 5
            TimeHandler.advance(delay)
            await Command.execute_pending_commands()

        profiler.disable()
        stats = pstats.Stats(profiler)
        stats.sort_stats("cumtime")
        stats.print_stats(30)

        self.conclusion()
