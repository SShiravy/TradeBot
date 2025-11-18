from ChartModule import Signal, MarketSide, Candle
from TradingModule import Position, OrderSide, ExchangeAgent
from TradingModule.commands import TradeCommand
from TradingModule import commands
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from copy import copy
import numpy as np
import logging


logger = logging.getLogger("PositionHandler")


@dataclass(slots=True)
class PositionsReport:
    total_closed_position: int
    total_open_positions: int
    long_zero_pnl: int
    short_zero_pnl: int
    long_win: int
    long_lose: int
    short_win: int
    short_lose: int
    pnl: float
    pnl_percent: float
    spot_pnl: float
    spot_pnl_percent: float
    total_pip: float | None = field(default=None, init=False)

    def __str__(self) -> str:
        doc = [
            f"{self.total_closed_position} Closed Position",
            f"{self.total_open_positions} position still open",
            f"Long: {self.long_win} Win & {self.long_lose} Lose & {self.long_zero_pnl} Flat",
            f"Short: {self.short_win} Win & {self.short_lose} Lose & {self.short_zero_pnl} Flat",
            f"PNL = {round(self.pnl, 4)}",
            f"PNL% = {round(self.pnl_percent, 4)}",
            f"Spot PNL = {round(self.spot_pnl, 4)}",
            f"Spot PNL% = {round(self.spot_pnl_percent, 4)}",
        ]
        if self.total_pip:
            doc.append(f"Total pip: {round(self.total_pip, 2)}")
        return "\n".join(doc)


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

    def candles_check(
        self, candles: list[Candle], position: Position
    ) -> TradeCommand | None:
        if not position.previous_check:
            return None
        ticks = []
        for candle in candles:
            if position.previous_check is None:
                position.previous_check = position.open_time
            if candle.time < position.previous_check:
                continue
            ticks += [candle.open, candle.low, candle.high, candle.close]
            position.previous_check = candle.time
        return self.handler(position, ticks)

    def manage_positions(self) -> list[TradeCommand] | None:
        all_commands = []
        symbol_candles_dict: dict[str, list[Candle]] = {}
        all_pos = copy(self.open_positions)
        for pos in all_pos:
            if pos.closed:
                self.closed_positions.append(pos)
                self.open_positions.remove(pos)
                continue
            if not pos.previous_check:
                pos.previous_check = pos.open_time

            if not symbol_candles_dict.get(pos.chart.symbol):
                candles = self.exchange_agent.get_candles_since(
                    pos.chart, pos.previous_check
                )
                if not candles:
                    logger.warning(f"getting candles failed for {pos=}")
                    continue
                symbol_candles_dict[pos.chart.symbol] = candles

            command = self.candles_check(symbol_candles_dict[pos.chart.symbol], pos)
            if command:
                all_commands.append(command)
        return all_commands

    def report(self) -> PositionsReport:
        total_pnl = 0.0
        total_pnl_percent = 0.0
        total_spot_pnl = 0.0
        total_spot_pnl_percent = 0.0
        win_long_pos = 0
        win_short_pos = 0
        lose_long_pos = 0
        lose_short_pos = 0
        zero_pnl_long = 0
        zero_pnl_short = 0
        for pos in self.closed_positions:
            total_pnl += pos.pnl
            total_pnl_percent += pos.pnl_percent
            total_spot_pnl += pos.pnl / pos.leverage
            total_spot_pnl_percent += pos.pnl_percent / pos.leverage
            if pos.side is OrderSide.BUY:
                if pos.pnl > 0:
                    win_long_pos += 1
                elif pos.pnl < 0:
                    lose_long_pos += 1
                else:
                    zero_pnl_long += 1

            else:
                if pos.pnl > 0:
                    win_short_pos += 1
                elif pos.pnl < 0:
                    lose_short_pos += 1
                else:
                    zero_pnl_short += 1

        report = PositionsReport(
            len(self.closed_positions),
            len(self.open_positions),
            zero_pnl_long,
            zero_pnl_short,
            win_long_pos,
            lose_long_pos,
            win_short_pos,
            lose_short_pos,
            total_pnl,
            total_pnl_percent,
            total_spot_pnl,
            total_spot_pnl_percent,
        )
        self.closed_positions = []
        return report


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

    def report(self):
        total_pip = 0
        for pos in self.closed_positions:
            total_pip += pos.pnl_in_pip
        report = super().report()
        report.total_pip = total_pip
        return report


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
