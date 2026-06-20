# ruff: noqa: F401
from sqlmodel import SQLModel, create_engine
from config import settings

engine = create_engine(settings.LOCAL_BACKTEST_DB_NAME)


def create_db():
    from LocalBackTester.Database.divergence_models import (
        DiverBacktestRow,
        DiverSignalRow,
    )
    from LocalBackTester.Database.backtest_models import PositionsResult

    SQLModel.metadata.create_all(engine)
