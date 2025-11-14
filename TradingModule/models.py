from ChartModule import Chart, ChartData, MarketSide
from ChartModule.plot import PlotChart
from datetime import datetime
from dataclasses import dataclass, field, asdict
from datetime import timezone
from abc import ABC, abstractmethod
from typing import Any
from enum import Enum


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
    chart: Chart
    side: OrderSide
    entry_price: float
    volume: float
    stoploss: float
    takeprofit: float
    leverage: int = 1
    open_time: datetime = field(default=datetime.now(timezone.utc))
    source: str = "Unknown"
    id: str | None = None

    closed: datetime | None = field(default=None, init=False)
    previous_check: datetime | None = field(default=None, init=False)
    pnl: float = field(default=0.0, init=False)
    pnl_percent: float = field(default=0, init=False)

    def update_pnl(self, executed_price: float, volume: float | None = None):
        """
        calculate pnl based on volume and percent
        if argument volume is None, then whole volume will considered
        """
        if self.volume < 0:
            return
        volume = self.volume if volume is None or self.volume - volume < 0 else volume

        self.pnl_percent = round(
            ((self.entry_price - executed_price) / self.entry_price)
            * 100
            * self.leverage,
            2,
        )
        self.pnl = self.pnl_percent * volume
        self.volume -= volume

    def __str__(self):
        return f"{asdict(self)}"

    def draw(self, plot: PlotChart):
        if self.closed:
            plot.draw_sl_tp_lines(
                self.open_time, self.closed, self.takeprofit, self.stoploss
            )
        else:
            end_time = self.open_time
            start_time = self.open_time - self.chart.timeframe.time_delta * 10
            plot.draw_sl_tp_lines(start_time, end_time, self.takeprofit, self.stoploss)


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
    def get_chartdata_since(self, chart: Chart, time: datetime) -> ChartData | None:
        pass

    @abstractmethod
    def open_position(self, position: Position) -> float | None:
        """
        return executed price if successful otherwise None
        its better to update position id to executed order price
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
