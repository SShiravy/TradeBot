import numpy as np
from ChartModule.models import MarketSide, Signal
from ChartModule.plot import Plot
from TradingModule import commands
from TradingModule.PositionHandlers.model import PositionHandler
from TradingModule.commands import TradeCommand
from TradingModule.models import ExchangeAgent, OrderSide, Position, Trigger
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
        riskfree_trigger_ratio: float = 0.0,
        long_trade: bool = True,
        short_trade: bool = True,
    ) -> None:
        super().__init__(
            exchange_agent, initial_volume, leverage, long_trade, short_trade
        )
        self.ratio = ratio
        self.stoploss_percent = stoploss_percent
        self.riskfree_trigger_ratio = riskfree_trigger_ratio

    def export_config(self) -> dict:
        conf_dict = super().export_config()
        conf_dict.update(
            {
                "ratio": self.ratio,
                "riskfree_trigger_ratio": self.riskfree_trigger_ratio,
                "stoploss_percent": self.stoploss_percent,
            }
        )
        return conf_dict

    def init_stoploss(self, entry_price: float, side: OrderSide) -> float:
        return abs(self.stoploss_percent / 100 - side.factor()) * entry_price

    def init_takeprofit(self, entry_price: float, side: OrderSide) -> float:
        return (
            abs(self.stoploss_percent * self.ratio / 100 + side.factor()) * entry_price
        )

    def set_riskfree_trigger(self, position: Position) -> float:
        sl_percent = (
            abs(position.entry_price - position.stoploss) / position.entry_price
        )
        trigger_price = round(
            abs(sl_percent * self.riskfree_trigger_ratio + position.side.factor())
            * position.entry_price,
            position.chart.precision,
        )
        position.steps = [Trigger(trigger_price)]
        return trigger_price

    async def generate_position(
        self,
        signal: Signal,
        entry_price: float | None = None,
        plot: Plot | None = None,
        sl_base_price: float | None = None,
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

        if sl_base_price is None:
            sl_base_price = entry_price

        precision = signal.chart.precision
        sl = round(self.init_stoploss(sl_base_price, side), precision)
        sl_percent = abs(entry_price - sl) / entry_price
        tp = round(
            abs(sl_percent * self.ratio + side.factor()) * entry_price, precision
        )

        position = Position(
            signal.chart,
            side,
            entry_price,
            self.initial_volume,
            sl,
            tp,
            self.leverage,
            signal.candle.time + timedelta(seconds=2),
            signal.source,
            real_trade,
            plot=plot,
        )

        if self.riskfree_trigger_ratio > 0:
            self.set_riskfree_trigger(position)
        await commands.OpenPosition(position, self.exchange_agent).execute()
        self.open_positions.append(position)
        logger.info(f"New Position on {position.chart}")
        logger.debug(f"The New Position {position}")
        return position

    def modify_init_sl_tp(self, position: Position):
        sl_percent = (
            abs(position.entry_price - position.stoploss) / position.entry_price
        )
        tp = round(
            abs(sl_percent * self.ratio + position.side.factor())
            * position.entry_price,
            position.chart.precision,
        )
        if tp != position.takeprofit:
            position.takeprofit = tp
            commands.ChangeTakeProfit(position, self.exchange_agent, tp, report=False)
        position.confiremed = True
        logger.info(f"Position Updated on {position.chart}")

    def handler(
        self, position: Position, tick_prices: list[float]
    ) -> TradeCommand | None:
        res = super().handler(position, tick_prices)
        if res:
            return res
        if position.steps == []:
            return None

        direction = position.side.factor()

        ticks = np.array(tick_prices) * direction
        trigger = position.steps[0].price * direction

        cross = ticks >= trigger

        if cross.any():
            position.steps = []
            return commands.TrailStoploss(
                position, self.exchange_agent, position.entry_price
            )


class SlTpRatioForex(PositionHandler):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        ratio: float,
        initial_volume: float = 0.01,
        stoploss_pip: int = 20,
        riskfree_trigger_ratio: float = 0.0,
        long_trade: bool = True,
        short_trade: bool = True,
    ) -> None:
        super().__init__(exchange_agent, initial_volume, 1, long_trade, short_trade)
        self.ratio = ratio
        self.stoploss_pip = stoploss_pip / 10
        self.riskfree_trigger_ratio = riskfree_trigger_ratio

    def export_config(self) -> dict:
        conf_dict = super().export_config()
        conf_dict.pop("leverage")
        conf_dict.update(
            {
                "ratio": self.ratio,
                "riskfree_trigger_ratio": self.riskfree_trigger_ratio,
                "stoploss_pip": self.stoploss_pip,
            }
        )
        return conf_dict

    def init_stoploss(self, entry_price: float, side: OrderSide) -> float:
        return entry_price - side.factor() * self.stoploss_pip

    def init_takeprofit(self, entry_price: float, side: OrderSide) -> float:
        # WARNING: Don't use this method!
        return entry_price + side.factor() * (self.stoploss_pip * self.ratio)

    def set_riskfree_trigger(self, position: Position) -> float:
        sl_pip = abs(position.entry_price - position.stoploss)
        trigger_price = round(
            abs(
                position.entry_price
                + position.side.factor() * sl_pip * self.riskfree_trigger_ratio
            ),
            position.chart.precision,
        )
        position.steps = [Trigger(trigger_price)]
        return trigger_price

    async def generate_position(
        self,
        signal: Signal,
        entry_price: float | None = None,
        plot: Plot | None = None,
        sl_base_price: float | None = None,
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

        if sl_base_price is None:
            sl_base_price = entry_price

        precision = signal.chart.precision
        sl = round(self.init_stoploss(sl_base_price, side), precision)
        sl_pip = abs(entry_price - sl)
        tp = round(abs(entry_price + side.factor() * sl_pip * self.ratio), precision)

        position = Position(
            signal.chart,
            side,
            entry_price,
            self.initial_volume,
            sl,
            tp,
            self.leverage,
            signal.candle.time + timedelta(seconds=2),
            signal.source,
            real_trade,
            plot=plot,
        )
        if self.riskfree_trigger_ratio > 0:
            self.set_riskfree_trigger(position)
        await commands.OpenPosition(position, self.exchange_agent).execute()
        self.open_positions.append(position)
        logger.info(f"New Position on {position.chart}")
        logger.debug(f"The New Position {position}")
        position.in_forex = True
        return position

    def modify_init_sl_tp(self, position: Position):
        sl_pip = abs(position.entry_price - position.stoploss)
        tp = round(
            abs(position.entry_price + position.side.factor() * sl_pip * self.ratio),
            position.chart.precision,
        )
        if tp != position.takeprofit:
            position.takeprofit = tp
            commands.ChangeTakeProfit(position, self.exchange_agent, tp, report=False)
        position.confiremed = True
        logger.info(f"Position Updated on {position.chart}")

    def handler(
        self, position: Position, tick_prices: list[float]
    ) -> TradeCommand | None:
        res = super().handler(position, tick_prices)
        if res:
            return res
        if not position.steps:
            return None

        direction = position.side.factor()

        ticks = np.array(tick_prices) * direction
        trigger = position.steps[0].price * direction

        cross = ticks >= trigger

        if cross.any():
            position.steps = []
            return commands.TrailStoploss(
                position, self.exchange_agent, position.entry_price
            )
