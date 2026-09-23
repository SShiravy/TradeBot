from TraderBot.models import _Event, Command, PnLReport
from ChartModule.models import Signal
from Settings.timing import TimeHandler
import Commands as commands
import logging


logger = logging.getLogger("Events")


class Event(_Event):
    occurred_events: dict[str, int] = {}
    consider_report: bool = True
    consider_db_record: bool = True
    consider_trade: bool = True

    def __init__(
        self,
        trade_context: commands.TradeCommandContext | None = None,
        report_context: commands.ReportCommandContext | None = None,
        record_context: commands.DatabaseCommandContext | None = None,
        extra_commands: list[Command] = [],
    ):
        self.trade_context = trade_context
        self.report_context = report_context
        self.record_context = record_context
        self.occur_timestamps: int | None = None
        self.extra_commands = extra_commands

    @property
    def name(self):
        return self.__class__.__name__

    def __str__(self) -> str:
        return f"{self.name}|time:{self.occur_timestamps}"

    def __record(self):
        n = self.occurred_events.get(self.name, 0)
        self.occurred_events[self.name] = n + 1

    def report_command(self, *args, **kwargs):
        pass

    def database_command(self, *args, **kwargs):
        pass

    def trade_command(self, *args, **kwargs):
        pass

    def send_commands(self, *args, **kwargs):
        if self.consider_trade:
            self.trade_command(*args, **kwargs)
        if self.consider_report:
            self.report_command(*args, **kwargs)
        if self.consider_db_record:
            self.database_command(*args, **kwargs)

    def occur(
        self,
        trade_context: commands.TradeCommandContext | None = None,
        report_context: commands.ReportCommandContext | None = None,
        record_context: commands.DatabaseCommandContext | None = None,
        *args,
        **kwargs,
    ):
        if trade_context:
            self.trade_context = trade_context
        if report_context:
            self.report_context = report_context
        if record_context:
            self.record_context = record_context

        logger.info(f"{self.name} event occure")
        self.occur_timestamps = TimeHandler.now()
        self.__record()
        self.send_commands()
        for command in self.extra_commands:
            command.send()


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
        commands.RecordSignal(self.signal, self.record_context)


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
        pnl_report: PnLReport | None = None,
        trade_context: commands.TradeCommandContext | None = None,
        report_context: commands.ReportCommandContext | None = None,
        record_context: commands.DatabaseCommandContext | None = None,
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
        super().__init__(trade_context, report_context, record_context, extra_commands)
        self.pnl_report = pnl_report
        self.trail_stop = trail_stop

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
            commands.TrailStoploss(self.trail_stop, self.trade_context)

    def occur(
        self,
        pnl_report: PnLReport | None = None,
        trail_stop: float | None = None,
        trade_context: commands.TradeCommandContext | None = None,
        report_context: commands.ReportCommandContext | None = None,
        record_context: commands.DatabaseCommandContext | None = None,
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
