from ChartModule import Candle, Chart, ChartData
from datetime import datetime
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
from enum import Enum


class OrderSide(Enum):
    BUY = "Buy"
    SELL = "Sell"

    @property
    def position(self):
        match self:
            case OrderSide.BUY:
                return "Long"
            case OrderSide.SELL:
                return "Short"


@dataclass(slots=True)
class Signal:
    chart: Chart
    candle: Candle
    side: OrderSide
    source: str = "Unknown"

    def __str__(self) -> str:
        return f"{self.chart} {self.side} at {self.candle.time} from {self.source}"


@dataclass(slots=True)
class Position:
    chart: Chart
    side: OrderSide
    entry_price: float
    volume: float
    stoploss: float
    takeprofit: float
    leverage: int = 1
    open_time: datetime | None = field(default=None)
    source: str = "Unknown"
    id = None

    closed: datetime | None = field(default=None, init=False)
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
            (self.entry_price / executed_price - 1) * 100 * self.leverage, 2
        )
        self.pnl = self.pnl * volume
        self.volume -= volume

    def __str__(self):
        return f"{asdict(self)}"


class ExchangeAPI(ABC):
    @abstractmethod
    def give_chartdata(self, chart: Chart, n_bars: int = 100) -> ChartData:
        pass

    @abstractmethod
    def open_position(self, position: Position):
        """
        return position id if successful otherwise None
        its better to update position.entry_price to executed order price
        """
        pass

    @abstractmethod
    def give_open_orders(self, chart: Chart):
        pass

    @abstractmethod
    def change_stoploss(self, position: Position, price) -> bool:
        pass

    @abstractmethod
    def change_takeprofit(self, position: Position, price) -> bool:
        pass

    @abstractmethod
    def partial_close(self, position: Position, volume):
        """
        return executed price if successful otherwise None
        """
        pass

    @abstractmethod
    def close_position(self, position: Position):
        """
        return executed price if successful otherwise None
        """
        pass
