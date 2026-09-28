import json
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel

from ChartModule.models import Chart, Signal
from Database.hashing import generate_hash, serialize_config
from Settings.timing import TimeHandler
from TraderBot.models import PnLReport, PositionSide
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

    trader_bot_id: int = Field(foreign_key="Trader_Bots.id", index=True)

    @classmethod
    def generate_datapoint(cls, signal: Signal, trader_bot_id: int) -> "SignalRow":
        return cls(
            signal_type=type(signal).__name__,
            chart=str(signal.chart),
            timestamp=signal.candle.timestamp,
            side=signal.side.value,
            source=signal.source,
            trader_bot_id=trader_bot_id,
        )

    def __str__(self) -> str:
        return f"{self.chart} {self.side} at {TimeHandler.to_datetime(self.timestamp)} from {self.source}"


class PnLReportRow(SQLModel, table=True):
    __tablename__ = "PnL_Reports"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)

    identifier: str = Field(index=True)
    chart: str = Field(index=True)
    side: str = Field(index=True)
    source: str = Field(index=True)

    first_time: int = Field(index=True)
    last_time: int = Field(index=True)

    pnl_dollar: float = Field(default=0.0)
    pnl_percent: float = Field(default=0.0)
    pnl_pips: float = Field(default=0.0)
    volume: float = Field(default=0.0)

    wins: int = Field(default=0)
    flats: int = Field(default=0)
    loses: int = Field(default=0)
    total_positions: int = Field(default=0)

    max_win_in_a_row: int = Field(default=0)
    max_lose_in_a_row: int = Field(default=0)

    triggered_steps_json: str = Field(default="{}")
    overall_report: bool = Field(default=False, index=True)

    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    trader_bot_id: int = Field(foreign_key="Trader_Bots.id", index=True)

    def apply(self, report: PnLReport) -> "PnLReportRow":
        """Overwrite every value of this row with the ones of report."""
        self.identifier = report.identifier
        self.chart = str(report.chart)
        self.side = report.side.value
        self.source = report.source
        self.first_time = report.first_time
        self.last_time = report.last_time

        self.pnl_dollar = round(report.pnl_dollar, 3)
        self.pnl_percent = round(report.pnl_percent, 3)
        self.pnl_pips = round(report.pnl_pips, 3)
        self.volume = report.volume

        self.wins = report.wins
        self.flats = report.flats
        self.loses = report.loses
        self.total_positions = report.total_positions

        self.max_win_in_a_row = report.max_win_in_a_row
        self.max_lose_in_a_row = report.max_lose_in_a_row

        self.triggered_steps_json = json.dumps(
            {str(step): count for step, count in report.triggered_steps.items()},
            sort_keys=True,
        )
        self.overall_report = report.overall_report
        self.updated_at = datetime.now(timezone.utc)
        return self

    @classmethod
    def generate_datapoint(
        cls, report: PnLReport, trader_bot_id: int
    ) -> "PnLReportRow":
        row = cls(
            trader_bot_id=trader_bot_id,
            identifier=report.identifier,
            chart=str(report.chart),
            side=report.side.value,
            source=report.source,
            first_time=report.first_time,
            last_time=report.last_time,
        )
        return row.apply(report)

    def to_report(self, chart: Chart) -> PnLReport:
        """
        Rebuild the PnLReport of this row so it can be added to another one.
        The chart is given by the caller, only str(chart) is stored here.
        """
        report = PnLReport(
            chart=chart,
            side=PositionSide(self.side),
            source=self.source,
            first_time=self.first_time,
            last_time=self.last_time,
        )
        report.pnl_dollar = self.pnl_dollar
        report.pnl_percent = self.pnl_percent
        report.pnl_pips = self.pnl_pips
        report.volume = self.volume

        report.wins = self.wins
        report.flats = self.flats
        report.loses = self.loses
        report.total_positions = self.total_positions

        report.max_win_in_a_row = self.max_win_in_a_row
        report.max_lose_in_a_row = self.max_lose_in_a_row

        report.triggered_steps = {
            int(step): count
            for step, count in json.loads(self.triggered_steps_json).items()
        }
        report.overall_report = self.overall_report
        return report

    @property
    def win_rate(self) -> float:
        if not self.total_positions:
            return 0.0
        return self.wins / self.total_positions * 100

    def __str__(self) -> str:
        kind = "overall" if self.overall_report else self.identifier
        return (
            f"[{self.id}] {kind} | {self.total_positions} positions "
            f"| {self.pnl_dollar} $ | win rate {self.win_rate:.2f} % "
            f"| until {TimeHandler.to_datetime(self.last_time)}"
        )
