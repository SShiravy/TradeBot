from dataclasses import dataclass
from typing import Literal

from AutoTrendlineModule.auto_trendline import MTREvent, TrendlineModel
from ChartModule.Indicators.models import IndicatorBaseModel, SupportCandleConditions
from ChartModule.models import ChartData, MarketSide, Signal
from SRZoneModule.sr_zone import ZoneModel
from TradingModule.models import Strategy


@dataclass(slots=True, frozen=True)
class StaticSRSignal(Signal):
    zone: ZoneModel
    touch_type: Literal["Shadow", "Body"]


@dataclass(slots=True, frozen=True)
class DynamicSRSignal(Signal):
    dynamic_sr: TrendlineModel


@dataclass(slots=True, frozen=True)
class MTRSignal(Signal):
    mtr: MTREvent


class DummyStrategy(Strategy):
    def __init__(
        self,
        name: str,
        long_support_conditions=SupportCandleConditions.RAW,
        short_support_conditions=SupportCandleConditions.RAW,
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

    def check_signal(
        self,
        chartdata: ChartData,
        check_long: bool = True,
        check_short: bool = True,
        *args,
        **kwargs,
    ) -> Signal | None:
        pass

    def report(self, *args, **kwargs) -> str:
        return ""

    def draw(self, plot, signal, draw_indicators: bool = True, *args, **kwargs):
        if draw_indicators and self.confirmation_indicators:
            for indicator in self.confirmation_indicators:
                indicator.plot(plot)

    def export_config(self):
        indicators_configs = []
        for indicator in self.confirmation_indicators:
            indicators_configs.append(indicator.export_configs())
        return {
            "long_support_conditions": self.long_support_conditions.value,
            "short_support_conditions": self.short_support_conditions.value,
            "indicators": indicators_configs,
        }
