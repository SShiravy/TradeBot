import logging
from Settings.timing import TimeHandler
from TraderBot.models import Command, Trigger, TriggerType


logger = logging.getLogger("Commands")


class OpenPosition(Command):
    async def command(self):
        entry_price = self.context.exchange_agent.open_position(self.context.position)
        if entry_price:
            self.context.position.entry_price = entry_price
            self.context.position.open_timestamp = TimeHandler.now()
            return True
        return False


class StopLoss(Command):
    async def command(self):
        self.context.position.closed_timestamp = TimeHandler.now()
        return True


class TakeProfit(Command):
    async def command(self) -> bool:
        return True


class TrailStoploss(Command):
    def __init__(self, new_stoploss: float, bounded_command: Command | None = None):
        super().__init__(bounded_command)
        self.stoploss_price = new_stoploss

    async def command(self):
        if self.context.exchange_agent.change_stoploss(
            self.context.position, self.stoploss_price
        ):
            return False
        self.context.position.stoploss = Trigger(
            self.stoploss_price,
            self.context.position.volume,
            -1,
            StopLoss(),
            TriggerType.SL,
        )
        return True
