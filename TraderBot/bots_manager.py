import cProfile
import io
import pstats
import tracemalloc
import asyncio
import logging
from datetime import timedelta
from TraderBot.PositionHandlers.trades_pnl import PnLReportGenerator
from TraderBot.models import Command, ReporterBot
from Settings.timing import TimeHandler
from TraderBot.trader_bot import TraderBot


class BotsManager:
    def __init__(
        self,
        name: str,
        reporter: ReporterBot,
        bots: list[TraderBot],
        manage_interval: float = 2.0,
        heartbeat_interval: float = 3600.0,
        enable_profiling: bool = True,
    ) -> None:
        self.name = name
        self.reporter = reporter
        self.bots = bots
        self.manage_interval = manage_interval
        self.heartbeat_interval = heartbeat_interval
        self._start_time = TimeHandler.now()
        self._stop_event = asyncio.Event()

        self._last_snapshot: tracemalloc.Snapshot | None = None
        self.enable_profiling = enable_profiling
        self._profilers: dict[str, cProfile.Profile] = {}

    def _memory_report(self) -> str:
        snapshot = tracemalloc.take_snapshot()
        lines = ["Memory (top 20 by allocated size):"]

        if self._last_snapshot is not None:
            top_stats = snapshot.compare_to(self._last_snapshot, "lineno")
        else:
            top_stats = snapshot.statistics("lineno")

        for stat in top_stats[:20]:
            lines.append(str(stat))

        self._last_snapshot = snapshot
        return "\n".join(lines)

    async def _run_bot_task(self, bot: TraderBot):
        """Runs bot.task(), profiled if enabled. Executed inside the worker thread."""
        if not self.enable_profiling:
            return await bot.task()
        profiler = self._profilers[bot.identifier]
        profiler.enable()
        try:
            result = await bot.task()
            return result
        finally:
            profiler.disable()

    def _profiling_report(self, bot: TraderBot) -> str | None:
        profiler = self._profilers.get(bot.identifier)
        if profiler is None:
            return None
        stream = io.StringIO()
        pstats.Stats(profiler, stream=stream).sort_stats("cumtime").print_stats(30)
        return stream.getvalue()

    async def _trade_task(self, bot: TraderBot) -> None:
        if self.enable_profiling:
            self._profilers[bot.identifier] = cProfile.Profile()
        error_count = 0
        while not self._stop_event.is_set():
            try:
                delay = await self._run_bot_task(bot)
                logging.info(
                    f"{bot.chart.timeframe} checked on {bot.chart}. sleeping {delay}s"
                )
                await asyncio.sleep(max(1, delay))
                error_count = 0
            except Exception as e:
                error_count += 1
                logging.exception(f"{error_count} failures for {bot.identifier}: {e}")
                if error_count == 3:
                    await self.reporter.send_msg(f"3x error: {e}\non {bot.identifier}")
                await asyncio.sleep(bot.chart.timeframe.minutes * 60 / 2)
                if error_count > 6:
                    await self.reporter.send_msg(
                        f"Removing {bot.identifier} after 6 failures: {e}"
                    )
                    return

    async def _manage_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                for bot in self.bots:
                    bot.trades_manager.manage_positions()
                await Command.execute_pending_commands()
            except Exception as e:
                logging.exception(f"Manage failed: {e}")
            await asyncio.sleep(self.manage_interval)

    async def _heartbeat_loop(self) -> None:
        while not self._stop_event.is_set():
            await asyncio.sleep(self.heartbeat_interval)
            current, peak = tracemalloc.get_traced_memory()
            elapsed = TimeHandler.elapsed_since(self._start_time)
            await self.reporter.send_msg(
                f"{self.name}\n👋🤖 Lifespan: {elapsed}\n"
                f"Memory: {current / 1024 / 1024:.2f} MB (peak {peak / 1024 / 1024:.2f} MB)"
            )

    def _daily_report_sleeptime(self):
        now = TimeHandler.to_datetime(TimeHandler.now())
        next_report = now.replace(hour=20, minute=58)
        next_report = (
            next_report if next_report > now else next_report + timedelta(days=1)
        )
        return next_report - now

    async def _daily_report_loop(self) -> None:
        while not self._stop_event.is_set():
            sleep_time = self._daily_report_sleeptime()
            logging.info(f"Next daily report in {sleep_time}s")
            await asyncio.sleep(max(1, sleep_time.total_seconds()))

            await self.reporter.send_msg(f"{self.name}\n{Command.close_records()}")
            await self.reporter.send_msg(self._memory_report())

            if self.enable_profiling:
                for bot in self.bots:
                    report = self._profiling_report(bot)
                    if report:
                        await self.reporter.send_msg(
                            f"Profiling {bot.identifier}:\n{report}"
                        )

            per_bot_reports = []
            for bot in self.bots:
                pnl = PnLReportGenerator.overall_report(
                    bot.trades_manager.closed_positions
                )
                per_bot_reports.append(pnl)
                await self.reporter.send_msg(f"{bot.identifier}:\n{pnl}")

            await self.reporter.send_msg(
                f"Overall of {self.name}:\n{sum(per_bot_reports)}"
            )

    async def start(self) -> None:
        tracemalloc.start()
        await self.reporter.send_msg(
            f"--{self.name}--\n⚡ Start at {TimeHandler.format(self._start_time)} UTC ⚡"
        )
        async with asyncio.TaskGroup() as tg:
            for bot in self.bots:
                bot.post_init()
                tg.create_task(self._trade_task(bot))
            tg.create_task(self._manage_loop())
            tg.create_task(self._heartbeat_loop())
            tg.create_task(self._daily_report_loop())

    def stop(self) -> None:
        self._stop_event.set()
