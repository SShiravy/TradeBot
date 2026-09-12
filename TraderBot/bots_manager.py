from TraderBot import commands, PositionsReport
from TraderBot.reporter import TelegramReporter
from datetime import datetime, timezone, timedelta
import tracemalloc
import asyncio
import logging


class BotsManager:
    def __new__(
        cls,
        name: str = "",
        configs: list[TraderBot] = [],
        report_time: dict = {"h": 23, "m": 50},
        commands_report: bool = True,
    ):
        if not hasattr(cls, "_instance"):
            cls._instance = object.__new__(cls)
            cls.name = name
            cls.configs = configs
            cls.report_time = report_time
            cls._start_time = datetime.now(tz=timezone.utc).replace(microsecond=0)
            cls._commands_report = commands_report
        return cls._instance

    async def manage(self):
        while True:
            try:
                for config in self.configs:
                    config.position_handler.manage_positions()
                await commands.Command.execute_pending_commands(
                    report=self._commands_report
                )
                await asyncio.sleep(2)
            except Exception as e:
                logging.exception(f"Manage Failed: {e}")
                await asyncio.sleep(10)

    async def trade_task(self, config: TraderBot):
        logging.info(f"Task with config:{str(config)} initilized")
        error_number = 0
        if not config.agent.prepare_chart(config.chart):
            logging.error(f"Failed to check chart for config: {config}")
            return
        while True:
            try:
                res = await config.task()
                if isinstance(res, timedelta):
                    sleep_time = res
                else:
                    sleep_time = res[0]
                logging.info(
                    f"{config.chart.timeframe} Checked on {config.chart}. sleep for {sleep_time}"
                )

                if sleep_time.total_seconds() < 0:
                    raise ValueError(f"Negative sleep time: {sleep_time}, 1m sleep")

                await asyncio.sleep(sleep_time.total_seconds())
                error_number = 0

            except Exception as e:
                error_number += 1
                logging.exception(f"{error_number} Times Task failed :{e}\n{config}")
                if error_number == 3:
                    await TelegramReporter().log_report(
                        f"3 Times Error:{e}\non {config}"
                    )
                # Delay for half candle
                await asyncio.sleep(
                    int(config.chart.timeframe.time_delta.total_seconds() / 2)
                )

                if error_number > 6:
                    await TelegramReporter().log_report(
                        f"Error:{e}\non {config}\nMore Than 6 Times\nTask removed"
                    )
                    break
                continue

    async def heartbeat(self):
        while True:
            await asyncio.sleep(3600)
            current, peak = tracemalloc.get_traced_memory()
            elapsed_time = str(
                datetime.now(tz=timezone.utc).replace(microsecond=0) - self._start_time
            )
            msg = [
                f"{self.name}",
                f"👋🤖\nLifespan⌛:\n{elapsed_time}",
                f"Memory📝:\n{current / 1024 / 1024:.2f} MB\npeak: {peak / 1024 / 1024:.2f} MB",
            ]
            await TelegramReporter().log_report("\n".join(msg))

    async def report(self):
        now = datetime.now(tz=timezone.utc)
        report_time = now.replace(
            hour=self.report_time["h"],
            minute=self.report_time["m"],
            second=0,
            microsecond=0,
        )
        if report_time < now:
            report_time += timedelta(days=1)
        sleep_time = report_time - now
        while True:
            logging.info(f"Next daily report in {sleep_time}")
            await asyncio.sleep(sleep_time.total_seconds())
            commands_report = commands.Command.close_records()
            await TelegramReporter().log_report(f"{self.name}\n{commands_report}")
            overall_report = []
            for config in self.configs:
                all_reports = config.position_handler.report()
                for report in all_reports:
                    await TelegramReporter().log_report(str(report))
                overall_report.append(PositionsReport.give_overall_report(all_reports))

            overall_report = sum(overall_report)
            await TelegramReporter().public_report(
                self.name + "\n" + str(overall_report)
            )

            now = datetime.now(tz=timezone.utc)
            report_time = (now + timedelta(days=1)).replace(
                hour=self.report_time["h"], minute=self.report_time["m"], microsecond=0
            )
            sleep_time = report_time - now

    async def start(self):
        tracemalloc.start()
        await TelegramReporter().log_report(
            f"--{self.name}--\n⚡⚡\nStart at\n{self._start_time} utc\n⚡⚡"
        )
        tasks = [self.trade_task(config) for config in self.configs]
        tasks.append(self.heartbeat())
        tasks.append(self.report())
        tasks.append(self.manage())
        await asyncio.gather(*tasks)
