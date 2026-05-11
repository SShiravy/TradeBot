from DivergenceStrategy.divergence import DivergenceTradeConfig, DivergenceSignal
from sqlmodel import Session, select
from LocalBackTester.Database.divergence_models import DiverBacktestRow, DiverSignalRow
from LocalBackTester.Database.create_db import engine
import logging

logger = logging.getLogger("TradeCommand")


def valid_diver_backtest_hash(diver_tradeconfig: DivergenceTradeConfig) -> bool:
    """Check if already exists in db with same hash return False, otherwise return True"""
    hash = DiverBacktestRow.give_config_hash(diver_tradeconfig)
    with Session(engine) as session:
        statement = select(DiverBacktestRow).where(DiverBacktestRow.config_hash == hash)
        result = session.exec(statement).first()
        if result:
            return False
        else:
            return True


def store_diver_backtest(diver_tradeconfig: DivergenceTradeConfig):
    if not valid_diver_backtest_hash(diver_tradeconfig):
        logger.error("Same config already exists in db...")
        raise Exception("Same config already exists in db...")
    datapoint = DiverBacktestRow.give_datapoint(diver_tradeconfig)
    with Session(engine) as session:
        session.add(datapoint)
        session.commit()
        session.refresh(datapoint)

    return datapoint


def store_diver_signal(diver_signals: list[DivergenceSignal], source_id):
    with Session(engine) as session:
        for diver_signal in diver_signals:
            datapoint = DiverSignalRow.give_datapoint(diver_signal, source_id)
            session.add(datapoint)
        session.commit()
