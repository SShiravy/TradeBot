from ChartModule.models import Candle, Chart, ChartData
from TradingModule.models import ExchangeAgent, Position
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from enum import Enum 


class KlineSource(Enum):
    BINCANCE = "binance"
    OPOFINANCE_META = "opofinance"
    OTET_Meta = "otet"
    DUKASCOPY = "dukascopy"
    OTHER = "other"


@dataclass(slots=True)
class CsvChart(Chart):
    csv_path: str = field(default="")
    csv_source: KlineSource = field(default=KlineSource.OTHER)
    
    def __str__(self) -> str:
        return f"Csv Chart: {self.symbol} {self.timeframe} {self.csv_source}"
    
