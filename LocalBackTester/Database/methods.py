from ChartModule.models import CandlesSource, MarketSide
from DivergenceStrategy.divergence import DivergenceTradeConfig, DivergenceSignal
from ChartModule.Indicators import Line
from sqlmodel import Session, select
from LocalBackTester.Database.divergence_models import DiverBacktestRow, DiverSignalRow
from LocalBackTester.Database.backtest_models import PositionsResult
from LocalBackTester.Database.create_db import engine
import logging

from TradingModule.PositionHandlers.model import PositionHandler


logger = logging.getLogger("DB Methods")

# Diver Config ----------


def fetch_diver_backtest(
    diver_tradeconfig: DivergenceTradeConfig,
) -> DiverBacktestRow | None:
    """Fetch diver_tradeconfig from db with same hash. return backtest row or None"""
    hash = DiverBacktestRow.give_config_hash(diver_tradeconfig)
    with Session(engine) as session:
        statement = select(DiverBacktestRow).where(DiverBacktestRow.config_hash == hash)
        result = session.exec(statement).first()
    return result


def store_diver_backtest(diver_tradeconfig: DivergenceTradeConfig):
    if fetch_diver_backtest(diver_tradeconfig):
        raise Exception("Same config already exists in db...")
    datapoint = DiverBacktestRow.generate_datapoint(diver_tradeconfig)
    with Session(engine) as session:
        session.add(datapoint)
        session.commit()
        session.refresh(datapoint)

    return datapoint


# Diver Signal ----------


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


def fetch_diver_siganls(
    diver_tradeconfig: DivergenceTradeConfig,
) -> list[DivergenceSignal] | None:
    signal_models = fetch_diver_signal_models(diver_tradeconfig)
    if signal_models is None:
        logger.info("No diver signal_model related to this tradeconfig in db")
        return None

    all_diver_signals = []
    n_bar = diver_tradeconfig.chart.total_bars_number  # type:ignore
    base_chartdata, second_chartdata = diver_tradeconfig.get_chartdata(n_bar=n_bar)  # type: ignore
    for signal in signal_models:
        signal_candle = base_chartdata.find_candle_by_time(signal.signal_timestamp)
        if signal_candle is None:
            logger.error(f"No candle for signal: {signal}")
            continue

        if signal.side == "Bullish":
            line_candlesource = (
                CandlesSource.Bottom
                if diver_tradeconfig.strategy.body_candle
                else CandlesSource.Low
            )

        else:  # signal.side == "Bearish"
            line_candlesource = (
                CandlesSource.Top
                if diver_tradeconfig.strategy.body_candle
                else CandlesSource.High
            )

        diver_signal = DivergenceSignal(
            chart=diver_tradeconfig.chart,
            candle=signal_candle,
            side=MarketSide(signal.side),  # type: ignore
            source=str(signal.source),
            base_line=Line(
                source=line_candlesource,
                start_candle=base_chartdata.find_candle_by_time(
                    signal.baseline_start_timestamp  # type: ignore
                ),
                end_candle=base_chartdata.find_candle_by_time(
                    signal.baseline_end_timestamp
                ),  # type: ignore
            ),
            second_line=Line(
                source=line_candlesource,
                start_candle=second_chartdata.find_candle_by_time(
                    signal.secondline_start_timestamp  # type: ignore
                ),
                end_candle=second_chartdata.find_candle_by_time(
                    signal.secondline_end_timestamp
                ),  # type: ignore
            ),
        )
        all_diver_signals.append(diver_signal)
    return all_diver_signals


def store_diver_signal(diver_signals: list[DivergenceSignal], source_id):
    with Session(engine) as session:
        for diver_signal in diver_signals:
            datapoint = DiverSignalRow.generate_datapoint(diver_signal, source_id)
            session.add(datapoint)
        session.commit()


# Position Result --------------


def fetch_positions_result(handler: PositionHandler, backtest_source: int):
    hash = PositionsResult.give_handler_hash(handler, backtest_source)
    with Session(engine) as session:
        statement = select(PositionsResult).where(PositionsResult.handler_hash == hash)
        result = session.exec(statement).first()
    return result


def store_positions_result(
    handler: PositionHandler, commands_report: str, source_id: int
):
    if fetch_positions_result(handler, source_id):
        raise Exception("Same config already exists in db...")
    datapoint = PositionsResult.generate_datapoint(handler, commands_report, source_id)
    with Session(engine) as session:
        session.add(datapoint)
        session.commit()
        session.refresh(datapoint)
    return datapoint
