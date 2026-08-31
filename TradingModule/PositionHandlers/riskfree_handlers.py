from TradingModule.PositionHandlers.simple_handlers import SimpleCrypto, SimpleForex
from TradingModule.models import ExchangeAgent, Position
from TradingModule.commands import Command
from TradingModule import commands
import numpy as np


class RiskFreeCrypto(SimpleCrypto):
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

    def export_config(self) -> dict:
        conf_dict = super().export_config()
        conf_dict.update(
            {
                "riskfree_trigger_percent": self.riskfree_trigger_percent,
            }
        )
        return conf_dict

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
    ) -> Command | None:
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


class RiskFreeForex(SimpleForex):
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
        self.riskfree_trigger_pip = riskfree_trigger_pip / 10

    def export_config(self) -> dict:
        conf_dict = super().export_config()
        conf_dict.update({"riskfree_trigger_pip": self.riskfree_trigger_pip})
        return conf_dict

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
    ) -> Command | None:
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
