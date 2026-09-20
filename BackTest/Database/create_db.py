# ruff: noqa: F401
from sqlmodel import SQLModel, create_engine
from Settings.config import settings

engine = create_engine(settings.LOCAL_BACKTEST_DB_NAME)


def create_db():
    import Bots.DivergenceStrategy.divergence_db_models
    from BackTest.Database.backtest_models import PositionsResult

    SQLModel.metadata.create_all(engine)
