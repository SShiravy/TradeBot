import io
import cProfile
import pstats
import shutil
import sqlite3
import tempfile
import tracemalloc
import asyncio
import logging
import random
import Database as db
from datetime import timedelta
from pathlib import Path
from TraderBot.Commands.db_commands import DatabaseCommand
from TraderBot.events import Event
from TraderBot.PositionHandlers.trades_pnl import PnLReportGenerator
from TraderBot.models import Command, ReporterBot
from Settings.timing import TimeHandler
from TraderBot.trader_bot import TraderBot
from Settings import settings


# telegram refuses a document over 50 MB, the rest of the report still goes out
MAX_UPLOAD_BYTES = 45 * 1024 * 1024


class BotsManager:
    def __init__(
        self,
        name: str,
        reporter: ReporterBot,
        bots: list[TraderBot],
        manage_interval: float = 2.0,
        heartbeat_interval: float = 3600.0,
        enable_profiling: bool = True,
        database_name: "str|None" = settings.LIVE_DB_NAME,
    ) -> None:
        self.name = name
        self.reporter = reporter
        self.bots = bots
        self.manage_interval = manage_interval
        self.heartbeat_interval = heartbeat_interval

        self.report_seconds_shift = random.randrange(0, 59)
        self._start_time = TimeHandler.now()
        self._stop_event = asyncio.Event()

        self._last_snapshot: tracemalloc.Snapshot | None = None
        self.enable_profiling = enable_profiling
        self._profilers: dict[str, cProfile.Profile] = {}

        if database_name:
            engine = db.give_engine(database_name)
            db.create_db(engine)
            Event.consider_db_record = True
            DatabaseCommand.db_engine = engine
            self.db_engin = engine
        else:
            Event.consider_db_record = False
            self.db_engin = None

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
            elapsed = timedelta(seconds=TimeHandler.elapsed_since(self._start_time))
            await self.reporter.send_msg(
                f"{self.name}\n👋🤖 Lifespan: {elapsed}\n"
                f"Memory: {current / 1024 / 1024:.2f} MB (peak {peak / 1024 / 1024:.2f} MB)"
            )

    def _daily_report_sleeptime(self):
        now = TimeHandler.to_datetime(TimeHandler.now())
        # next_report = now.replace(hour=20, minute=self.report_seconds_shift)
        next_report = now.replace(hour=23, minute=40)
        next_report = (
            next_report if next_report > now else next_report + timedelta(days=1)
        )
        return next_report - now

    @staticmethod
    def _log_files() -> list[Path]:
        """Every file the root logger writes to, its rotated backups included."""
        files: list[Path] = []
        for handler in logging.getLogger().handlers:
            if not isinstance(handler, logging.FileHandler):
                continue
            base = Path(handler.baseFilename)
            files.append(base)
            for index in range(1, getattr(handler, "backupCount", 0) + 1):
                files.append(base.with_name(f"{base.name}.{index}"))
        return [file for file in files if file.exists()]

    def _database_snapshot(self) -> "tuple[Path, str] | None":
        """
        A consistent copy of the db the bots record on, safe to upload while
        they keep writing to it, with the name of the db it was copied from.
        None when this manager holds no sqlite db.
        """
        if self.db_engin is None:
            return None

        url = self.db_engin.url
        if not url.get_backend_name().startswith("sqlite") or not url.database:
            logging.warning(f"no sqlite database to send: {url}")
            return None

        database = Path(url.database)
        # its own directory, so the upload carries the real db name
        snapshot = Path(tempfile.mkdtemp(prefix=f"{self.name}_")) / database.name
        source = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
        target = sqlite3.connect(snapshot)
        try:
            source.backup(target)
        finally:
            target.close()
            source.close()
        return snapshot, database.name

    async def _send_file(self, path: Path, caption: str) -> None:
        """Upload one file. A failure here never breaks the report."""
        size = path.stat().st_size
        if size > MAX_UPLOAD_BYTES:
            logging.warning(f"{path.name} is {size / 1024 / 1024:.1f} MB, not sent")
            return
        try:
            await self.reporter.send_msg(caption, file_path=str(path))
        except Exception as e:
            logging.exception(f"Failed to send {path.name}: {e}")

    async def _send_records(self) -> None:
        """Send the log files and the database the bots record on."""
        for log_file in self._log_files():
            await self._send_file(log_file, f"🗒 {self.name} log: {log_file.name}")

        snapshot = None
        try:
            copied = self._database_snapshot()
            if copied is None:
                return
            snapshot, database_name = copied
            await self._send_file(snapshot, f"🗄 {self.name} db: {database_name}")
        except Exception as e:
            logging.exception(f"Failed to send the database: {e}")
        finally:
            if snapshot:
                shutil.rmtree(snapshot.parent, ignore_errors=True)

    async def _daily_report_loop(self) -> None:
        while not self._stop_event.is_set():
            sleep_time = self._daily_report_sleeptime()
            logging.info(f"Next daily report in {sleep_time}")
            await asyncio.sleep(max(1, sleep_time.total_seconds()))

            await self.reporter.send_msg(f"📝 {self.name}\n{Command.close_records()}")
            await self.reporter.send_msg(f"🗒️ {self._memory_report()}")

            if self.enable_profiling:
                for bot in self.bots:
                    report = self._profiling_report(bot)
                    if report:
                        await self.reporter.send_msg(
                            f"🧾 Profiling {bot.identifier}:\n{report}"
                        )
                        await asyncio.sleep(2)

            per_bot_reports = []
            for bot in self.bots:
                if not bot.trades_manager.closed_positions:
                    continue
                pnl = PnLReportGenerator.overall_report(
                    bot.trades_manager.closed_positions
                )
                per_bot_reports.append(pnl)
                await self.reporter.send_msg(f"📈 {bot.identifier}:\n{pnl}")

            await self.reporter.send_msg(
                f"Overall of {self.name}:\n{sum(per_bot_reports)}"
            )

            await self._send_records()

    async def start(self) -> None:
        tracemalloc.start()
        await self.reporter.send_msg(
            f"--{self.name}--\n⚡ Start at {TimeHandler.format(self._start_time)} UTC ⚡"
        )
        async with asyncio.TaskGroup() as tg:
            for bot in self.bots:
                bot.post_init()
                if self.db_engin:
                    db.store_trader_bot(bot, self.db_engin)
                tg.create_task(self._trade_task(bot))
            tg.create_task(self._manage_loop())
            tg.create_task(self._heartbeat_loop())
            tg.create_task(self._daily_report_loop())

    def stop(self) -> None:
        self._stop_event.set()
