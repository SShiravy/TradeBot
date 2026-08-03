from ChartModule import Signal, MarketSide, Chart, TimeFrame
from ChartModule.plot import Plot
from TradingModule import Position, OrderSide, ExchangeAgent, PositionsReport
from TradingModule.PositionHandlers.trading_constraints import TradingConstraint
from TradingModule.commands import TradeCommand
from TradingModule import commands
from abc import ABC, abstractmethod
from datetime import timedelta
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
        trading_constraints: list[TradingConstraint] = [],
        send_report: bool = True,
    ) -> None:
        self.exchange_agent = exchange_agent
        self.initial_volume = initial_volume
        self.leverage = leverage
        self.open_positions: list[Position] = []
        self.closed_positions: list[Position] = []
        self.long_trade: bool = long_trade
        self.short_trade: bool = short_trade
        self.trading_constraints = trading_constraints
        self.send_report = send_report

    @abstractmethod
    def init_stoploss(self, entry_price: float, side: OrderSide, chart: Chart) -> float:
        pass

    @abstractmethod
    def init_takeprofit(
        self, entry_price: float, side: OrderSide, *args, **kwargs
    ) -> float:
        pass

    @abstractmethod
    def export_config(self) -> dict:
        return {
            "Handler": self.__class__.__name__,
            "initial_volume": self.initial_volume,
            "leverage": self.leverage,
            "long_trade": self.long_trade,
            "short_trade": self.short_trade,
            "constraints": [c.export_config() for c in self.trading_constraints],
        }

    async def generate_position(
        self,
        signal: Signal,
        entry_price: float | None = None,
        plot: Plot | None = None,
        *args,
        **kwargs,
    ) -> Position | None:
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

        position = Position(
            signal.chart,
            side,
            entry_price,
            self.initial_volume,
            self.init_stoploss(entry_price, side, signal.chart),
            self.init_takeprofit(entry_price, side, signal.chart),
            self.leverage,
            signal.candle.time + timedelta(seconds=2),
            signal.source,
            real_trade,
            plot=plot,
        )
        await commands.OpenPosition(position, self.exchange_agent).execute()
        self.open_positions.append(position)
        if not real_trade:
            position.confiremed = True

        logger.info(f"New Position on {position.chart}")
        logger.debug(f"The New Position {position}")
        return position

    def modify_init_sl_tp(self, position: Position):
        sl = self.init_stoploss(position.entry_price, position.side, position.chart)
        if sl != position.stoploss:
            position.stoploss = sl
            commands.TrailStoploss(position, self.exchange_agent, sl, report=False)
        tp = self.init_takeprofit(position.entry_price, position.side)
        if tp != position.takeprofit:
            position.takeprofit = tp
            commands.ChangeTakeProfit(position, self.exchange_agent, tp, report=False)
        position.confiremed = True
        logger.info(f"Position Updated on {position.chart}")

    def handler(
        self, position: Position, tick_prices: list[float]
    ) -> TradeCommand | None:
        if not position.confiremed:
            self.modify_init_sl_tp(position)
        if position.confiremed and not position.sended:
            commands.SendPositionSignal(
                position, self.exchange_agent, report=self.send_report
            )
        direction = position.side.factor()
        ticks = np.array(tick_prices) * direction
        sl = position.stoploss * direction
        tp = position.takeprofit * direction
        cross = np.logical_or(ticks <= sl, ticks >= tp)
        if not cross.any():
            return None
        idx = np.argmax(cross)
        if ticks[idx] <= sl:
            return commands.StopLoss(
                position, self.exchange_agent, report=self.send_report
            )
        else:
            return commands.TakeProfit(
                position, self.exchange_agent, report=self.send_report
            )

    def candles_check(self, position: Position) -> TradeCommand | None:
        ticks = []
        if position.previous_check is None:
            position.previous_check = position.start_time

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

    def manage_positions(self):
        all_pos = self.open_positions.copy()
        for pos in all_pos:
            if pos.closed:
                self.closed_positions.append(pos)
                self.open_positions.remove(pos)
                continue
            self.candles_check(pos)

    def report(self, flush: bool = True) -> list[PositionsReport]:
        reports = PositionsReport.generate_reports(self.closed_positions)
        if flush:
            self.closed_positions = []
        return reports
