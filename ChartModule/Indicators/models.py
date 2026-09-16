from ChartModule import Candle, ChartData, MarketSide
from abc import ABC, abstractmethod
from enum import Flag
from typing import Any
import logging


logger = logging.getLogger("IndicatorModel")

from abc import ABC, abstractmethod
from typing import Any


class Indicator(ABC):
    def __init__(self) -> None:
        self.chartdata: ChartData | None = None
        self.data: Any = None
        self.rules: list[IndicatorRule] = []
        self.last_checked_candle: Candle | None = None

    def export_configs(self) -> dict:
        return {"name": self.__class__.__name__}

    def find_new_candle_index(self, chartdata: ChartData) -> int:
        if self.last_checked_candle is None:
            raise ValueError("last_checked_candle is None")
        idx = chartdata.timestamp_index(self.last_checked_candle.timestamp)
        return idx + 1

    @abstractmethod
    def _calculate(self, *args, **kwargs) -> Any: ...

    @abstractmethod
    def plot(self, plot, *args, **kwargs) -> Any: ...

    @abstractmethod
    def update(self, chartdata: ChartData, *args, **kwargs) -> Any:
        """
        Must return the updated data. Called by set() when incremental
        update is possible instead of a full recalculation.
        """
        ...

    def set(self, chartdata: ChartData, *args, **kwargs) -> Any:
        if self.data is None:
            self.chartdata = chartdata
            self.data = self._calculate(chartdata, *args, **kwargs)
        else:
            self.chartdata = chartdata
            self.data = self.update(chartdata, *args, **kwargs)
        self.last_checked_candle = chartdata[-1]
        return self.data

    def forecast(self, *args, **kwargs) -> MarketSide:
        if self.data is None or not self.rules:
            return MarketSide.NEUTRAL
        votes = [rule.forecast(self, *args, **kwargs) for rule in self.rules]
        return self._aggregate_votes(votes)

    def _aggregate_votes(self, votes: list[MarketSide]) -> MarketSide:
        """
        Majority vote aggregation. Override in a subclass for weighted
        or rule-priority-based logic if a simple majority isn't enough.
        """
        bullish = votes.count(MarketSide.BULLISH)
        bearish = votes.count(MarketSide.BEARISH)
        if bullish > bearish:
            return MarketSide.BULLISH
        if bearish > bullish:
            return MarketSide.BEARISH
        return MarketSide.NEUTRAL


class IndicatorRule(ABC):
    @abstractmethod
    def forecast(
        self,
        indicator: Indicator,
        *args,
        **kwargs,
    ) -> MarketSide: ...

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.forecast(*args, **kwargs)


class SupportCandleConditions(Flag):
    """
    support candlestick conditions
    """

    RAW = 2

    HIGHER_LOW = 4
    HIGHER_BOTTOM = 8
    HIGHER_HIGH = 16
    HIGHER_TOP = 32

    LOWER_LOW = 64
    LOWER_BOTTOM = 128
    LOWER_HIGHT = 256
    LOWER_TOP = 512

    GREEN_RED = 1024
    RED_GREEN = 2048

    @classmethod
    def get_index_dict(cls):
        return {i + 1: list(cls)[i] for i in range(len(cls))}

    @property
    def indices(self):
        values_list = list(SupportCandleConditions)
        res = []
        for support_condition in self:
            res.append(values_list.index(support_condition) + 1)
        return res

    @classmethod
    def get_item_by_index(cls, indices: list[int]):
        result = None
        index_dict = cls.get_index_dict()
        for i in indices:
            support_condition = index_dict.get(i)
            if support_condition is None:
                continue
            if result:
                result |= support_condition
            else:
                result = support_condition
        return result

    def check(self, chartdata: ChartData, index: int = -1) -> bool:
        if SupportCandleConditions.RAW in self:
            return True

        current_candle = chartdata.candle(index)
        previous_candle = chartdata.candle(index - 1)
        if SupportCandleConditions.RAW in self:
            return True

        if SupportCandleConditions.GREEN_RED in self:
            if not (
                previous_candle.side is MarketSide.BULLISH
                and current_candle.side is MarketSide.BEARISH
            ):
                return False

        elif SupportCandleConditions.RED_GREEN in self:
            if not (
                previous_candle.side is MarketSide.BEARISH
                and current_candle.side is MarketSide.BULLISH
            ):
                return False

        if SupportCandleConditions.HIGHER_LOW in self:
            if current_candle.low < previous_candle.low:
                return False
        if SupportCandleConditions.HIGHER_BOTTOM in self:
            if current_candle.body_bottom < previous_candle.body_bottom:
                return False
        if SupportCandleConditions.HIGHER_HIGH in self:
            if current_candle.high < previous_candle.high:
                return False
        if SupportCandleConditions.HIGHER_TOP in self:
            if current_candle.body_top < previous_candle.body_top:
                return False

        if SupportCandleConditions.LOWER_LOW in self:
            if current_candle.low > previous_candle.low:
                return False
        if SupportCandleConditions.LOWER_BOTTOM in self:
            if current_candle.body_bottom > previous_candle.body_bottom:
                return False
        if SupportCandleConditions.LOWER_HIGHT in self:
            if current_candle.high > previous_candle.high:
                return False
        if SupportCandleConditions.LOWER_TOP in self:
            if current_candle.body_top > previous_candle.body_top:
                return False
        return True
