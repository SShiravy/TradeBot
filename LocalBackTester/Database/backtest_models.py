from datetime import timedelta
from sqlmodel import SQLModel, Field
import json
from LocalBackTester.Database.hashing import generate_hash
from TradingModule.PositionHandlers.model import PositionHandler
from TradingModule.models import PositionsReport


class PositionsResult(SQLModel, table=True):
    __tablename__ = "Positions_Result"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)

    pnl: float = Field(default=0.0)
    pnl_percent: float = Field(default=0.0)
    pnl_in_pip: float | None = Field(default=None)

    spot_pnl: float = Field(default=0.0)
    spot_pnl_percent: float = Field(default=0.0)

    wins: int = Field(default=0)
    flats: int = Field(default=0)
    loses: int = Field(default=0)

    max_win_in_a_row: int = Field(default=0)
    max_lose_in_a_row: int = Field(default=0)

    number_of_positions: int = Field(default=1)
    duration: timedelta

    handler_hash: str = Field(index=True, unique=True)
    handler_config_json: str

    commands_report: str

    source: int = Field(foreign_key="Divergence_Backtests.id", index=True)

    @classmethod
    def give_handler_hash(cls, handler: PositionHandler, backtest_source: int):
        conf_dict = handler.export_config()
        conf_dict["backtest_source"] = backtest_source
        return generate_hash(conf_dict)

    @classmethod
    def generate_datapoint(
        cls, handler: PositionHandler, commands_report: str, backtest_source: int
    ):
        if handler.closed_positions == []:
            raise ValueError(
                f"handler with empty closed position list. {handler.export_config()}"
            )

        all_reports = handler.report(flush=False)
        report = PositionsReport.give_overall_report(all_reports)
        report.calculate_max_win_lose_in_row(handler.closed_positions)
        datapoint = PositionsResult(
            pnl=round(report.pnl, 2),
            pnl_percent=round(report.pnl_percent, 2),
            pnl_in_pip=round(report.pnl_in_pip, 2)
            if report.pnl_in_pip
            else report.pnl_in_pip,
            spot_pnl=round(report.spot_pnl, 4),
            spot_pnl_percent=round(report.spot_pnl_percent, 2),
            wins=report.wins,
            flats=report.flats,
            loses=report.loses,
            max_lose_in_a_row=report.max_lose_in_a_row,
            max_win_in_a_row=report.max_win_in_a_row,
            number_of_positions=report.total_positions,
            duration=report.calculate_duration(),
            handler_hash=cls.give_handler_hash(handler, backtest_source),
            handler_config_json=json.dumps(handler.export_config()),
            commands_report=commands_report,
            source=backtest_source,
        )

        return datapoint

    def __str__(self) -> str:
        report_msg = [
            f"DB_id = {self.id}",
            f"Total Positions = {self.number_of_positions}",
            f"Wins = {self.wins}",
            f"Loses = {self.loses}",
            f"Flats = {self.flats}",
            f"PNL = {round(self.pnl, 2)} $",
        ]
        if self.pnl_in_pip is not None:
            report_msg.append(f"PNL in pip = {round(self.pnl_in_pip, 2)}")
        else:
            report_msg.append(f"pnl percent = {round(self.pnl_percent, 2)} %")
            report_msg.append(f"Spot PNL = {round(self.spot_pnl, 4)} $")
            report_msg.append(f"spot pnl percent = {round(self.spot_pnl_percent, 2)} %")

        if (self.wins + self.loses) != 0:
            report_msg.append(
                f"Win Rate = {round(self.wins / (self.wins + self.loses) * 100, 2)} %"
            )

        if self.max_lose_in_a_row or self.max_win_in_a_row:
            report_msg.append(f"Max Win in a Row = {self.max_win_in_a_row}")
            report_msg.append(f"Max Lose in a Row = {self.max_lose_in_a_row}")

        report_msg.append(f"\n{self.commands_report}\n")
        report_msg.append(f"Duration = {self.duration}")
        return "\n".join(report_msg)
