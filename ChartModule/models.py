from dataclasses import dataclass, asdict, field
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Literal
from enum import Enum
import pandas as pd
import numpy as np
from copy import copy


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
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    NEUTRAL = "Neutral"

    @property
    def number(self):
        match self:
            case MarketSide.BEARISH:
                return -1
            case MarketSide.BULLISH:
                return 1
        return 0


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
    time: datetime
    timeframe: TimeFrame | str | None = None
    timestamp: int | None = None


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


@dataclass(slots=True)
class Chart:
    symbol: str
    timeframe: TimeFrame
    precision: int = field(default=3)

    def __str__(self) -> str:
        return f"{self.symbol} {self.timeframe}"


@dataclass(slots=True, frozen=True)
class Signal:
    chart: Chart
    candle: Candle
    side: Literal[MarketSide.BEARISH, MarketSide.BULLISH]
    source: str

    def __str__(self) -> str:
        return f"{self.chart} {self.side} at {self.candle.time} from {self.source}"


class IndicatorBaseModel(ABC):
    def __init__(self) -> None:
        self.values: Any = None
        self.candles: list[Candle] = []
        self.last_checked_candle: Candle | None = None

    @abstractmethod
    def _calculate(self, *args, **kwargs) -> Any:
        pass

    @abstractmethod
    def _forcast(self, *args, **kwargs) -> MarketSide:
        pass

    @abstractmethod
    def plot(self, plot, *args, **kwargs) -> Any:
        pass

    def forcast(self, *args, **kwargs) -> MarketSide:
        if self.values is None:
            return MarketSide.NEUTRAL
        else:
            return self._forcast(*args, **kwargs)

    def update(self, candles: list[Candle], *args, **kwargs) -> Any:
        self.candles = candles
        new_values = self._calculate(*args, **kwargs)
        last_value = self.values[-1]
        if new_values and new_values[-1] != last_value and last_value in new_values:
            new_values = new_values[new_values.index(last_value) :]

        self.values += new_values
        self.last_checked_candle = candles[-1]
        return new_values

    def set(self, candles: list[Candle], *args, **kwargs) -> Any:
        if not self.values:
            self.candles = candles
            self.values = self._calculate(*args, **kwargs)
            self.last_checked_candle = candles[-1]
        else:
            self.update(candles, *args, **kwargs)
        return self.values


class IndicatorCandleSource(Enum):
    High = "high"
    Low = "low"
    Top = "top"
    Bottom = "bottom"
    Close = "close"
    Open = "open"
    Volume = "volume"

    def __call__(self, candle: Candle) -> float:
        match self:
            case IndicatorCandleSource.High:
                return candle.high
            case IndicatorCandleSource.Low:
                return candle.low
            case IndicatorCandleSource.Top:
                return candle.body_top
            case IndicatorCandleSource.Bottom:
                return candle.body_bottom
            case IndicatorCandleSource.Close:
                return candle.close
            case IndicatorCandleSource.Open:
                return candle.open
            case IndicatorCandleSource.Volume:
                return candle.volume


@dataclass(slots=True)
class ChartData:
    chart: Chart
    candles: list[Candle] = field(default_factory=list)
    indicators: list[IndicatorBaseModel] = field(default_factory=list)

    def __len__(self):
        return len(self.candles)

    def __iter__(self):
        return iter(self.candles)

    def __getitem__(self, index):
        return self.candles[index]

    def __str__(self):
        return f"{self.chart} with {len(self.candles)} candles & {len(self.indicators)} Idicator"

    def index(self, value):
        return self.candles.index(value)

    @classmethod
    def heikinashi_candles(cls, candles: list[Candle]) -> list[Candle]:
        ha_candles = []

        # First HA candle
        first_candle = candles[0]
        ha_close = (
            first_candle.open
            + first_candle.high
            + first_candle.low
            + first_candle.close
        ) / 4
        ha_open = (first_candle.open + first_candle.close) / 2
        ha_high = first_candle.high
        ha_low = first_candle.low

        ha_candles.append(
            Candle(
                ha_open,
                ha_close,
                ha_high,
                ha_low,
                first_candle.volume,
                first_candle.time,
                first_candle.timeframe,
            )
        )

        # Rest of HA candles
        for candle in candles[1:]:
            prev_ha = ha_candles[-1]
            digits = len(str(candle.high).split(".")[-1])

            ha_close = round(
                (candle.open + candle.high + candle.low + candle.close) / 4, digits
            )
            ha_open = round((prev_ha.open + prev_ha.close) / 2, digits)
            ha_high = max(candle.high, ha_open, ha_close)
            ha_low = min(candle.low, ha_open, ha_close)

            ha_candles.append(
                Candle(
                    ha_open,
                    ha_close,
                    ha_high,
                    ha_low,
                    candle.volume,
                    candle.time,
                    candle.timeframe,
                )
            )

        return ha_candles

    def give_heikingashi_chartdata(self):
        return ChartData(
            self.chart, self.heikinashi_candles(self.candles), self.indicators
        )

    def generate_dataframe(self) -> pd.DataFrame:
        open_list = []
        high_list = []
        low_list = []
        close_list = []
        volume_list = []
        time_list = []

        for candle in self.candles:
            open_list.append(candle.open)
            high_list.append(candle.high)
            low_list.append(candle.low)
            close_list.append(candle.close)
            volume_list.append(candle.volume)
            time_list.append(candle.time)

        df = pd.DataFrame(
            {
                "open": open_list,
                "high": high_list,
                "low": low_list,
                "close": close_list,
                "volume": volume_list,
            },
            index=time_list,
        )
        return df

    @classmethod
    def generate_crosspair(
        cls,
        first_chartdata: "ChartData",
        second_chartdata: "ChartData",
        crosspair_chart: Chart,
    ):
        all_candles_list = []
        first_index = 0
        second_index = 0
        n_bar = max(len(first_chartdata), len(second_chartdata))
        for _ in range(n_bar):
            if first_index > len(first_chartdata):
                break
            if second_index > len(second_chartdata):
                break
            first_candle = first_chartdata.candles[first_index]
            second_candle = second_chartdata.candles[second_index]
            if first_candle.time < second_candle.time:
                first_index += 1
                continue
            if second_candle.time < first_candle.time:
                second_index += 1
                continue

            all_candles_list.append(
                Candle(
                    first_candle.open / second_candle.open,
                    first_candle.close / second_candle.close,
                    first_candle.high / second_candle.high,
                    first_candle.low / second_candle.low,
                    min(first_candle.volume, second_candle.volume),
                    first_candle.time,
                    timeframe=crosspair_chart.timeframe,
                )
            )
            first_index += 1
            second_index += 1

        crosspair_candlestick = ChartData(crosspair_chart, all_candles_list)
        return crosspair_candlestick

    def give_sub_chartdata(self, sub_candles):
        chart = copy(self.chart)
        return ChartData(chart, sub_candles)
