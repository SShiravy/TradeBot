from ChartModule.models import Chart
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd


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

    @property
    def total_bars_number(self) -> int:
        return len(pd.read_csv(self.csv_path))
