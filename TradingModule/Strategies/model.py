from ChartModule.models import IndicatorBaseModel, ChartData, Signal, MarketSide
from ChartModule.Indicators import SupportConditions
from abc import ABC, abstractmethod


class Strategy(ABC):
    def __init__(
        self,
        name: str,
        long_support_conditions: SupportConditions,
        short_support_conditions: SupportConditions,
        confirmation_indicators: list[IndicatorBaseModel] = [],
    ) -> None:
        self.name = name
        self.confirmation_indicators = confirmation_indicators
        self.long_support_conditions = long_support_conditions
        self.short_support_conditions = short_support_conditions

    def get_indicators_confirmation(self, chartdata: ChartData) -> list[MarketSide]:
        if self.confirmation_indicators == []:
            return [MarketSide.NEUTRAL]
        all_forcasts = []
        for indicator in self.confirmation_indicators:
            indicator.set(chartdata.candles)
            all_forcasts.append(indicator.forcast())
        return all_forcasts

    @abstractmethod
    def check_signal(
        self,
        chartdata: ChartData,
        long_signal: bool = True,
        short_signal: bool = True,
        *args,
        **kwargs,
    ) -> Signal | None:
        pass

    @abstractmethod
    def report(self, *args, **kwargs) -> str:
        pass

    @abstractmethod
    def draw(self, plot, signal, draw_indicators, *args, **kwargs):
        pass
