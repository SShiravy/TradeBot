from dataclasses import dataclass
from Settings.timing import TimeHandler
from TraderBot.models import (
    Command,
    CommandContext,
    ExchangeAgent,
    Position,
)
import logging


logger = logging.getLogger("Commands")


@dataclass(slots=True)
class TradeCommandContext(CommandContext):
    position: Position
    agent: ExchangeAgent


class TradeCommand(Command):
    def __init__(
        self, context: TradeCommandContext, bounded_commands: list[Command] = []
    ):
        self.context: TradeCommandContext
        super().__init__(context, bounded_commands)


class OpenPosition(TradeCommand):
    async def command(self):
        entry_price = self.context.agent.open_position(self.context.position)
        if entry_price:
            self.context.position.entry_price = entry_price
            self.context.position.open_timestamp = TimeHandler.now()
            return True
        return False


class StopLoss(TradeCommand):
    async def command(self):
        self.context.position.closed_timestamp = TimeHandler.now()
        return True


class TakeProfit(TradeCommand):
    async def command(self) -> bool:
        return True


class TrailStoploss(TradeCommand):
    def __init__(
        self,
        new_stoploss: float,
        context: TradeCommandContext,
        bounded_command: list[Command] = [],
    ):
        super().__init__(context, bounded_command)
        self.stoploss_price = new_stoploss

    async def command(self):
        if self.context.agent.change_stoploss(
            self.context.position, self.stoploss_price
        ):
            return False
        self.context.position.stoploss.price = self.stoploss_price
        return True
