import logging
from ChartModule.models import Signal
from TraderBot.models import Command, PnLReport
from TraderBot.PositionHandlers.trades_pnl import PnLReportGenerator

logger = logging.getLogger("Reporter")


class NewSignalReport(Command):
    def __init__(
        self,
        signal: Signal,
        bounded_command: Command | None = None,
        img_path: str | None = None,
    ):
        super().__init__(bounded_command)
        self.signal = signal
        self.img_path = img_path

    async def command(self):
        if not self.reporter:
            logger.warning("Reporter not initialized, cannot send new signal report")
            return True
        msg = self.reporter.msg_formater.new_signal(self.signal)
        res = await self.reporter.send_msg(msg, img_path=self.img_path)
        if not res:
            return False
        return True


class NewPositionReport(Command):
    def __init__(
        self,
        bounded_command: Command | None = None,
        img_path: str | None = None,
        reply_id: None | int = None,
    ):
        super().__init__(bounded_command)
        self.img_path = img_path
        self.reply_id = reply_id

    async def command(self):
        if not self.reporter:
            logger.warning("Reporter not initialized, cannot send new position report")
            return True
        msg = self.reporter.msg_formater.new_position(self.position)
        res = await self.reporter.send_msg(
            msg, img_path=self.img_path, reply_id=self.reply_id
        )
        if not res:
            return False
        self.position.report_id = res.message_id
        return True


class StoplossHitReport(Command):
    def __init__(self, bounded_command: Command | None = None):
        super().__init__(bounded_command)
        self._pnl_report: PnLReport | None = None

    def give_pnl_report(self):
        if self._pnl_report == None:
            self._pnl_report = PnLReportGenerator.position_report(self.position)
        return self._pnl_report

    async def command(self):
        if not self.reporter:
            logger.warning("Reporter not initialized, cannot send new position report")
            return True
        if self.reporter:
            msg = self.reporter.msg_formater.position_closed(
                self.position, self.give_pnl_report()
            )
            res = await self.reporter.send_msg(msg, reply_id=self.position.report_id)
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
            self._pnl_report = PnLReportGenerator.position_report(self.position)
        return self._pnl_report

    async def command(self):
        if not self.reporter:
            logger.warning("Reporter not initialized, cannot send new position report")
            return True
        if self.reporter:
            msg = self.reporter.msg_formater.trigger_hit(
                self.position, self.give_pnl_report()
            )
            if self.trail_stop:
                msg += "\n\n" + self.reporter.msg_formater.sl_trailed(self.position)
            res = await self.reporter.send_msg(msg, reply_id=self.position.report_id)
            if not res:
                return False
        return True
