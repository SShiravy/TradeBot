from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING
from ChartModule.models import Signal
from TraderBot.models import Command, CommandContext

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

logger = logging.getLogger("Commands")


@dataclass(slots=True)
class DatabaseCommandContext(CommandContext):
    bot_hash: str


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

    @property
    def engine(self) -> "Engine":
        return self.db_engine or self.database().engine


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
        database = self.database()
        try:
            bot_row = database.fetch_trader_bot_by_hash(
                self.context.bot_hash, self.engine
            )
            if bot_row is None or bot_row.id is None:
                logger.error(
                    f"no trader bot recorded under {self.context.bot_hash}, "
                    f"{self.signal} not stored"
                )
                return False
            row = database.store_signal_by_bot_id(self.signal, bot_row.id, self.engine)
        except Exception:
            logger.exception(f"storing {self.signal} failed")
            return False
        self.row_id = row.id
        return row.id is not None
