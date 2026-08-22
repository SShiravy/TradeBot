
from dataclasses import dataclass
from typing import Literal

from AutoTrendlineModule.auto_trendline import MTREvent
from ChartModule.models import Signal
from SRZoneModule.sr_zone import ZoneModel


@dataclass(slots=True, frozen=True)
class SRSignal(Signal):
    zone: ZoneModel
    touch_type: Literal["Shadow", "Body"]




@dataclass(slots=True, frozen=True)
class MTRSignal(Signal):
    mtr: MTREvent
