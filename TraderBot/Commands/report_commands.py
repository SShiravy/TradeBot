import logging
from ChartModule.models import Signal
from ChartModule.plot import Figure
from TraderBot.models import Command, CommandStatus, PnLReport, ReporterBot
from TraderBot.PositionHandlers.trades_pnl import PnLReportGenerator

logger = logging.getLogger("Reporter")


class NewSignalReport(Command):
    def __init__(
        self,
        signal: Signal,
        bounded_command: Command | None = None,
        plot: Figure | None = None,
    ):
        super().__init__(bounded_command)
        self.signal = signal
        self.plot = plot
        self.reporter: ReporterBot | None

    def send(self, context=None, reporter: ReporterBot | None = None):
        # TODO: Creat specific context for this command and remove extra param
        self.reporter = reporter
        self.status = CommandStatus.PENDING

    async def command(self):
        if not self.reporter:
            logger.warning("Reporter not initialized, cannot send new signal report")
            return True
        msg = self.reporter.msg_formater.new_signal(self.signal)
        res = await self.reporter.send_msg(
            msg, img_path=self.plot.save_image() if self.plot else None
        )
        if not res:
            return False
        return True


class NewPositionReport(Command):
    def __init__(
        self,
        bounded_command: Command | None = None,
        plot: Figure | None = None,
        reply_id: None | int = None,
    ):
        super().__init__(bounded_command)
        self.plot = plot
        self.reply_id = reply_id

    async def command(self):
        if not self.context.reporter:
            logger.warning("Reporter not initialized, cannot send new position report")
            return True
        msg = self.context.reporter.msg_formater.new_position(self.context.position)
        res = await self.context.reporter.send_msg(
            msg,
            img_path=self.plot.save_image() if self.plot else None,
            reply_id=self.reply_id,
        )
        if not res:
            return False
        self.context.position.report_id = res.message_id
        return True


class StoplossHitReport(Command):
    def __init__(self, bounded_command: Command | None = None):
        super().__init__(bounded_command)
        self._pnl_report: PnLReport | None = None

    def give_pnl_report(self):
        if self._pnl_report == None:
            self._pnl_report = PnLReportGenerator.position_report(self.context.position)
        return self._pnl_report

    async def command(self):
        if not self.context.reporter:
            logger.warning("Reporter not initialized, cannot send new position report")
            return True
        if self.context.reporter:
            msg = self.context.reporter.msg_formater.position_closed(
                self.context.position, self.give_pnl_report()
            )
            res = await self.context.reporter.send_msg(
                msg, reply_id=self.context.position.report_id
            )
            if not res:
                return False
        return True


class TriggerHitReport(Command):
    def __init__(
        self, bounded_command: Command | None = None, trail_stop: bool = False
    ):
        super().__init__(bounded_command)
        self._pnl_report: PnLReport | None = None
        self.trail_stop = trail_stop

    def give_pnl_report(self):
        if self._pnl_report == None:
            self._pnl_report = PnLReportGenerator.position_report(self.context.position)
        return self._pnl_report

    async def command(self):
        if not self.context.reporter:
            logger.warning("Reporter not initialized, cannot send new position report")
            return True
        if self.context.reporter:
            msg = self.context.reporter.msg_formater.trigger_hit(
                self.context.position, self.give_pnl_report()
            )
            if self.trail_stop:
                msg += "\n\n" + self.context.reporter.msg_formater.sl_trailed(
                    self.context.position
                )
            res = await self.context.reporter.send_msg(
                msg, reply_id=self.context.position.report_id
            )
            if not res:
                return False
        return True
