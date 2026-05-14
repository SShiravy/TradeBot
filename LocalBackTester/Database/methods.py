from ChartModule.models import IndicatorCandleSource, MarketSide
from DivergenceStrategy.divergence import DivergenceTradeConfig, DivergenceSignal
from ChartModule.Indicators import Line
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


def fetch_diver_siganls(
    diver_tradeconfig: DivergenceTradeConfig,
) -> list[DivergenceSignal] | None:
    signal_models = fetch_diver_signal_models(diver_tradeconfig)
    if signal_models is None:
        logger.info("No diver signal_model related to this tradeconfig in db")
        return None

    all_diver_signals = []
    base_chartdata, second_chartdata = diver_tradeconfig.get_chartdata()  # type: ignore
    for signal in signal_models:
        signal_candle = base_chartdata.find_candle_by_time(signal.signal_timestamp)
        if signal.side == "Bullish":
            line_candlesource = (
                IndicatorCandleSource.Bottom
                if diver_tradeconfig.strategy.body_candle
                else IndicatorCandleSource.Low
            )

        else:  # signal.side == "Bearish"
            line_candlesource = (
                IndicatorCandleSource.Top
                if diver_tradeconfig.strategy.body_candle
                else IndicatorCandleSource.High
            )

        if signal_candle is None:
            logger.error(f"No candle for signal: {signal}")
            continue
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


def store_diver_backtest(diver_tradeconfig: DivergenceTradeConfig):
    if fetch_diver_backtest(diver_tradeconfig):
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
