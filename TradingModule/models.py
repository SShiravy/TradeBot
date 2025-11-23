from ChartModule import Chart, ChartData, MarketSide, Candle
from ChartModule.plot import PlotChart
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from datetime import timezone
from typing import Any
from enum import Enum
import hashlib
import json
import uuid


class OrderSide(Enum):
    BUY = "Buy"
    SELL = "Sell"

    @property
    def position_side(self):
        match self:
            case OrderSide.BUY:
                return "Long"
            case OrderSide.SELL:
                return "Short"

    @classmethod
    def from_market_side(cls, market_side: MarketSide):
        match market_side:
            case MarketSide.BEARISH:
                return cls.SELL
            case MarketSide.BULLISH:
                return cls.BUY
            case MarketSide.NEUTRAL:
                return None

    def factor(self):
        return 1 if self is OrderSide.BUY else -1


@dataclass(slots=True)
class Position:
    id: uuid.UUID | str = field(default_factory=uuid.uuid4, init=False)
    chart: Chart
    side: OrderSide
    entry_price: float
    volume: float
    stoploss: float
    takeprofit: float
    leverage: int = 1
    open_time: datetime = field(default=datetime.now(timezone.utc))
    source: str = "Unknown"
    exchange_id: str = field(default="")
    real_trade: bool = field(default=True)

    closed: datetime | None = field(default=None, init=False)
    previous_check: datetime | None = field(default=None, init=False)
    last_update: datetime | None = field(default=None, init=False)
    pnl: float = field(default=0.0, init=False)
    pnl_percent: float = field(default=0.0, init=False)
    in_forex: bool = field(default=False, init=False)
    pnl_in_pip: float = field(default=0.0, init=False)

    def update_pnl(self, executed_price: float, volume: float | None = None):
        """
        calculate pnl based on volume and percent
        if argument volume is None, then whole volume will considered
        """
        if self.volume <= 0:
            return
        volume = self.volume if volume is None or self.volume - volume < 0 else volume
        direction = 1 if self.side is OrderSide.BUY else -1
        if self.in_forex:
            self.pnl += (executed_price - self.entry_price) * direction * volume * 100
            self.pnl_in_pip += (executed_price - self.entry_price) * direction * 10
        else:
            self.pnl_percent += (
                (executed_price - self.entry_price)
                * direction
                / self.entry_price
                * 100
                * self.leverage
            )
            self.pnl += self.pnl_percent * volume / 100
        self.volume -= volume

    def __str__(self):
        return f"{self.side}|{self.source}|{self.chart}|{self.open_time}|{self.entry_price}"

    def __hash__(self):
        raw = json.dumps(
            {
                "chart": str(self.chart),
                "side": self.side.value,
                "time": str(self.open_time.timestamp()),
                "source": self.source,
            },
            sort_keys=True,
        ).encode()
        return int(hashlib.sha256(raw).hexdigest(), 16)

    def draw(self, plot: PlotChart):
        if self.closed:
            plot.draw_sl_tp_lines(
                self.last_update if self.last_update else self.open_time,
                self.closed,
                self.takeprofit,
                self.stoploss,
            )
            if self.last_update:
                end_of_line = self.last_update
            else:
                end_of_line = self.open_time
            plot.draw_line(
                self.open_time,
                self.entry_price,
                end_of_line,
                self.stoploss,
                "#FFD562",
            )
            plot.draw_line(
                self.open_time,
                self.entry_price,
                end_of_line,
                self.takeprofit,
                "#7fff86",
            )
        else:
            start_time = self.open_time - self.chart.timeframe.time_delta * 10
            plot.draw_sl_tp_lines(
                start_time,
                self.open_time,
                self.takeprofit,
                self.stoploss,
            )
        plot.set_y_range((self.stoploss, self.takeprofit))


@dataclass(slots=True)
class PositionsReport:
    chart: Chart
    side: OrderSide
    source: str
    first_time: datetime
    last_time: datetime

    pnl: float = field(default=0.0, init=False)
    pnl_percent: float = field(default=0.0, init=False)
    pnl_in_pip: float | None = field(default=None, init=False)

    spot_pnl: float = field(default=0.0, init=False)
    spot_pnl_percent: float = field(default=0.0, init=False)

    wins: int = field(default=0, init=False)
    flats: int = field(default=0, init=False)
    loses: int = field(default=0, init=False)

    total_positions: int = field(default=1, init=False)

    overal_report: bool = field(default=False, init=False)

    forex_report: bool = field(default=False, init=False)

    @property
    def identifier(self):
        identity = (
            str(self.source)
            + "_"
            + str(self.side.position_side)
            + "_"
            + str(self.chart)
        )
        if self.forex_report:
            identity += "_forex"
        return identity

    def __add__(self, other):
        if isinstance(other, (int, float)):
            return self
        if isinstance(other, PositionsReport):
            if self.forex_report != other.forex_report:
                raise ValueError(
                    f"two report must be on forex or both not: {self.forex_report} and {other.forex_report}"
                )
            first_time = min(self.first_time, other.first_time)
            last_time = max(self.last_time, other.last_time)
            report = PositionsReport(
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

            report.forex_report = self.forex_report

            report.total_positions = self.total_positions + other.total_positions

            if self.identifier != other.identifier:
                report.overal_report = True
            return report

        return NotImplemented

    __radd__ = __add__

    @classmethod
    def generate_position_report(cls, position: Position):
        close_time = position.open_time
        if position.closed:
            close_time = position.closed
        elif position.last_update:
            close_time = position.last_update
        report = cls(
            chart=position.chart,
            side=position.side,
            source=position.source,
            first_time=position.open_time,
            last_time=close_time,
        )

        report.pnl = position.pnl
        report.pnl_percent = position.pnl_percent
        report.spot_pnl = position.pnl / position.leverage
        report.spot_pnl_percent = position.pnl_percent / position.leverage
        if position.in_forex:
            report.pnl_in_pip = position.pnl_in_pip
            report.forex_report = True
        if position.pnl > 0:
            report.wins += 1
        elif position.pnl < 0:
            report.loses += 1
        else:
            report.flats += 1

        return report

    @classmethod
    def generate_reports(cls, all_positions: list[Position]):
        """
        return list of reports with uniqe identifier(chart and side)
        """
        reports_dict: dict[str, PositionsReport] = {}
        for pos in all_positions:
            report = cls.generate_position_report(pos)
            if not reports_dict.get(report.identifier):
                reports_dict[report.identifier] = report
            else:
                reports_dict[report.identifier] += report

        return list(reports_dict.values())

    @classmethod
    def give_overall_report(cls, all_reports: list):
        report = sum(all_reports)
        return report

    def __str__(self) -> str:
        report_msg = [
            f"{self.identifier if not self.overal_report else 'Overall'}",
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
        duration = timedelta(seconds=(self.last_time - self.first_time).seconds)
        report_msg.append(f"Duration = {duration}")
        return "\n".join(report_msg)


class ExchangeAgent(ABC):
    @abstractmethod
    def check_chart(self, chart: Chart) -> bool:
        """
        check symbol exist or not and
        change chart.precision
        """
        pass

    @abstractmethod
    def get_chartdata(self, chart: Chart, n_bars: int = 100) -> ChartData | None:
        pass

    @abstractmethod
    def get_candles_since(self, chart: Chart, time: datetime) -> list[Candle]:
        chartdata = self.get_chartdata(chart, 3)
        if chartdata is None:
            return []
        candles = []
        for candle in chartdata:
            if candle.time < time:
                continue
            candles.append(candle)
        return candles

    @abstractmethod
    def open_position(self, position: Position) -> float | None:
        """
        return executed price if successful otherwise None
        its better to update position id to executed order price
        and position open_time
        """
        pass

    @abstractmethod
    def get_open_positions(self, chart: Chart) -> Any:
        pass

    @abstractmethod
    def change_stoploss(self, position: Position, price: float) -> bool:
        pass

    @abstractmethod
    def change_takeprofit(self, position: Position, price: float) -> bool:
        pass

    @abstractmethod
    def partial_close(self, position: Position, volume: float) -> float | None:
        """
        return executed price if successful otherwise None
        """
        pass

    @abstractmethod
    def close_position(self, position: Position) -> float | None:
        """
        return executed price if successful otherwise None
        """
        pass
