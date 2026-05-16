from typing import Optional
from sqlmodel import SQLModel, Field
import json
from LocalBackTester.Database.hashing import generate_hash
from TradingModule.PositionHandlers.model import PositionHandler
from TradingModule.models import PositionsReport


class PositionsResult(SQLModel, table=True):
    __tablename__ = "Positions_Result"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)

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

    handler_hash: str = Field(index=True, unique=True)
    handler_config_json: str

    commands_report: str

    source: int = Field(foreign_key="Divergence_Backtests.id", index=True)

    @classmethod
    def give_handler_hash(cls, handler: PositionHandler):
        conf_dict = handler.export_config()
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
            handler_hash=cls.give_handler_hash(handler),
            handler_config_json=json.dumps(handler.export_config()),
            commands_report=commands_report,
            source=backtest_source,
        )

        return datapoint
