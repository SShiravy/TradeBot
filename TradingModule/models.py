from ChartModule import Chart, ChartData, MarketSide, Candle
from ChartModule.plot import PlotChart
from datetime import datetime
from dataclasses import dataclass, field, asdict
from datetime import timezone
from abc import ABC, abstractmethod
from typing import Any
from enum import Enum
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
    chart: Chart
    side: OrderSide
    entry_price: float
    volume: float
    stoploss: float
    takeprofit: float
    leverage: int = 1
    open_time: datetime = field(default=datetime.now(timezone.utc))
    source: str = "Unknown"
    id: uuid.UUID | str = field(default_factory=uuid.uuid4)
    real_trade: bool = field(default=True)

    closed: datetime | None = field(default=None, init=False)
    previous_check: datetime | None = field(default=None, init=False)
    last_update: datetime | None = field(default=None, init=False)
    pnl: float = field(default=0.0, init=False)
    pnl_percent: float = field(default=0, init=False)
    pnl_in_pip: float = field(default=0, init=False)

    def update_pnl(self, executed_price: float, volume: float | None = None):
        """
        calculate pnl based on volume and percent
        if argument volume is None, then whole volume will considered
        """
        if self.volume <= 0:
            return
        volume = self.volume if volume is None or self.volume - volume < 0 else volume
        direction = 1 if self.side is OrderSide.BUY else -1
        self.pnl_percent = round(
            ((executed_price - self.entry_price) * direction / self.entry_price)
            * 100
            * self.leverage,
            2,
        )
        self.pnl = round(self.pnl_percent * volume / 100, 2)
        self.pnl_in_pip += (executed_price - self.entry_price) * direction
        self.volume -= volume

    def __str__(self):
        return f"{asdict(self)}"

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
