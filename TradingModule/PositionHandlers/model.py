from ChartModule import Signal, MarketSide, Chart, TimeFrame
from TradingModule import Position, OrderSide, ExchangeAgent, PositionsReport
from TradingModule.commands import TradeCommand
from TradingModule import commands
from abc import ABC, abstractmethod
from datetime import timedelta
from copy import copy
import numpy as np
import logging


logger = logging.getLogger("PositionHandler")


class PositionHandler(ABC):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        initial_volume: float = 0.0,
        leverage: int = 1,
        long_trade: bool = True,
        short_trade: bool = True,
    ) -> None:
        self.exchange_agent = exchange_agent
        self.initial_volume = initial_volume
        self.leverage = leverage
        self.open_positions: list[Position] = []
        self.closed_positions: list[Position] = []
        self.long_trade: bool = long_trade
        self.short_trade: bool = short_trade

    @abstractmethod
    def init_stoploss(self, entry_price: float, side: OrderSide) -> float:
        pass

    @abstractmethod
    def init_takeprofit(self, entry_price: float, side: OrderSide) -> float:
        pass

    def generate_position(
        self,
        signal: Signal,
        entry_price: float | None = None,
        position_id: str = "",
        *args,
        **kwargs,
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

        percision = signal.chart.precision

        position = Position(
            signal.chart,
            side,
            entry_price,
            self.initial_volume,
            round(self.init_stoploss(entry_price, side), percision),
            round(self.init_takeprofit(entry_price, side), percision),
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

    def handler(
        self, position: Position, tick_prices: list[float]
    ) -> TradeCommand | None:
        direction = position.side.factor()
        ticks = np.array(tick_prices) * direction
        sl = position.stoploss * direction
        tp = position.takeprofit * direction
        cross = np.logical_or(ticks <= sl, ticks >= tp)
        if not cross.any():
            return None
        idx = np.argmax(cross)
        if ticks[idx] <= sl:
            return commands.StopLoss(position, self.exchange_agent)
        else:
            return commands.TakeProfit(position, self.exchange_agent)

    def candles_check(self, position: Position) -> TradeCommand | None:
        ticks = []
        if position.previous_check is None:
            position.previous_check = position.open_time

        m_chart = Chart(position.chart.symbol, TimeFrame.one_minute)
        candles = self.exchange_agent.get_chartdata(m_chart, 3)
        if not candles:
            logger.warning(f"getting candles failed for {position}")
            return
        for candle in candles:
            if candle.time < position.previous_check:
                continue
            ticks += [candle.open, candle.low, candle.high, candle.close]
            position.previous_check = candle.time
        return self.handler(position, ticks)

    def manage_positions(self) -> list[TradeCommand] | None:
        all_commands = []
        all_pos = copy(self.open_positions)
        for pos in all_pos:
            if pos.closed:
                self.closed_positions.append(pos)
                self.open_positions.remove(pos)
                continue
            command = self.candles_check(pos)
            if command:
                all_commands.append(command)
        return all_commands

    def report(self) -> list[PositionsReport]:
        reports = PositionsReport.generate_reports(self.closed_positions)
        self.closed_positions = []
        return reports
