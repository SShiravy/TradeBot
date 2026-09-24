from TraderBot.models import Command, Event, PnLReport
from ChartModule.models import Signal
import TraderBot.Commands as commands
import logging


logger = logging.getLogger("Events")


class NewPosition(Event):
    def report_command(self):
        if not self.trade_context or not self.report_context:
            return
        commands.ReportNewPosition(
            self.trade_context.position, self.report_context
        ).send()

    def trade_command(self):
        if not self.trade_context:
            return
        commands.OpenPosition(self.trade_context).send()


class NewSignal(Event):
    def __init__(
        self,
        signal: Signal,
        trade_context: commands.TradeCommandContext | None = None,
        report_context: commands.ReportCommandContext | None = None,
        record_context: commands.DatabaseCommandContext | None = None,
        extra_commands: list[Command] = [],
    ):
        super().__init__(trade_context, report_context, record_context, extra_commands)
        self.signal = signal

    def report_command(self):
        if not self.report_context:
            return
        commands.ReportNewSignal(self.signal, self.report_context).send()

    def database_command(self):
        if not self.record_context:
            return
        commands.RecordSignal(self.signal, self.record_context).send()


class StopLossHit(Event):
    def __init__(
        self,
        trade_context: commands.TradeCommandContext | None = None,
        report_context: commands.ReportCommandContext | None = None,
        record_context: commands.DatabaseCommandContext | None = None,
        pnl_report: PnLReport | None = None,
        extra_commands: list[Command] = [],
    ):
        super().__init__(trade_context, report_context, record_context, extra_commands)
        self.pnl_report = pnl_report

    def report_command(self):
        if not self.trade_context or not self.report_context:
            return
        commands.StoplossHitReport(
            self.trade_context.position, self.report_context, self.pnl_report
        ).send()

    def database_command(self):
        pass

    def trade_command(self):
        if not self.trade_context:
            return
        commands.StopLoss(self.trade_context).send()

    def occur(
        self,
        trade_context: commands.TradeCommandContext | None = None,
        report_context: commands.ReportCommandContext | None = None,
        record_context: commands.DatabaseCommandContext | None = None,
        pnl_report: PnLReport | None = None,
        *args,
        **kwargs,
    ):
        if pnl_report:
            self.pnl_report = pnl_report
        return super().occur(
            trade_context, report_context, record_context, *args, **kwargs
        )


class TakeProfitHit(Event):
    def __init__(
        self,
        trade_context: commands.TradeCommandContext | None = None,
        report_context: commands.ReportCommandContext | None = None,
        record_context: commands.DatabaseCommandContext | None = None,
        pnl_report: PnLReport | None = None,
        trail_stop: float | None = None,
        extra_commands: list[Command] = [],
    ):
        if pnl_report:
            self.pnl_report = pnl_report
        if trail_stop:
            self.trail_stop = trail_stop
        super().__init__(trade_context, report_context, record_context, extra_commands)

    def database_command(self):
        pass

    def report_command(self):
        if not self.trade_context or not self.report_context:
            return
        commands.TriggerHitReport(
            self.trade_context.position,
            self.report_context,
            self.trail_stop != None,
            self.pnl_report,
        ).send()

    def trade_command(self):
        if not self.trade_context:
            return
        commands.TakeProfit(self.trade_context).send()
        if self.trail_stop:
            commands.TrailStoploss(self.trail_stop, self.trade_context).send()

    def occur(
        self,
        trade_context: commands.TradeCommandContext | None = None,
        report_context: commands.ReportCommandContext | None = None,
        record_context: commands.DatabaseCommandContext | None = None,
        pnl_report: PnLReport | None = None,
        trail_stop: float | None = None,
        *args,
        **kwargs,
    ):
        if pnl_report:
            self.pnl_report = pnl_report
        if trail_stop:
            self.trail_stop = trail_stop
        return super().occur(
            trade_context, report_context, record_context, *args, **kwargs
        )
