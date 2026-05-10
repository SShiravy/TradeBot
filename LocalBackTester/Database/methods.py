

from signal import signal

from DivergenceStrategy.divergence import DivergenceTradeConfig, DivergenceSignal
from sqlmodel import Session
from LocalBackTester.Database.divergence_models import DiverBacktestRow,DiverSignalRow
from LocalBackTester.Database.create_db import engine

def store_diver_backtest(diver_tradeconfig: DivergenceTradeConfig):
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

