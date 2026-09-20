from dataclasses import dataclass
from typing import Literal

from ChartModule.models import Signal
from ChartModule.Indicators.auto_trendline import MTREvent, TrendlineModel
from ChartModule.Indicators.sr_zone import ZoneModel


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
