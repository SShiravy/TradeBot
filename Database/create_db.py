from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, create_engine
from Database.models import PnLReportRow, SignalRow, TraderBotRow
from Settings import settings

TABLES = [  # type:ignore
    TraderBotRow.__table__,
    SignalRow.__table__,
    PnLReportRow.__table__,
]

live_db_engine = create_engine(settings.LIVE_DB_NAME)
backtest_db_engine = create_engine(settings.BACKTEST_DB_NAME)


def give_engine(db_name: str) -> Engine:
    """Engine for any other database holding these same tables."""
    return create_engine(db_name)


def create_db(db_engine: Engine = live_db_engine) -> None:
    """Create the Trader_Bots, Signals and PnL_Reports tables if they are missing."""
    SQLModel.metadata.create_all(db_engine, tables=TABLES)
