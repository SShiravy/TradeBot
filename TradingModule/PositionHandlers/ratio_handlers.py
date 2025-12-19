from ChartModule.models import MarketSide, Signal
from TradingModule.PositionHandlers.model import PositionHandler
from TradingModule.models import ExchangeAgent, OrderSide, Position
from datetime import timedelta
import logging


logger = logging.getLogger("PositionHandler")


class SlTpRatioCrypto(PositionHandler):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        ratio: float,
        initial_volume: float = 0.5,
        leverage: int = 1,
        stoploss_percent: float = 3,
        long_trade: bool = True,
        short_trade: bool = True,
    ) -> None:
        super().__init__(
            exchange_agent, initial_volume, leverage, long_trade, short_trade
        )
        self.ratio = ratio
        self.stoploss_percent = stoploss_percent

    def init_stoploss(self, entry_price: float, side: OrderSide) -> float:
        return abs(self.stoploss_percent / 100 - side.factor()) * entry_price

    def init_takeprofit(self, entry_price: float, side: OrderSide) -> float:
        return (
            abs(self.stoploss_percent / self.ratio / 100 + side.factor()) * entry_price
        )

    def generate_position(
        self,
        signal: Signal,
        entry_price: float | None = None,
        position_id: str = "",
        sl_tp_base_price: float | None = None,
    ) -> Position:
        real_trade = False
        if signal.side is MarketSide.BEARISH:
            side = OrderSide.SELL
            if self.short_trade:
                real_trade = True
        else:  # signal.side is MarketSide.BULLISH:
            side = OrderSide.BUY
            if self.long_trade:
                real_trade = True
        if entry_price is None:
            entry_price = signal.candle.close

        if sl_tp_base_price is None:
            sl_tp_base_price = entry_price

        percision = signal.chart.precision

        position = Position(
            signal.chart,
            side,
            entry_price,
            self.initial_volume,
            round(self.init_stoploss(sl_tp_base_price, side), percision),
            round(self.init_takeprofit(sl_tp_base_price, side), percision),
            self.leverage,
            signal.candle.time + timedelta(seconds=2),
            signal.source,
            position_id,
            real_trade,
        )
        self.open_positions.append(position)
        logger.info(f"New Position on {position.chart}")
        logger.debug(f"The New Position {position}")
        return position


class SlTpRatioForex(PositionHandler):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        ratio: int,
        initial_volume: float = 0.01,
        stoploss_pip: int = 20,
        long_trade: bool = True,
        short_trade: bool = True,
    ) -> None:
        super().__init__(exchange_agent, initial_volume, 1, long_trade, short_trade)
        self.ratio = ratio
        self.stoploss_pip = stoploss_pip / 10

    def init_stoploss(self, entry_price: float, side: OrderSide) -> float:
        return entry_price - side.factor() * self.stoploss_pip

    def init_takeprofit(self, entry_price: float, side: OrderSide) -> float:
        return entry_price + side.factor() * (self.stoploss_pip / self.ratio)

    def generate_position(
        self,
        signal: Signal,
        entry_price: float | None = None,
        position_id: str = "",
        sl_tp_base_price: float | None = None,
    ) -> Position:
        real_trade = False
        if signal.side is MarketSide.BEARISH:
            side = OrderSide.SELL
            if self.short_trade:
                real_trade = True
        else:  # signal.side is MarketSide.BULLISH:
            side = OrderSide.BUY
            if self.long_trade:
                real_trade = True
        if entry_price is None:
            entry_price = signal.candle.close

        if sl_tp_base_price is None:
            sl_tp_base_price = entry_price

        percision = signal.chart.precision

        position = Position(
            signal.chart,
            side,
            entry_price,
            self.initial_volume,
            round(self.init_stoploss(sl_tp_base_price, side), percision),
            round(self.init_takeprofit(sl_tp_base_price, side), percision),
            self.leverage,
            signal.candle.time + timedelta(seconds=2),
            signal.source,
            position_id,
            real_trade,
        )
        self.open_positions.append(position)
        logger.info(f"New Position on {position.chart}")
        logger.debug(f"The New Position {position}")
        position.in_forex = True
        return position
