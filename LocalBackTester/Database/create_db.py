from sqlmodel import create_engine

engine = create_engine("sqlite:///local_backtest.db")


SQLModel.metadata.create_all(engine)
