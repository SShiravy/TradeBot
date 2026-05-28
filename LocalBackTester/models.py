from ChartModule.models import Candle, Chart
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np


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
    ticks_path: str | None = field(default=None)

    def __str__(self) -> str:
        return f"Csv Chart: {self.symbol} {self.timeframe} {self.csv_source}"

    def export_config(self) -> dict:
        conf_dict = super(CsvChart, self).export_config()
        conf_dict.update(
            {
                "csv_path": self.csv_path,
                "csv_source": self.csv_source.value,
                "ticks_path": self.ticks_path,
            }
        )
        return conf_dict

    @property
    def total_bars_number(self) -> int:
        return len(pd.read_csv(self.csv_path))


class TickDataHandler:
    def __init__(
        self,
        parquet_path: str,
    ):
        self.df = pd.read_parquet(
            parquet_path,
        )

        self.df = self.df.sort_values(
            "time",
        )

        self.timestamps = self.df["time"].to_numpy(dtype=np.int64)

    def get_ticks_from_timstamp_range(
        self,
        start_timestamp: int,
        end_timestamp: int,
    ) -> pd.DataFrame:
        left = np.searchsorted(
            self.timestamps,
            start_timestamp,
            side="left",
        )

        right = np.searchsorted(
            self.timestamps,
            end_timestamp + 1,
            side="left",
        )

        return self.df.iloc[left:right]

    def get_ticks_for_candle(self, candle: Candle, chart: Chart) -> pd.DataFrame:
        start_ts = candle.timestamp

        end_ts = start_ts + chart.timeframe.minutes * 60

        return self.get_ticks_from_timstamp_range(start_ts, end_ts)
