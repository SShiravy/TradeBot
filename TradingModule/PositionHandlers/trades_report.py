
from copy import copy
from dataclasses import dataclass, field
from datetime import timedelta
from ChartModule.models import Chart
from ChartModule.timing import TimeHandler
from TradingModule.models import Position, PositionSide


@dataclass(slots=True)
class TradesReport:
    chart: Chart
    side: PositionSide
    source: str
    first_time: int
    last_time: int

    pnl: float = field(default=0.0, init=False)
    pnl_percent: float = field(default=0.0, init=False)
    pnl_in_pip: float | None = field(default=None, init=False)

    spot_pnl: float = field(default=0.0, init=False)
    spot_pnl_percent: float = field(default=0.0, init=False)

    wins: int = field(default=0, init=False)
    flats: int = field(default=0, init=False)
    loses: int = field(default=0, init=False)

    triggered_steps: dict = field(default_factory=dict, init=False)

    max_win_in_a_row: int = field(default=0, init=False)
    max_lose_in_a_row: int = field(default=0, init=False)

    total_positions: int = field(default=1, init=False)

    overal_report: bool = field(default=False, init=False)

    forex_report: bool = field(default=False, init=False)

    @property
    def identifier(self):
        identity = (
            str(self.source)
            + "_"
            + str(self.side)
            + "_"
            + str(self.chart)
        )
        if self.forex_report:
            identity += "_forex"
        return identity

    def __add__(self, other):
        if isinstance(other, (int, float)):
            return self
        if isinstance(other, TradesReport):
            if self.forex_report != other.forex_report:
                raise ValueError(
                    f"two report must be on forex or both not: {self.forex_report} and {other.forex_report}"
                )
            first_time = min(self.first_time, other.first_time)
            last_time = max(self.last_time, other.last_time)
            report = TradesReport(
                self.chart, self.side, self.source, first_time, last_time
            )
            report.pnl = self.pnl + other.pnl
            report.pnl_percent = self.pnl_percent + other.pnl_percent
            report.spot_pnl = self.spot_pnl + other.spot_pnl
            report.spot_pnl_percent = self.spot_pnl_percent + other.spot_pnl_percent
            if self.pnl_in_pip is not None and other.pnl_in_pip is not None:
                report.pnl_in_pip = self.pnl_in_pip + other.pnl_in_pip

            report.wins = self.wins + other.wins
            report.flats = self.flats + other.flats
            report.loses = self.loses + other.loses

            for k, v in self.triggered_steps.items():
                self.triggered_steps[k] += other.triggered_steps.get(k, 0)
            other.triggered_steps.update(self.triggered_steps)
            report.triggered_steps = copy(other.triggered_steps)

            report.forex_report = self.forex_report

            report.total_positions = self.total_positions + other.total_positions

            if self.identifier != other.identifier:
                report.overal_report = True
            return report

        return NotImplemented

    __radd__ = __add__

    @classmethod
    def generate_position_report(cls, position: Position):
        close_time = position.defined_timestamp
        if position.closed_timestamp:
            close_time = position.closed_timestamp
        elif position.last_check_timestamp:
            close_time = position.last_check_timestamp
        report = cls(
            chart=position.chart,
            side=position.side,
            source=position.source,
            first_time=position.defined_timestamp,
            last_time=close_time,
        )

        report.pnl = position.pnl_dollar
        report.pnl_percent = position.pnl_percent
        report.spot_pnl = position.pnl_dollar / position.leverage
        report.spot_pnl_percent = position.pnl_percent / position.leverage
        if position.in_forex:
            report.pnl_in_pip = position.pnl_in_pip
            report.forex_report = True
        if position.pnl_dollar > 0:
            report.wins += 1
        elif position.pnl_dollar < 0:
            report.loses += 1
        else:
            report.flats += 1
        if len(position.steps) > 1:
            for i, step in enumerate(position.steps[1:]):
                if step.triggered_timestamp:
                    report.triggered_steps[i] = report.triggered_steps.get(i, 0) + 1

        return report

    def calculate_max_win_lose_in_row(self, all_positions: list[Position]):
        all_pos = all_positions.copy()
        all_pos.sort(
            key=lambda pos: pos.closed_timestamp
            if pos.closed_timestamp
            else TimeHandler.now()
        )
        win_in_a_row = 0
        lose_in_a_row = 0
        for pos in all_pos:
            if pos.pnl_dollar > 0:
                win_in_a_row += 1
                self.max_lose_in_a_row = max(self.max_lose_in_a_row, lose_in_a_row)
                self.max_win_in_a_row = max(self.max_win_in_a_row, win_in_a_row)
                lose_in_a_row = 0

            elif pos.pnl_dollar < 0:
                lose_in_a_row += 1
                self.max_lose_in_a_row = max(self.max_lose_in_a_row, lose_in_a_row)
                self.max_win_in_a_row = max(self.max_win_in_a_row, win_in_a_row)
                win_in_a_row = 0

    @classmethod
    def generate_reports(cls, all_positions: list[Position]):
        """
        return list of reports with uniqe identifier(chart and side)
        """
        reports_dict: dict[str, TradesReport] = {}
        for pos in all_positions:
            report = cls.generate_position_report(pos)
            if not reports_dict.get(report.identifier):
                reports_dict[report.identifier] = report
            else:
                reports_dict[report.identifier] += report

        return list(reports_dict.values())

    @classmethod
    def give_overall_report(cls, all_reports: list) -> "TradesReport":
        report = sum(all_reports)
        return report  # type: ignore

    def calculate_duration(self):
        duration = timedelta(
            seconds=int(self.last_time) - int(self.first_time)
        )
        return duration

    def __str__(self) -> str:
        report_msg = [
            f"{self.identifier if not self.overal_report else f'Overall {self.source} on {self.chart.symbol}'}",
            f"Total Positions = {self.total_positions}",
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

        if self.triggered_steps:
            report_msg.append("Number of Triggered Steps:")
            for k, v in self.triggered_steps.items():
                count = v - self.triggered_steps.get(k + 1, 0)
                report_msg.append(
                    f"  TP_{k + 1} : {count} | {round(v / self.total_positions * 100, 2)}%"
                )
        if self.max_lose_in_a_row or self.max_win_in_a_row:
            report_msg.append(f"Max Win in a Row = {self.max_win_in_a_row}")
            report_msg.append(f"Max Lose in a Row = {self.max_lose_in_a_row}")

        duration = self.calculate_duration()
        report_msg.append(f"Duration = {duration}")
        return "\n".join(report_msg)

