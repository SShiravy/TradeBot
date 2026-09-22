from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, create_engine
from Database.models import SignalRow, TraderBotRow
from Settings import settings

TABLES = [TraderBotRow.__table__, SignalRow.__table__]  # type:ignore

engine = create_engine(settings.LIVE_DB_NAME)
backtest_engine = create_engine(settings.BACKTEST_DB_NAME)


def give_engine(db_name: str) -> Engine:
    """Engine for any other database holding these same tables."""
    return create_engine(db_name)


def create_db(db_engine: Engine = engine) -> None:
    """Create the Trader_Bots and Signals tables if they do not exist yet."""
    SQLModel.metadata.create_all(db_engine, tables=TABLES)
