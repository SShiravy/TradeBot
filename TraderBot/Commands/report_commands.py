import logging
from ChartModule.models import Signal
from TraderBot.models import Command, PnLReport, Position, ReportCommandContext
from TraderBot.PositionHandlers.trades_pnl import PnLReportGenerator

logger = logging.getLogger("Commands")


class ReportCommand(Command):
    def __init__(
        self, context: ReportCommandContext, bounded_commands: list[Command] = []
    ):
        self.context: ReportCommandContext
        super().__init__(context, bounded_commands)


class ReportNewSignal(ReportCommand):
    def __init__(
        self,
        signal: Signal,
        context: ReportCommandContext,
        bounded_commands: list[Command] = [],
    ):
        super().__init__(context, bounded_commands)
        self.signal = signal
        self.msg_id: int | None = None

    async def command(self):
        path = (
            self.context.reporter.save_path
            or f"Records/SignalsImg/{self.signal.source}/"
        )
        msg = self.context.reporter.msg_formater.new_signal(self.signal)
        res = await self.context.reporter.send_msg(
            msg,
            img_path=self.context.figure.save_image(
                name=str(self.signal.candle.timestamp), path=path
            )
            if self.context.figure
            else None,
            reply_id=self.context.reply_id,
        )
        if not res:
            logger.warning(f"result of sending {self.signal}: {res}")
            return False
        self.msg_id = getattr(res, "message_id", res)
        return True


class ReportNewPosition(ReportCommand):
    def __init__(
        self,
        position: Position,
        context: ReportCommandContext,
        bounded_commands: list[Command] = [],
    ):
        super().__init__(context, bounded_commands)
        self.position = position

    async def command(self):
        msg = self.context.reporter.msg_formater.new_position(self.position)
        path = (
            self.context.reporter.save_path
            or f"Records/PositionImg/{self.position.source}/"
        )
        res = await self.context.reporter.send_msg(
            msg,
            img_path=self.context.figure.save_image(
                name=str(self.position.defined_timestamp), path=path
            )
            if self.context.figure
            else None,
            reply_id=self.context.reply_id,
        )
        if not res:
            logger.warning(f"result of sending {self.position}: {res}")
            return False
        self.position.report_id = getattr(res, "message_id", res)
        return True


class StoplossHitReport(ReportCommand):
    def __init__(
        self,
        position: Position,
        context: ReportCommandContext,
        pnl_report: PnLReport | None = None,
        bounded_commands: list[Command] = [],
    ):
        super().__init__(context, bounded_commands)
        self.pnl_report = pnl_report
        self.position = position

    def give_pnl_report(self):
        if self.pnl_report == None:
            self.pnl_report = PnLReportGenerator.position_report(self.position)
        return self.pnl_report

    async def command(self):
        msg = self.context.reporter.msg_formater.position_closed(
            self.position, self.give_pnl_report()
        )
        res = await self.context.reporter.send_msg(
            msg, reply_id=self.position.report_id
        )
        if not res:
            return False
        return True


class TriggerHitReport(ReportCommand):
    def __init__(
        self,
        position: Position,
        context: ReportCommandContext,
        trail_stop: bool = False,
        pnl_report: PnLReport | None = None,
        bounded_commands: list[Command] = [],
    ):
        super().__init__(context, bounded_commands)
        self.position = position
        self.pnl_report = pnl_report
        self.trail_stop = trail_stop

    def give_pnl_report(self):
        if self.pnl_report == None:
            self.pnl_report = PnLReportGenerator.position_report(self.position)
        return self.pnl_report

    async def command(self):
        msg = self.context.reporter.msg_formater.trigger_hit(
            self.position, self.give_pnl_report()
        )
        if self.trail_stop:
            msg += "\n\n" + self.context.reporter.msg_formater.sl_trailed(self.position)
        res = await self.context.reporter.send_msg(
            msg, reply_id=self.position.report_id
        )
        if not res:
            return False
        return True
