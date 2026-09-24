import logging
from typing import TYPE_CHECKING
from ChartModule.models import Signal
from TraderBot.models import Command, DatabaseCommandContext

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

logger = logging.getLogger("Commands")


class DatabaseCommand(Command):
    db_engine: "Engine | None" = None

    def __init__(
        self, context: DatabaseCommandContext, bounded_commands: list[Command] = []
    ):
        self.context: DatabaseCommandContext
        super().__init__(context, bounded_commands)

    @staticmethod
    def database():
        import Database

        return Database


class RecordSignal(DatabaseCommand):
    def __init__(
        self,
        signal: Signal,
        context: DatabaseCommandContext,
        bounded_commands: list[Command] = [],
    ):
        super().__init__(context, bounded_commands)
        self.signal = signal
        self.row_id: int | None = None

    async def command(self):
        if self.db_engine is None:
            return True
        database = self.database()
        bot_row = database.fetch_trader_bot_by_hash(
            self.context.bot_hash, self.db_engine
        )
        if bot_row is None or bot_row.id is None:
            logger.error(
                f"no trader bot recorded under {self.context.bot_hash}, "
                f"{self.signal} not stored"
            )
            return False
        row = database.store_signal_by_bot_id(self.signal, bot_row.id, self.db_engine)
        self.row_id = row.id
        return row.id is not None
