from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from abc import ABC, abstractmethod


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


class CandleType(Enum):
    Bullish = "bullish"
    Bearish = "bearish"


@dataclass(slots=True)
class Candle:
    open: float
    close: float
    high: float
    low: float
    time: datetime
    volume: float | None = None
    timeframe: TimeFrame | str | None = None

    @property
    def type(self):
        return CandleType.Bullish if self.close > self.open else CandleType.Bearish

    @property
    def body_bottom(self):
        return min(self.open, self.close)

    @property
    def body_top(self):
        return max(self.open, self.close)

    @property
    def body_lenght(self):
        return self.body_top - self.body_bottom

    def __str__(self) -> str:
        return f"{asdict(self)}"


@dataclass(slots=True)
class Chart:
    symbol: str
    timeframe: TimeFrame

    def __str__(self) -> str:
        return f"{self.symbol}_{self.timeframe}"


class Indicator(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def set(self):
        pass


@dataclass(slots=True)
class ChartData:
    chart: Chart
    candles: list[Candle] = field(default_factory=list)
    indicators: list[Indicator] = field(default_factory=list)

    def __len__(self):
        return len(self.candles)

    def __iter__(self):
        return iter(self.candles)

    def __str__(self):
        return f"{self.chart} with {len(self.candles)} candles & {len(self.indicators)}"

    @property
    def heikin_ashi_candles(self) -> list[Candle]:
        ha_candles = []

        # First HA candle
        first_candle = self.candles[0]
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
                first_candle.time,
                first_candle.volume,
                first_candle.timeframe,
            )
        )

        # Rest of HA candles
        for candle in self.candles[1:]:
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
                    candle.time,
                    candle.volume,
                    candle.timeframe,
                )
            )

        return ha_candles

    def give_heiking_ashi(self):
        return ChartData(self.chart, self.heikin_ashi_candles, self.indicators)

    @classmethod
    def give_crosspair(cls, first_chartdata, second_chartdata):
        pass
