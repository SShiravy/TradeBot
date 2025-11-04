from ChartModule import Chart, ChartData, MarketSide
from datetime import datetime
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
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


class ExchangeAgent(ABC):
    @abstractmethod
    def get_chartdata(self, chart: Chart, n_bars: int = 100) -> ChartData | None:
        pass

    @abstractmethod
    def open_position(self, position: Position)->str|None:
        """
        return position id if successful otherwise None
        its better to update position.entry_price to executed order price
        """
        pass

    @abstractmethod
    def get_open_positions(self, chart: Chart):
        pass

    @abstractmethod
    def change_stoploss(self, position: Position, price) -> bool:
        pass

    @abstractmethod
    def change_takeprofit(self, position: Position, price) -> bool:
        pass

    @abstractmethod
    def partial_close(self, position: Position, volume) -> float|None:
        """
        return executed price if successful otherwise None
        """
        pass

    @abstractmethod
    def close_position(self, position: Position)->float|None:
        """
        return executed price if successful otherwise None
        """
        pass
