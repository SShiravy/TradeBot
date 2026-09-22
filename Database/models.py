from datetime import datetime, timezone

from sqlmodel import Field, SQLModel

from ChartModule.models import Signal
from Database.hashing import generate_hash, serialize_config
from Settings.timing import TimeHandler
from TraderBot.trader_bot import TraderBot


class TraderBotRow(SQLModel, table=True):
    """A trader bot configuration together with the hash identifying it."""

    __tablename__ = "Trader_Bots"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)

    identifier: str = Field(index=True)
    bot_type: str = Field(index=True)
    chart: str = Field(index=True)
    strategy: str = Field(index=True)

    config_hash: str = Field(index=True, unique=True)
    config_json: str

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def give_config_hash(cls, bot: TraderBot) -> str:
        """Hash of bot.export_config(), the identity of a bot inside the db."""
        return generate_hash(bot.export_config())

    @classmethod
    def generate_datapoint(cls, bot: TraderBot) -> "TraderBotRow":
        config = bot.export_config()
        return cls(
            identifier=bot.identifier,
            bot_type=type(bot).__name__,
            chart=str(bot.chart),
            strategy=bot.strategy.name,
            config_hash=generate_hash(config),
            config_json=serialize_config(config),
        )

    def __str__(self) -> str:
        return (
            f"[{self.id}] {self.bot_type} {self.identifier} ({self.config_hash[:12]})"
        )


class SignalRow(SQLModel, table=True):
    """
    The attributes every Signal inherits from its parent class.

    The candle is reduced to its timestamp and the chart to str(chart).
    """

    __tablename__ = "Signals"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)

    signal_type: str = Field(index=True)
    chart: str = Field(index=True)
    timestamp: int = Field(index=True)
    side: str = Field(index=True)
    source: str
    report_id: int | None = Field(default=None)

    trader_bot_id: int = Field(foreign_key="Trader_Bots.id", index=True)

    @classmethod
    def generate_datapoint(cls, signal: Signal, trader_bot_id: int) -> "SignalRow":
        return cls(
            signal_type=type(signal).__name__,
            chart=str(signal.chart),
            timestamp=signal.candle.timestamp,
            side=signal.side.value,
            source=signal.source,
            report_id=signal.report_id,
            trader_bot_id=trader_bot_id,
        )

    def __str__(self) -> str:
        return f"{self.chart} {self.side} at {TimeHandler.to_datetime(self.timestamp)} from {self.source}"
