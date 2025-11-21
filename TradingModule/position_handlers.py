from ChartModule import Signal, MarketSide, Chart, TimeFrame
from TradingModule import Position, OrderSide, ExchangeAgent, PositionsReport
from TradingModule.commands import TradeCommand
from TradingModule import commands
from abc import ABC, abstractmethod
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
        self, signal: Signal, entry_price: float | None = None, position_id: str = ""
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
            signal.candle.time,
            signal.source,
            position_id,
            real_trade=real_trade,
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


# Simple ---------------------------------------------


class SimpleCryptoHandler(PositionHandler):
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


class SimpleForexHandler(PositionHandler):
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
        self.stoploss_pip = stoploss_pip
        self.takeprofit_pip = takeprofit_pip

    def init_stoploss(self, entry_price: float, side: OrderSide) -> float:
        return entry_price - side.factor() * self.stoploss_pip

    def init_takeprofit(self, entry_price: float, side: OrderSide) -> float:
        return entry_price + side.factor() * self.takeprofit_pip

    def generate_position(
        self, signal: Signal, entry_price: float | None = None, position_id: str = ""
    ) -> Position:
        pos = super().generate_position(signal, entry_price, position_id)
        pos.in_forex = True
        return pos


# RiskFree---------------------------------------------


class RiskFreeCrypto(SimpleCryptoHandler):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        initial_volume: float = 0.05,
        leverage: int = 1,
        stoploss_percent: float = 5,
        takeprofit_percent: float = 5,
        riskfree_trigger_percent: float = 2,
        long_trade=True,
        short_trade=True,
    ) -> None:
        super().__init__(
            exchange_agent,
            initial_volume,
            leverage,
            stoploss_percent,
            takeprofit_percent,
            long_trade=long_trade,
            short_trade=short_trade,
        )
        self.riskfree_trigger_percent = riskfree_trigger_percent

    def give_trigger_price(self, position: Position) -> float:
        if position.stoploss == position.entry_price:
            # when already riskfree triggered
            return position.takeprofit
        else:
            return (
                abs(self.riskfree_trigger_percent / 100 + position.side.factor())
                * position.entry_price
            )

    def handler(
        self, position: Position, tick_prices: list[float]
    ) -> TradeCommand | None:
        res = super().handler(position, tick_prices)
        if res:
            return res
        direction = position.side.factor()

        ticks = np.array(tick_prices) * direction
        trigger = self.give_trigger_price(position) * direction

        cross = ticks >= trigger

        if cross.any():
            return commands.TrailStoploss(
                position, self.exchange_agent, position.entry_price
            )


class RiskFreeForex(SimpleForexHandler):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        initial_volume: float = 0.01,
        stoploss_pip: int = 20,
        takeprofit_pip: int = 20,
        riskfree_trigger_pip: int = 10,
        long_trade: bool = True,
        short_trade: bool = True,
    ) -> None:
        super().__init__(
            exchange_agent,
            initial_volume,
            stoploss_pip,
            takeprofit_pip,
            long_trade,
            short_trade,
        )
        self.riskfree_trigger_pip = riskfree_trigger_pip

    def give_trigger_price(self, position: Position) -> float:
        if position.stoploss == position.entry_price:
            # when already riskfree triggered
            return position.takeprofit
        else:
            return (
                self.riskfree_trigger_pip * position.side.factor()
                + position.entry_price
            )

    def handler(
        self, position: Position, tick_prices: list[float]
    ) -> TradeCommand | None:
        direction = position.side.factor()
        res = super().handler(position, tick_prices)
        if res:
            return res
        direction = position.side.factor()

        ticks = np.array(tick_prices) * direction
        trigger = self.give_trigger_price(position) * direction

        cross = ticks >= trigger

        if cross.any():
            return commands.TrailStoploss(
                position, self.exchange_agent, position.entry_price
            )


# Seperate Short Long tp sl ----------------------------------


class LongShortCryptoHandler(RiskFreeCrypto):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        initial_volume: float = 0.05,
        leverage: int = 1,
        long_stoploss_percent: float = 5,
        long_takeprofit_percent: float = 5,
        long_riskfree_trigger_percent: float = 2,
        short_stoploss_percent: float = 5,
        short_takeprofit_percent: float = 5,
        short_riskfree_trigger_percent: float = 2,
        long_trade=True,
        short_trade=True,
    ) -> None:
        super().__init__(
            exchange_agent,
            initial_volume,
            leverage,
            long_trade=long_trade,
            short_trade=short_trade,
        )

        self.long_stoploss_percent = long_stoploss_percent
        self.long_takeprofit_percent = long_takeprofit_percent
        self.long_riskfree_trigger_percent = long_riskfree_trigger_percent

        self.short_stoploss_percent = short_stoploss_percent
        self.short_takeprofit_percent = short_takeprofit_percent
        self.short_riskfree_trigger_percent = short_riskfree_trigger_percent

    def init_stoploss(self, entry_price: float, side: OrderSide) -> float:
        if side is OrderSide.BUY:
            return abs(self.long_stoploss_percent / 100 - 1) * entry_price
        else:
            return abs(self.short_stoploss_percent / 100 + 1) * entry_price

    def init_takeprofit(self, entry_price: float, side: OrderSide) -> float:
        if side is OrderSide.BUY:
            return abs(self.long_takeprofit_percent / 100 + 1) * entry_price
        else:
            return abs(self.short_takeprofit_percent / 100 - 1) * entry_price

    def give_trigger_price(self, position: Position) -> float:
        if position.stoploss == position.entry_price:
            # when already riskfree triggered
            return position.takeprofit
        if position.side is OrderSide.BUY:
            return (
                abs(self.long_riskfree_trigger_percent / 100 + 1) * position.entry_price
            )
        else:
            return (
                abs(self.short_riskfree_trigger_percent / 100 - 1)
                * position.entry_price
            )


class LongShortForexHandler(RiskFreeForex):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        initial_volume: float = 0.01,
        long_stoploss_pip: int = 20,
        long_takeprofit_pip: int = 20,
        long_riskfree_trigger_pip: int = 10,
        short_stoploss_pip: int = 20,
        short_takeprofit_pip: int = 20,
        short_riskfree_trigger_pip: int = 10,
        long_trade: bool = True,
        short_trade: bool = True,
    ) -> None:
        super().__init__(
            exchange_agent,
            initial_volume,
            long_trade,
            short_trade,
        )
        self.long_stoploss_pip = long_stoploss_pip
        self.long_takeprofit_pip = long_takeprofit_pip
        self.long_riskfree_trigger_pip = long_riskfree_trigger_pip

        self.short_stoploss_pip = short_stoploss_pip
        self.short_takeprofit_pip = short_takeprofit_pip
        self.short_riskfree_trigger_pip = short_riskfree_trigger_pip

    def init_stoploss(self, entry_price: float, side: OrderSide) -> float:
        if side is OrderSide.BUY:
            return entry_price - self.long_stoploss_pip
        else:
            return entry_price + self.short_stoploss_pip

    def init_takeprofit(self, entry_price: float, side: OrderSide) -> float:
        if side is OrderSide.BUY:
            return entry_price + self.long_takeprofit_pip
        else:
            return entry_price - self.short_takeprofit_pip

    def give_trigger_price(self, position: Position) -> float:
        if position.stoploss == position.entry_price:
            # when already riskfree triggered
            return position.takeprofit
        if position.side is OrderSide.BUY:
            return position.entry_price + self.long_riskfree_trigger_pip
        else:
            return position.entry_price - self.short_riskfree_trigger_pip
