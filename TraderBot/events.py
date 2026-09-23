from abc import ABC, abstractmethod
from ChartModule.plot import Figure
from Settings.timing import TimeHandler
import Commands as commands
import logging

from TraderBot.models import Command, ExchangeAgent, Position, ReporterBot

logger = logging.getLogger("Events")


class Event(ABC):
    occurred_events: dict[str, int] = {}
    report_commands: bool = True
    db_record_commands: bool = True

    def __init__(self, extra_commands: list[Command] = []):
        self.occur_timestamps: int | None = None
        self.extra_commands = extra_commands

    @property
    def name(self):
        return self.__class__.__name__

    def __str__(self) -> str:
        return f"{self.name}|occur:{self.occur_timestamps}"

    def __record(self):
        n = self.occurred_events.get(self.name, 0)
        self.occurred_events[self.name] = n + 1

    @abstractmethod
    def send_commands(self, *args, **kwargs):
        pass

    def occur(self, *args, **kwargs):
        logger.info(f"{self.name} event occure")
        self.occur_timestamps = TimeHandler.now()
        self.__record()
        self.send_commands(*args, **kwargs)
        for command in self.extra_commands:
            command.send()


class OpenPosition(Event):
    def __init__(
        self,
        position: Position,
        agent: ExchangeAgent,
        figure: Figure,
        reporter: ReporterBot | None,
        reply_id: int | None = None,
    ):
        super().__init__()
        self.position = position
        self.agent = agent
        self.figure = figure
        self.reporter = reporter
        self.reply_id = reply_id

    def send_commands(self, *args, **kwargs):
        bounded_commands = []
        if self.reporter:
            bounded_commands.append(
                commands.NewPositionReport(plot=self.figure, reply_id=self.reply_id)
            )
        if self.db_record_commands:
            pass

        commands.OpenPosition(bounded_commands).send()


# OpenPosition
# StopLoss
# TakeProfit
# TrailStoploss

# NewSignalReport
# NewPositionReport
# StoplossHitReport
# TriggerHitReport

# store pos pnl
# store new signal
# sttore bot

# daily report
