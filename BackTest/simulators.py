from BackTest.models import CsvChart
from Settings import TimeHandler
from TraderBot import TraderBot
from TraderBot.models import Command
from BackTest import BacktestAgent, BacktestReporter
import cProfile
import pstats


class SignalBacktest:
    def __init__(self, bot: TraderBot, backtest_agent: BacktestAgent) -> None:
        if not isinstance(bot.chart, CsvChart):
            raise ValueError(f"bot's chart is not a csv chart: {bot.chart}")

        chartdata = backtest_agent.first_n_candle(
            bot.chart, n_candle=bot.n_candle_check
        )
        start_time = chartdata.timestamps[-1]
        TimeHandler.set_time(int(start_time))

        self.backtest_agent = backtest_agent

        backtest_reporter = BacktestReporter()
        backtest_reporter.save_path += bot.identifier + "/"

        bot.trades_manager.reporter = backtest_reporter
        bot.agent = backtest_agent
        bot.trades_manager.exchange_agent = backtest_agent
        bot.consider_position = False
        self.bot = bot

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
