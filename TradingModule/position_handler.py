from ChartModule import Signal, MarketSide, ChartData
from TradingModule import Position, OrderSide, ExchangeAgent
from TradingModule.commands import TradeCommand, StopLoss, TakeProfit
from abc import ABC, abstractmethod
import numpy as np
import logging


logger = logging.getLogger("PositionHandler")


class PositionHandler(ABC):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        initial_volume: float = 0.0,
        leverage: int = 1,
    ) -> None:
        self.exchange_agent = exchange_agent
        self.initial_volume = initial_volume
        self.leverage = leverage
        self.open_positions: list[Position] = []
        self.closed_positions: list[Position] = []

    @abstractmethod
    def init_stoploss(self, entry_price: float, side: OrderSide) -> float:
        pass

    @abstractmethod
    def init_takeprofit(self, entry_price: float, side: OrderSide) -> float:
        pass

    @abstractmethod
    def generate_position(
        self, signal: Signal, entry_price: float | None = None, position_id: str = ""
    ) -> Position | None:
        if signal.side is MarketSide.BEARISH:
            side = OrderSide.SELL
        elif signal.side is MarketSide.BULLISH:
            side = OrderSide.BUY
        else:
            return None

        if entry_price is None:
            entry_price = signal.candle.close

        percision = signal.chart.precision

        position = Position(
            signal.chart,
            side,
            entry_price,
            self.initial_volume,
            round(self.init_stoploss(entry_price, side), percision),
            round(self.init_takeprofit(entry_price, side), percision),
            self.leverage,
            signal.candle.time,
            signal.source,
            position_id,
        )
        self.open_positions.append(position)
        return position

    @abstractmethod
    def handler(
        self, position: Position, tick_prices: list[float]
    ) -> TradeCommand | None:
        """
        every tick price after position.previous_check
        all logic of Position Handlers will develop here
        """
        pass

    def chartdata_check(
        self, chartdata: ChartData, position: Position
    ) -> TradeCommand | None:
        if not position.previous_check:
            return None
        ticks = []
        for candle in chartdata:
            if candle.time < position.previous_check:
                continue
            ticks += [candle.open, candle.low, candle.high, candle.close]
            position.previous_check = chartdata.candles[-1].time
        return self.handler(position, ticks)

    def manage_positions(self) -> list[TradeCommand] | None:
        all_commands = []
        symbol_chartdata_dict: dict[str, ChartData] = {}
        for pos in self.open_positions:
            if pos.closed:
                self.closed_positions.append(pos)
                self.open_positions.remove(pos)
                continue
            if not pos.previous_check and pos.open_time:
                pos.previous_check = pos.open_time
            else:
                logger.warning(f"Position Doesn't have any time: {pos}")
                continue
            if not symbol_chartdata_dict.get(pos.chart.symbol):
                chartdata = self.exchange_agent.get_chartdata_since(
                    pos.chart, pos.previous_check
                )
                if not chartdata:
                    logger.error(f"getting chartdata failed for {pos=}")
                    continue
                symbol_chartdata_dict[pos.chart.symbol] = chartdata

            command = self.chartdata_check(symbol_chartdata_dict[pos.chart.symbol], pos)
            if command:
                all_commands.append(command)
        return all_commands


class SimpleCryptoHandler(PositionHandler):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        initial_volume: float = 0,
        leverage: int = 1,
        stoploss_percent: int = 5,
        takeprofit_percent: int = 5,
    ) -> None:
        super().__init__(exchange_agent, initial_volume, leverage)
        self.stoploss_percent = stoploss_percent
        self.takeprofit_percent = takeprofit_percent

    def init_stoploss(self, entry_price: float, side: OrderSide) -> float:
        return abs(self.stoploss_percent / 100 - side.direction) * entry_price

    def init_takeprofit(self, entry_price: float, side: OrderSide) -> float:
        return abs(self.takeprofit_percent / 100 + side.direction) * entry_price

    def handler(
        self, position: Position, tick_prices: list[float]
    ) -> TradeCommand | None:
        direction = position.side.direction
        ticks = np.array(tick_prices) * direction
        sl = position.stoploss * direction
        tp = position.takeprofit * direction
        cross = np.logical_or(ticks <= sl, ticks >= tp)
        if not cross.any():
            result = None
        idx = np.argmax(cross)
        if ticks[idx] <= position.stoploss:
            result = StopLoss(position)
        else:
            result = TakeProfit(position)
        return result


class SimpleForexHandler(PositionHandler):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        initial_volume: float = 0,
        leverage: int = 1,
        stoploss_pip: int = 20,
        takeprofit_pip: int = 20,
    ) -> None:
        super().__init__(exchange_agent, initial_volume, leverage)
        self.stoploss_pip = stoploss_pip
        self.takeprofit_pip = takeprofit_pip

    def init_stoploss(self, entry_price: float, side: OrderSide) -> float:
        return entry_price - side.direction * self.stoploss_pip

    def init_takeprofit(self, entry_price: float, side: OrderSide) -> float:
        return entry_price + side.direction * self.takeprofit_pip

    def handler(
        self, position: Position, tick_prices: list[float]
    ) -> TradeCommand | None:
        direction = position.side.direction
        ticks = np.array(tick_prices) * direction
        sl = position.stoploss * direction
        tp = position.takeprofit * direction
        cross = np.logical_or(ticks <= sl, ticks >= tp)
        if not cross.any():
            result = None
        idx = np.argmax(cross)
        if ticks[idx] <= position.stoploss:
            result = StopLoss(position)
        else:
            result = TakeProfit(position)
        return result
