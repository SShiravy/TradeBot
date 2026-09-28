import logging

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from ChartModule.models import Signal
from Database.create_db import live_db_engine
from Database.models import PnLReportRow, SignalRow, TraderBotRow
from TraderBot.models import PnLReport
from TraderBot.trader_bot import TraderBot

logger = logging.getLogger("Database")


# Trader Bot ----------


def fetch_trader_bot_by_hash(
    config_hash: str, db_engine: Engine = live_db_engine
) -> TraderBotRow | None:
    with Session(db_engine) as session:
        statement = select(TraderBotRow).where(TraderBotRow.config_hash == config_hash)
        return session.exec(statement).first()


def fetch_trader_bot(
    bot: TraderBot, db_engine: Engine = live_db_engine
) -> TraderBotRow | None:
    return fetch_trader_bot_by_hash(TraderBotRow.give_config_hash(bot), db_engine)


def store_trader_bot(
    bot: TraderBot, db_engine: Engine = live_db_engine
) -> TraderBotRow:
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


def give_trader_bot_id(bot: TraderBot, db_engine: Engine = live_db_engine) -> int:
    row = store_trader_bot(bot, db_engine)
    if row.id is None:
        raise ValueError(f"Trader bot row without id: {row}")
    return row.id


# Signal ----------


def fetch_signal(
    signal: Signal, bot: TraderBot, db_engine: Engine = live_db_engine
) -> SignalRow | None:
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


def fetch_signals(
    bot: TraderBot, db_engine: Engine = live_db_engine
) -> list[SignalRow]:
    bot_row = fetch_trader_bot(bot, db_engine)
    if bot_row is None:
        logger.info("No trader bot related to this bot in db")
        return []

    with Session(db_engine) as session:
        statement = (
            select(SignalRow)
            .where(SignalRow.trader_bot_id == bot_row.id)
            .order_by(SignalRow.timestamp)  # type: ignore
        )
        return list(session.exec(statement).all())


def store_signal_by_bot_id(
    signal: Signal, trader_bot_id: int, db_engine: Engine = live_db_engine
) -> SignalRow:
    datapoint = SignalRow.generate_datapoint(signal, trader_bot_id)
    with Session(db_engine) as session:
        session.add(datapoint)
        session.commit()
        session.refresh(datapoint)
    logger.info(f"Signal stored: {datapoint}")
    return datapoint


def store_signal(
    signal: Signal, bot: TraderBot, db_engine: Engine = live_db_engine
) -> SignalRow:
    return store_signal_by_bot_id(signal, give_trader_bot_id(bot, db_engine), db_engine)


def store_signals(
    signals: list[Signal], bot: TraderBot, db_engine: Engine = live_db_engine
) -> list[SignalRow]:
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


# PnL Report ----------


def _pnl_report_statement(trader_bot_id: int, identifier: str, overall: bool):
    """
    The row a report of this kind belongs in: the single overall row of the bot,
    or the row of one identifier. An overall row is not matched on identifier,
    it merges reports of every chart, side and source the bot traded.
    """
    statement = (
        select(PnLReportRow)
        .where(PnLReportRow.trader_bot_id == trader_bot_id)
        .where(PnLReportRow.overall_report == overall)
    )
    if not overall:
        statement = statement.where(PnLReportRow.identifier == identifier)
    return statement


def fetch_pnl_report(
    bot: TraderBot,
    identifier: str = "",
    overall: bool = False,
    db_engine: Engine = live_db_engine,
) -> PnLReportRow | None:
    """
    A recorded report of bot: its overall one when overall is set, the report
    of identifier otherwise. None when nothing is recorded yet.
    """
    bot_row = fetch_trader_bot(bot, db_engine)
    if bot_row is None or bot_row.id is None:
        logger.info("No trader bot related to this bot in db")
        return None

    with Session(db_engine) as session:
        statement = _pnl_report_statement(bot_row.id, identifier, overall)
        return session.exec(statement).first()


def fetch_pnl_reports(
    bot: TraderBot, db_engine: Engine = live_db_engine
) -> list[PnLReportRow]:
    """Every pnl report recorded for bot, its overall one included."""
    bot_row = fetch_trader_bot(bot, db_engine)
    if bot_row is None:
        logger.info("No trader bot related to this bot in db")
        return []

    with Session(db_engine) as session:
        statement = (
            select(PnLReportRow)
            .where(PnLReportRow.trader_bot_id == bot_row.id)
            .order_by(PnLReportRow.last_time)  # type: ignore
        )
        return list(session.exec(statement).all())


def store_pnl_report(
    report: PnLReport, bot: TraderBot, db_engine: Engine = live_db_engine
) -> PnLReportRow:
    """
    Record report for bot.

    When a report of the same kind is already there - the overall row of the
    bot if report is an overall one, the row of the same identifier otherwise -
    the two are added together and the row is replaced by the sum. So the row
    always holds everything recorded for that bot so far, and report should
    only carry what is not recorded yet.
    """
    trader_bot_id = give_trader_bot_id(bot, db_engine)
    with Session(db_engine) as session:
        statement = _pnl_report_statement(
            trader_bot_id, report.identifier, report.overall_report
        )
        stored = session.exec(statement).first()
        if stored is None:
            datapoint = PnLReportRow.generate_datapoint(report, trader_bot_id)
        else:
            datapoint = stored.apply(stored.to_report(report.chart) + report)

        session.add(datapoint)
        session.commit()
        session.refresh(datapoint)

    logger.info(f"PnL report recorded: {datapoint}")
    return datapoint
