from Settings.timing import TimeHandler
from TraderBot.models import (
    Command,
    TradeCommandContext,
)
import logging


logger = logging.getLogger("Commands")


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
        if self.context.position.stoploss.triggered_timestamp:
            logger.debug(f"stoploss of {self.context.position} already hit")
            return True
        if not self.context.agent.change_stoploss(
            self.context.position, self.stoploss_price
        ):
            return False
        self.context.position.stoploss.price = self.stoploss_price
        return True
