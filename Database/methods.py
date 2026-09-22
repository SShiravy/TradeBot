import logging

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from ChartModule.models import Signal
from Database.create_db import engine
from Database.models import SignalRow, TraderBotRow
from TraderBot.trader_bot import TraderBot

logger = logging.getLogger("Database")


# Trader Bot ----------


def fetch_trader_bot(bot: TraderBot, db_engine: Engine = engine) -> TraderBotRow | None:
    """Fetch the row whose config hash matches ``bot``, or None."""
    config_hash = TraderBotRow.give_config_hash(bot)
    with Session(db_engine) as session:
        statement = select(TraderBotRow).where(TraderBotRow.config_hash == config_hash)
        return session.exec(statement).first()


def store_trader_bot(bot: TraderBot, db_engine: Engine = engine) -> TraderBotRow:
    """
    Store the configuration of ``bot``.

    A bot already stored under the same config hash is returned untouched,
    so calling this on every startup is safe.
    """
    stored = fetch_trader_bot(bot, db_engine)
    if stored:
        logger.info(f"Trader bot already in db: {stored}")
        return stored

    datapoint = TraderBotRow.generate_datapoint(bot)
    with Session(db_engine) as session:
        session.add(datapoint)
        session.commit()
        session.refresh(datapoint)
    logger.info(f"Trader bot stored: {datapoint}")
    return datapoint


def give_trader_bot_id(bot: TraderBot, db_engine: Engine = engine) -> int:
    """Id of ``bot`` in the db, storing it first when it is not there yet."""
    row = store_trader_bot(bot, db_engine)
    if row.id is None:
        raise ValueError(f"Trader bot row without id: {row}")
    return row.id


# Signal ----------


def fetch_signal(
    signal: Signal, bot: TraderBot, db_engine: Engine = engine
) -> SignalRow | None:
    """Fetch the row of ``signal`` for ``bot``, or None."""
    bot_row = fetch_trader_bot(bot, db_engine)
    if bot_row is None:
        logger.info("No trader bot related to this bot in db")
        return None

    with Session(db_engine) as session:
        statement = (
            select(SignalRow)
            .where(SignalRow.trader_bot_id == bot_row.id)
            .where(SignalRow.timestamp == signal.candle.timestamp)
            .where(SignalRow.side == signal.side.value)
            .where(SignalRow.source == signal.source)
            .where(SignalRow.signal_type == type(signal).__name__)
        )
        return session.exec(statement).first()


def fetch_signals(bot: TraderBot, db_engine: Engine = engine) -> list[SignalRow]:
    """Every signal stored for ``bot``, oldest first."""
    bot_row = fetch_trader_bot(bot, db_engine)
    if bot_row is None:
        logger.info("No trader bot related to this bot in db")
        return []

    with Session(db_engine) as session:
        statement = (
            select(SignalRow)
            .where(SignalRow.trader_bot_id == bot_row.id)
            .order_by(SignalRow.timestamp) # type: ignore
        )
        return list(session.exec(statement).all())


def store_signal(
    signal: Signal, bot: TraderBot, db_engine: Engine = engine
) -> SignalRow:
    """Store ``signal`` under ``bot``, storing the bot config when needed."""
    datapoint = SignalRow.generate_datapoint(signal, give_trader_bot_id(bot, db_engine))
    with Session(db_engine) as session:
        session.add(datapoint)
        session.commit()
        session.refresh(datapoint)
    logger.info(f"Signal stored: {datapoint}")
    return datapoint


def store_signals(
    signals: list[Signal], bot: TraderBot, db_engine: Engine = engine
) -> list[SignalRow]:
    """Store ``signals`` under ``bot`` in a single transaction."""
    if not signals:
        return []

    bot_id = give_trader_bot_id(bot, db_engine)
    datapoints = [SignalRow.generate_datapoint(signal, bot_id) for signal in signals]
    with Session(db_engine) as session:
        session.add_all(datapoints)
        session.commit()
        for datapoint in datapoints:
            session.refresh(datapoint)
    logger.info(f"{len(datapoints)} signals stored for bot {bot_id}")
    return datapoints
