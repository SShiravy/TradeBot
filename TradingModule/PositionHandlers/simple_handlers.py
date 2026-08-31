from ChartModule.models import Signal
from ChartModule.plot import Plot
from TradingModule.PositionHandlers.manager import PositionGenerator
from TradingModule.models import ExchangeAgent, PositionSide, Position


class SimpleCrypto(PositionGenerator):
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

    def export_config(self) -> dict:
        conf_dict = super().export_config()
        conf_dict.update(
            {
                "stoploss_percent": self.stoploss_percent,
                "takeprofit_percent": self.takeprofit_percent,
            }
        )
        return conf_dict

    def init_stoploss(self, entry_price: float, side: PositionSide) -> float:
        return abs(self.stoploss_percent / 100 - side.factor()) * entry_price

    def init_takeprofit(self, entry_price: float, side: PositionSide) -> float:
        return abs(self.takeprofit_percent / 100 + side.factor()) * entry_price


class SimpleForex(PositionGenerator):
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

    def export_config(self) -> dict:
        conf_dict = super().export_config()
        conf_dict.pop("leverage")
        conf_dict.update(
            {"stoploss_pip": self.stoploss_pip, "takeprofit_pip": self.takeprofit_pip}
        )
        return conf_dict

    def init_stoploss(self, entry_price: float, side: PositionSide) -> float:
        return entry_price - side.factor() * self.stoploss_pip

    def init_takeprofit(self, entry_price: float, side: PositionSide) -> float:
        return entry_price + side.factor() * self.takeprofit_pip

    async def generate(
        self,
        signal: Signal,
        entry_price: float | None = None,
        plot: Plot | None = None,
        *args,
        **kwargs,
    ) -> Position:
        pos = await super().generate(
            signal, entry_price, plot=plot, kwargs=kwargs, args=args
        )
        pos.in_forex = True
        return pos
