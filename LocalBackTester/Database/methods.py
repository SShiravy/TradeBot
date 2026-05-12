from ChartModule.models import Candle
from DivergenceStrategy.divergence import DivergenceTradeConfig, DivergenceSignal
from sqlmodel import Session, select
from LocalBackTester.Database.divergence_models import DiverBacktestRow, DiverSignalRow
from LocalBackTester.Database.create_db import engine
import logging

logger = logging.getLogger("DB Methods")


def fetch_diver_backtest(diver_tradeconfig: DivergenceTradeConfig):
    """Fetch diver_tradeconfig from db with same hash. return backtest row or None"""
    hash = DiverBacktestRow.give_config_hash(diver_tradeconfig)
    with Session(engine) as session:
        statement = select(DiverBacktestRow).where(DiverBacktestRow.config_hash == hash)
        result = session.exec(statement).first()
    return result

def fetch_diver_signal_models(diver_tradeconfig: DivergenceTradeConfig):
    """Fetch signals related to a diver_tradeconfig in db with same hash return signals or None"""
    result = fetch_diver_backtest(diver_tradeconfig)
    if result is None:
        logger.info("No backtest related to this tradeconfig in db")
        return None
    with Session(engine) as session:
        statement = select(DiverSignalRow).where(DiverSignalRow.source == result.id)
        result = session.exec(statement).all()
    return result

def fetch_diver_siganls(diver_tradeconfig: DivergenceTradeConfig):
    signal_models = fetch_diver_signal_models(diver_tradeconfig)
    if signal_models is None:
        logger.info("No diver signal_model related to this tradeconfig in db")
        return None
    
    # diver_signals_obj = []
    # for signal in signal_models:
    #     DivergenceSignal(chart=diver_tradeconfig.chart)
    
    

def store_diver_backtest(diver_tradeconfig: DivergenceTradeConfig):
    if not fetch_diver_backtest(diver_tradeconfig):
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
