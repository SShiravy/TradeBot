from ChartModule.models import Signal
from TradingModule.PositionHandlers.model import PositionHandler
from TradingModule.models import ExchangeAgent, OrderSide, Position


class SimpleCrypto(PositionHandler):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        initial_volume: float = 0.5,
        leverage: int = 1,
        stoploss_percent: float = 5,
        takeprofit_percent: float = 5,
        long_trade: bool = True,
        short_trade: bool = True,
    ) -> None:
        super().__init__(
            exchange_agent, initial_volume, leverage, long_trade, short_trade
        )
        self.stoploss_percent = stoploss_percent
        self.takeprofit_percent = takeprofit_percent

    def init_stoploss(self, entry_price: float, side: OrderSide) -> float:
        return abs(self.stoploss_percent / 100 - side.factor()) * entry_price

    def init_takeprofit(self, entry_price: float, side: OrderSide) -> float:
        return abs(self.takeprofit_percent / 100 + side.factor()) * entry_price


class SimpleForex(PositionHandler):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        initial_volume: float = 0.01,
        stoploss_pip: int = 20,
        takeprofit_pip: int = 20,
        long_trade: bool = True,
        short_trade: bool = True,
    ) -> None:
        super().__init__(exchange_agent, initial_volume, 1, long_trade, short_trade)
        self.stoploss_pip = stoploss_pip / 10
        self.takeprofit_pip = takeprofit_pip / 10

    def init_stoploss(self, entry_price: float, side: OrderSide) -> float:
        return entry_price - side.factor() * self.stoploss_pip

    def init_takeprofit(self, entry_price: float, side: OrderSide) -> float:
        return entry_price + side.factor() * self.takeprofit_pip

    def generate_position(
        self,
        signal: Signal,
        entry_price: float | None = None,
        position_id: str = "",
        *args,
        **kwargs,
    ) -> Position:
        pos = super().generate_position(
            signal, entry_price, position_id, kwargs=kwargs, args=args
        )
        pos.in_forex = True
        return pos
