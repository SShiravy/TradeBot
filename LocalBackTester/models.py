from ChartModule.models import Candle, Chart
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger("BacktestModels")


class KlineSource(Enum):
    BINCANCE = "binance"
    OPOFINANCE_META = "opofinance"
    OTET_Meta = "otet"
    DUKASCOPY = "dukascopy"
    OTHER = "other"


@dataclass(slots=True, frozen=True)
class Tick:
    timestamp: int
    bid: float
    ask: float
    last: float
    volume: float

import numpy as np


class TickData:

    def __init__(
        self,
        timestamps: np.ndarray,
        bids: np.ndarray,
        asks: np.ndarray,
        lasts: np.ndarray,
        volumes: np.ndarray,
    ):
        self.timestamps = timestamps
        self.bids = bids
        self.asks = asks
        self.lasts = lasts
        self.volumes = volumes
        

    def __len__(self):
        return len(self.timestamps)

    def __getitem__(self, index: int) -> Tick:
        return Tick(
            timestamp=int(self.timestamps[index]),
            bid=float(self.bids[index]),
            ask=float(self.asks[index]),
            last=float(self.lasts[index]),
            volume=float(self.volumes[index]),
        )

    def get_by_timestamp(self, timestamp: int) -> Tick | None:
        idx = np.searchsorted(self.timestamps, timestamp)

        if idx >= len(self.timestamps):
            return None

        if self.timestamps[idx] != timestamp:
            return None

        return self[int(idx)]

    def slice(self, left: int, right: int) -> "TickData":
        return TickData(
            self.timestamps[left:right],
            self.bids[left:right],
            self.asks[left:right],
            self.lasts[left:right],
            self.volumes[left:right],
        )
class TickDataHandler:

    def __init__(self, parquet_path: str,        
                start_timestamp: int | None = None,
                end_timestamp: int | None = None
                ):
        logger.info(f"Reading TickData from: {parquet_path}")

        df = (
            pd.read_parquet(parquet_path)
            .sort_values("time")
            .reset_index(drop=True)
        )

        if start_timestamp is not None:
            left = np.searchsorted(df["time"].to_numpy(), start_timestamp, side="left")
        else:
            left = 0

        if end_timestamp is not None:
            right = np.searchsorted(
                df["time"].to_numpy(),
                end_timestamp + 1,
                side="left",
            )
        else:
            right = len(df)

        df = df.iloc[left:right].reset_index(drop=True)

        df = (
            pd.read_parquet(parquet_path)
            .sort_values("time")
            .reset_index(drop=True)
        )

        self.tick_data = TickData(
            timestamps=df["time"].to_numpy(np.int64),
            bids=df["bid"].to_numpy(np.float64),
            asks=df["ask"].to_numpy(np.float64),
            lasts=df["last"].to_numpy(np.float64),
            volumes=df["volume"].to_numpy(np.float64),
        )

    def trim(
            self,
            start_timestamp: int | None = None,
            end_timestamp: int | None = None,
        ) -> None:
            if start_timestamp:
                left = int(np.searchsorted(
                    self.tick_data.timestamps,
                    start_timestamp,
                    side="left",
                ))
            else:
                left = 0
            if end_timestamp:
                right = int(np.searchsorted(
                    self.tick_data.timestamps,
                    end_timestamp + 1,
                    side="left",
                ))
            else:
                right = -1

            self.tick_data.timestamps = self.tick_data.timestamps[left:right]
            self.tick_data.bids = self.tick_data.bids[left:right]
            self.tick_data.asks = self.tick_data.asks[left:right]
            self.tick_data.lasts = self.tick_data.lasts[left:right]
            self.tick_data.volumes = self.tick_data.volumes[left:right]

    def get_ticks_from_timstamp_range(
        self,
        start_timestamp: int,
        end_timestamp: int,
    ) -> TickData:

        left = np.searchsorted(
            self.tick_data.timestamps,
            start_timestamp,
            side="left",
        )

        right = np.searchsorted(
            self.tick_data.timestamps,
            end_timestamp + 1,
            side="left",
        )

        return self.tick_data.slice(int(left), int(right))

    def get_ticks_for_candle(
        self,
        candle: Candle,
        chart: Chart,
    ) -> TickData:

        return self.get_ticks_from_timstamp_range(
            candle.timestamp,
            candle.timestamp + chart.timeframe.minutes * 60,
        )
    
@dataclass(slots=True)
class CsvChart(Chart):
    csv_path: str = field(default="")
    csv_source: KlineSource = field(default=KlineSource.OTHER)
    ticks_path: str | None = field(default=None)
    _tick_handler: TickDataHandler | None = field(default=None, init=False)

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

    @property
    def tick_handler(self) -> TickDataHandler:
        if self.ticks_path is None:
            raise ValueError("ticks_path is not set for CsvChart")
        if self._tick_handler is None:
            self._tick_handler = TickDataHandler(self.ticks_path)
        return self._tick_handler
