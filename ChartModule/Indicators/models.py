from ChartModule import Candle, ChartData, MarketSide
from abc import ABC, abstractmethod
from enum import Flag
from typing import Any
import logging


logger = logging.getLogger("IndicatorModel")


class IndicatorBaseModel(ABC):
    def __init__(self) -> None:
        self.data: Any = None
        self.candles: list[Candle] = []
        self.forcast_rules: list[IndicatorForcastRule] = []
        self.last_checked_candle: Candle | None = None

    def export_configs(self) -> dict:
        return {"name": self.__class__.__name__}

    def find_new_candle_index(self, candles: list[Candle]):
        """
        Reverse Linear Search
        """
        if not self.last_checked_candle:
            raise ValueError("last_checked_candle is None")
        for i, candle in enumerate(candles[::-1]):
            if candle.timestamp == self.last_checked_candle.timestamp:
                return len(candles) - i
        raise ValueError("last_checked_candle not found")

    @abstractmethod
    def _calculate(self, *args, **kwargs) -> Any: ...

    @abstractmethod
    def plot(self, plot, *args, **kwargs) -> Any: ...

    @abstractmethod
    def update(self, candles: list[Candle], *args, **kwargs) -> Any: ...

    def set(self, candles: list[Candle], *args, **kwargs) -> Any:
        if not self.data:
            self.candles = candles
            self.data = self._calculate(*args, **kwargs)
            self.last_checked_candle = candles[-1]
        else:
            self.update(candles, *args, **kwargs)
        return self.data

    def forcast(self, *args, **kwargs) -> MarketSide:
        if self.data is None or self.forcast_rules == []:
            return MarketSide.NEUTRAL
        else:
            return sum([rule.forcast(self.data) for rule in self.forcast_rules])  # type: ignore


class IndicatorForcastRule(ABC):
    @abstractmethod
    def forcast(
        self,
        indicator: IndicatorBaseModel,
        *args,
        **kwargs,
    ) -> MarketSide: ...

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.forcast(*args, **kwargs)


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

    Heikin_Ashi = 4096

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

    def check(self, candles: list[Candle]) -> bool:
        if SupportCandleConditions.RAW in self:
            return True
        if SupportCandleConditions.Heikin_Ashi in self:
            candles = ChartData.heikinashi_candles(candles)

        if SupportCandleConditions.GREEN_RED in self:
            if not (
                candles[-2].side is MarketSide.BULLISH
                and candles[-1].side is MarketSide.BEARISH
            ):
                return False

        elif SupportCandleConditions.RED_GREEN in self:
            if not (
                candles[-2].side is MarketSide.BEARISH
                and candles[-1].side is MarketSide.BULLISH
            ):
                return False

        if SupportCandleConditions.HIGHER_LOW in self:
            if candles[-1].low < candles[-2].low:
                return False
        if SupportCandleConditions.HIGHER_BOTTOM in self:
            if candles[-1].body_bottom < candles[-2].body_bottom:
                return False
        if SupportCandleConditions.HIGHER_HIGH in self:
            if candles[-1].high < candles[-2].high:
                return False
        if SupportCandleConditions.HIGHER_TOP in self:
            if candles[-1].body_top < candles[-2].body_top:
                return False

        if SupportCandleConditions.LOWER_LOW in self:
            if candles[-1].low > candles[-2].low:
                return False
        if SupportCandleConditions.LOWER_BOTTOM in self:
            if candles[-1].body_bottom > candles[-2].body_bottom:
                return False
        if SupportCandleConditions.LOWER_HIGHT in self:
            if candles[-1].high > candles[-2].high:
                return False
        if SupportCandleConditions.LOWER_TOP in self:
            if candles[-1].body_top > candles[-2].body_top:
                return False
        return True
