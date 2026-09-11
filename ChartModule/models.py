from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta, timezone
from typing import Iterator, Literal, overload
from enum import Enum
import pandas as pd
import numpy as np
from copy import replace
from ChartModule.timing import TimeHandler


class TimeFrame(Enum):
    one_minute = "1m"
    two_minutes = "2m"
    three_minutes = "3m"
    four_minutes = "4m"
    five_minutes = "5m"
    six_minutes = "6m"
    ten_minutes = "10m"
    twelve_minutes = "12m"
    fifteen_minutes = "15m"
    twenty_minutes = "20m"
    thirty_minutes = "30m"
    one_hour = "1h"
    two_hours = "2h"
    three_hours = "3h"
    four_hours = "4h"
    six_hours = "6h"
    eight_hours = "8h"
    twelve_hours = "12h"
    one_day = "1d"
    three_day = "3d"
    one_week = "1w"
    one_month = "1M"

    @property
    def minutes(self) -> int:
        """
        Return the minutes for a given TimeFrame
        """
        mapping = {
            TimeFrame.one_minute: 1,
            TimeFrame.three_minutes: 3,
            TimeFrame.five_minutes: 5,
            TimeFrame.fifteen_minutes: 15,
            TimeFrame.thirty_minutes: 30,
            TimeFrame.one_hour: 60,
            TimeFrame.two_hours: 120,
            TimeFrame.four_hours: 240,
            TimeFrame.six_hours: 360,
            TimeFrame.eight_hours: 480,
            TimeFrame.twelve_hours: 720,
            TimeFrame.one_day: 1440,
            TimeFrame.one_week: 10080,
            TimeFrame.one_month: 43200,
        }
        return mapping[self]

    @property
    def time_delta(self) -> timedelta:
        return timedelta(minutes=self.minutes)

    def __str__(self):
        return self.value


class MarketSide(Enum):
    BEARISH = "Bearish"
    NEUTRAL = "Neutral"
    BULLISH = "Bullish"

    @property
    def number(self):
        return {
            MarketSide.BEARISH: -1,
            MarketSide.BULLISH: 1,
            MarketSide.BEARISH: 0,
        }[self]

    def __add__(self, other: "MarketSide") -> "MarketSide":
        if not isinstance(other, MarketSide):
            return NotImplemented

        total = self.number + other.number

        if total > 0:
            return MarketSide.BULLISH
        elif total < 0:
            return MarketSide.BEARISH
        else:
            return MarketSide.NEUTRAL

    def __radd__(self, other):
        if other == 0:
            return self
        return self.__add__(other)

    @property
    def score(self):
        return self.number


@dataclass(slots=True, frozen=True)
class TickPrice:
    price: float
    time: datetime

    def __str__(self) -> str:
        return f"{asdict(self)}"

    def check_upward_cross(self, tick_prices: list[float]):
        res = np.array(tick_prices) - self.price
        if np.any(res > 0):
            return True
        return False

    def check_downward_cross(self, tick_prices: list[float]):
        res = np.array(tick_prices) - self.price
        if np.any(res < 0):
            return True
        return False


@dataclass(slots=True, frozen=True)
class Candle:
    open: float
    close: float
    high: float
    low: float
    volume: float
    timestamp: int
    timeframe: TimeFrame

    @property
    def side(self):
        return MarketSide.BULLISH if self.close > self.open else MarketSide.BEARISH

    @property
    def body_bottom(self):
        return min(self.open, self.close)

    @property
    def body_top(self):
        return max(self.open, self.close)

    @property
    def body_length(self):
        return self.body_top - self.body_bottom

    def __str__(self) -> str:
        return f"{asdict(self)}"


class ChartType(Enum):
    Simple = "Simple"
    Heikinashi = "Heikinashi"


@dataclass(slots=True)
class Chart:
    symbol: str
    timeframe: TimeFrame
    chart_type: ChartType = field(default=ChartType.Simple)
    precision: int = field(default=3, init=False)
    pip_factor: float = field(default=1, init=False)
    contract_size: float | int = field(default=1, init=False)

    def __str__(self) -> str:
        return f"{self.symbol} {self.timeframe.value}"

    def export_config(self) -> dict:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe.value,
            "precision": self.precision,
            "chart_type": self.chart_type,
            "pip_factor": self.pip_factor,
            "contract_size": self.contract_size,
        }


@dataclass(slots=True, frozen=True)
class Signal:
    chart: Chart
    candle: Candle
    side: Literal[MarketSide.BEARISH, MarketSide.BULLISH]
    source: str

    def __str__(self) -> str:
        return f"{self.chart} {self.side} at {datetime.fromtimestamp(self.candle.timestamp, tz=timezone.utc)} from {self.source}"


@dataclass(slots=True)
class ChartData:
    chart: Chart
    open: np.ndarray = field(default_factory=lambda: np.array([]))
    high: np.ndarray = field(default_factory=lambda: np.array([]))
    low: np.ndarray = field(default_factory=lambda: np.array([]))
    close: np.ndarray = field(default_factory=lambda: np.array([]))
    volume: np.ndarray = field(default_factory=lambda: np.array([]))
    timestamps: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.int64))
    indices: np.ndarray = field(init=False)

    def __len__(self):
        return self.timestamps.shape[0]

    def candle(self, i: int) -> Candle:
        # single-candle construction, O(1), no intermediate allocations
        ts = int(self.timestamps[i])
        return Candle(
            open=float(self.open[i]),
            high=float(self.high[i]),
            low=float(self.low[i]),
            close=float(self.close[i]),
            volume=float(self.volume[i]),
            timestamp=ts,
            timeframe=self.chart.timeframe,
        )

    @overload
    def __getitem__(self, key: int) -> Candle: ...
    @overload
    def __getitem__(self, key: slice) -> Iterator[Candle]: ...

    def __getitem__(self, key: int | slice) -> "Candle | Iterator[Candle]":
        if isinstance(key, slice):
            # lazy generator, only builds candles as they're consumed
            indices = range(*key.indices(len(self)))
            return (self.candle(i) for i in indices)
        if isinstance(key, int):
            if key < 0:
                key += len(self)
            return self.candle(key)
        raise TypeError(f"Invalid index type: {type(key)}")

    def __iter__(self) -> Iterator[Candle]:
        for i in self.indices:
            yield self.candle(i)

    def __str__(self):
        return f"{self.chart} with {len(self)} candles"

    def timestamp_index(self, timestamp: int) -> int:
        idx = np.searchsorted(self.timestamps, timestamp)
        if idx >= len(self) or self.timestamps[idx] != timestamp:
            raise ValueError(f"Timestamp {timestamp} not found in chart data")
        return int(idx)

    def candle_index(self, candle: Candle) -> int:
        idx = self.timestamp_index(candle.timestamp)
        if (
            self.open[idx] != candle.open
            or self.high[idx] != candle.high
            or self.low[idx] != candle.low
            or self.close[idx] != candle.close
        ):
            raise ValueError(
                f"Candle at timestamp {candle.timestamp} does not match stored data"
            )
        return idx

    @staticmethod
    def _compute_heikinashi(
        open_: np.ndarray, high: np.ndarray, low: np.ndarray, close: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        n = open_.shape[0]
        if n == 0:
            return open_.copy(), high.copy(), low.copy(), close.copy()

        ha_close = (open_ + high + low + close) / 4.0
        ha_open = np.empty(n, dtype=np.float64)
        ha_open[0] = (open_[0] + close[0]) / 2.0
        for i in range(1, n):
            ha_open[i] = (ha_open[i - 1] + ha_close[i - 1]) / 2.0

        ha_high = np.maximum.reduce([high, ha_open, ha_close])
        ha_low = np.minimum.reduce([low, ha_open, ha_close])
        return ha_open, ha_high, ha_low, ha_close

    @classmethod
    def generate_heikinashi(cls, source: "ChartData") -> "ChartData":
        ha_open, ha_high, ha_low, ha_close = cls._compute_heikinashi(
            source.open, source.high, source.low, source.close
        )
        ha_chart = replace(source.chart, chart_type=ChartType.Heikinashi)
        return cls(
            chart=ha_chart,
            open=ha_open,
            high=ha_high,
            low=ha_low,
            close=ha_close,
            volume=source.volume.copy(),
            timestamps=source.timestamps.copy(),
        )

    def generate_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "open": self.open,
                "high": self.high,
                "low": self.low,
                "close": self.close,
                "volume": self.volume,
            },
            index=pd.to_datetime(self.timestamps, unit="s", utc=True),
        )

    @classmethod
    def generate_crosspair(
        cls,
        first_chartdata: "ChartData",
        second_chartdata: "ChartData",
        crosspair_chart: Chart,
    ):
        if first_chartdata.chart.timeframe != second_chartdata.chart.timeframe:
            raise ValueError(
                "Both chart data must have the same timeframe to generate a crosspair."
            )
        return cls(
            crosspair_chart,
            first_chartdata.open / second_chartdata.open,
            first_chartdata.high / second_chartdata.high,
            first_chartdata.low / second_chartdata.low,
            first_chartdata.close / second_chartdata.close,
            np.minimum(first_chartdata.volume, second_chartdata.volume),
            first_chartdata.timestamps,
        )

    def subdata(
        self, start_index: int = 0, end_index: int = -1, copy: bool = True
    ) -> "ChartData":
        n = len(self)
        s = slice(start_index, end_index).indices(n)
        s = slice(*s)

        if copy:
            return ChartData(
                chart=self.chart,
                open=self.open[s].copy(),
                high=self.high[s].copy(),
                low=self.low[s].copy(),
                close=self.close[s].copy(),
                volume=self.volume[s].copy(),
                timestamps=self.timestamps[s].copy(),
            )

        return ChartData(
            chart=self.chart,
            open=self.open[s],
            high=self.high[s],
            low=self.low[s],
            close=self.close[s],
            volume=self.volume[s],
            timestamps=self.timestamps[s],
        )

    def __post_init__(self):
        self.timestamps = TimeHandler.validate_timestamps(self.timestamps,auto_fix=True)
        if self.chart.chart_type is ChartType.Heikinashi:
            ha_open, ha_high, ha_low, ha_close = self._compute_heikinashi(
                self.open, self.high, self.low, self.close
            )
            self.open, self.high, self.low, self.close = (
                ha_open,
                ha_high,
                ha_low,
                ha_close,
            )
        self.indices = np.arange(len(self), dtype=np.int64)


    # TODO: cache these methods to avoid repeated calculations
    @property
    def body_top(self) -> np.ndarray:
        return np.maximum(self.open, self.close)

    @property
    def body_bottom(self) -> np.ndarray:
        return np.minimum(self.open, self.close)

    @property
    def body_length(self) -> np.ndarray:
        return self.body_top - self.body_bottom

    # TODO: add an update method to update the chartdata with new candles


class CandlesSource(Enum):
    High = "high"
    Low = "low"
    Top = "top"
    Bottom = "bottom"
    Close = "close"
    Open = "open"
    Volume = "volume"
    BodyLength = "body_length"

    @overload
    def __call__(self, data: Candle) -> float: ...
    @overload
    def __call__(self, data: ChartData) -> np.ndarray: ...

    def __call__(self, data: ChartData | Candle) -> np.ndarray | float:
        match self:
            case CandlesSource.High:
                return data.high
            case CandlesSource.Low:
                return data.low
            case CandlesSource.Top:
                return data.body_top
            case CandlesSource.Bottom:
                return data.body_bottom
            case CandlesSource.Close:
                return data.close
            case CandlesSource.Open:
                return data.open
            case CandlesSource.Volume:
                return data.volume
            case CandlesSource.BodyLength:
                return data.body_length
