from TradingModule.PositionHandlers.riskfree_handlers import (
    RiskFreeCrypto,
    RiskFreeForex,
)
from TradingModule.models import ExchangeAgent, PositionSide, Position


class SideDistinctCrypto(RiskFreeCrypto):
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

    def export_config(self) -> dict:
        return {
            "Handler": self.__class__.__name__,
            "initial_volume": self.initial_volume,
            "leverage": self.leverage,
            "long_trade": self.long_trade,
            "short_trade": self.short_trade,
            "long_stoploss_percent": self.long_stoploss_percent,
            "long_takeprofit_percent": self.long_takeprofit_percent,
            "long_riskfree_trigger_percent": self.long_riskfree_trigger_percent,
            "short_stoploss_percent": self.short_stoploss_percent,
            "short_takeprofit_percent": self.short_takeprofit_percent,
            "short_riskfree_trigger_percent": self.short_riskfree_trigger_percent,
        }

    def init_stoploss(self, entry_price: float, side: PositionSide) -> float:
        if side is PositionSide.LONG:
            return abs(self.long_stoploss_percent / 100 - 1) * entry_price
        else:
            return abs(self.short_stoploss_percent / 100 + 1) * entry_price

    def init_takeprofit(self, entry_price: float, side: PositionSide) -> float:
        if side is PositionSide.LONG:
            return abs(self.long_takeprofit_percent / 100 + 1) * entry_price
        else:
            return abs(self.short_takeprofit_percent / 100 - 1) * entry_price

    def give_trigger_price(self, position: Position) -> float:
        if position.stoploss == position.entry_price:
            # when already riskfree triggered
            return position.takeprofit
        if position.side is PositionSide.LONG:
            return (
                abs(self.long_riskfree_trigger_percent / 100 + 1) * position.entry_price
            )
        else:
            return (
                abs(self.short_riskfree_trigger_percent / 100 - 1)
                * position.entry_price
            )


class SideDistinctForex(RiskFreeForex):
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
        self.long_stoploss_pip = long_stoploss_pip / 10
        self.long_takeprofit_pip = long_takeprofit_pip / 10
        self.long_riskfree_trigger_pip = long_riskfree_trigger_pip / 10

        self.short_stoploss_pip = short_stoploss_pip / 10
        self.short_takeprofit_pip = short_takeprofit_pip / 10
        self.short_riskfree_trigger_pip = short_riskfree_trigger_pip / 10

    def export_config(self) -> dict:
        return {
            "Handler": self.__class__.__name__,
            "initial_volume": self.initial_volume,
            "long_trade": self.long_trade,
            "short_trade": self.short_trade,
            "long_stoploss_pip": self.long_stoploss_pip,
            "long_takeprofit_pip": self.long_takeprofit_pip,
            "long_riskfree_trigger_pip": self.long_riskfree_trigger_pip,
            "short_stoploss_pip": self.short_stoploss_pip,
            "short_takeprofit_pip": self.short_takeprofit_pip,
            "short_riskfree_trigger_pip": self.short_riskfree_trigger_pip,
        }

    def init_stoploss(self, entry_price: float, side: PositionSide) -> float:
        if side is PositionSide.LONG:
            return entry_price - self.long_stoploss_pip
        else:
            return entry_price + self.short_stoploss_pip

    def init_takeprofit(self, entry_price: float, side: PositionSide) -> float:
        if side is PositionSide.LONG:
            return entry_price + self.long_takeprofit_pip
        else:
            return entry_price - self.short_takeprofit_pip

    def give_trigger_price(self, position: Position) -> float:
        if position.stoploss == position.entry_price:
            # when already riskfree triggered
            return position.takeprofit
        if position.side is PositionSide.LONG:
            return position.entry_price + self.long_riskfree_trigger_pip
        else:
            return position.entry_price - self.short_riskfree_trigger_pip
