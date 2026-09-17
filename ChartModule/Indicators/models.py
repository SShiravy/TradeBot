from ChartModule import Candle, ChartData, MarketSide
from abc import ABC, abstractmethod
from enum import Flag
from typing import Any
import logging
from ChartModule.plot import ChartPane, Figure, ObjectPlotter


logger = logging.getLogger("IndicatorModel")


class IndicatorPlotter(ObjectPlotter):
    @abstractmethod
    def __call__(self, pane: ChartPane, indicator_data: Any, *args, **kwargs):
        pass


class Indicator(ABC):
    def __init__(self) -> None:
        self.chartdata: ChartData | None = None
        self.data: Any = None
        self.rules: list[IndicatorRule] = []
        self.last_checked_candle: Candle | None = None
        self.plotter: IndicatorPlotter

    @property
    def name(self):
        return self.__class__.__name__

    def export_configs(self) -> dict:
        return {"name": self.name}

    def _find_update_start(self, chartdata: ChartData) -> int | None:
        """
        Locate where new_chartdata continues from what we last saw.
        Returns the index to start computing from, or None if the
        last known timestamp isn't present (gap, reset, or trimmed
        history) -- signaling a full recompute.
        """
        if self.last_checked_candle is None:
            return None

        ts = self.last_checked_candle.timestamp
        idx = chartdata.timestamp_index(ts)
        if idx >= len(chartdata) or chartdata.timestamps[idx] != ts:
            return None
        return idx + 1

    @abstractmethod
    def _calculate(self, chartdata: ChartData, *args, **kwargs) -> Any:
        """Full computation over the entire chartdata."""
        ...

    @abstractmethod
    def _calculate_new(self, chartdata: ChartData, start: int, *args, **kwargs) -> Any:
        """
        Compute only the segment from `start` onward, using chartdata
        (which holds full history) and self.data (previous result) as
        needed context. Return just the new portion, aligned to
        chartdata[start:] -- the caller merges it with self.data.
        """
        ...

    def _merge(self, new_segment: Any) -> Any:
        """How to combine self.data with a freshly computed new_segment. Override per data type."""
        raise NotImplementedError

    def update(self, chartdata: ChartData, *args, **kwargs) -> Any:
        start = self._find_update_start(chartdata)
        if start is None:
            return self._calculate(chartdata, *args, **kwargs)
        if start >= len(chartdata):
            return self.data  # nothing new closed since last check
        new_segment = self._calculate_new(chartdata, start, *args, **kwargs)
        return self._merge(new_segment)

    def set(self, chartdata: ChartData, *args, **kwargs) -> Any:
        self.chartdata = chartdata
        if self.data is None:
            self.data = self._calculate(chartdata, *args, **kwargs)
        else:
            self.data = self.update(chartdata, *args, **kwargs)
        self.last_checked_candle = chartdata[-1]
        return self.data

    def forecast(self, *args, **kwargs) -> MarketSide:
        if self.data is None or not self.rules:
            return MarketSide.NEUTRAL
        votes = [rule.forecast(self, *args, **kwargs) for rule in self.rules]
        return self._aggregate_votes(votes)

    def _aggregate_votes(self, votes: list[MarketSide]) -> MarketSide:
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


class SupportCandlesPattern(Flag):  # TODO: make this an indicator
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
        values_list = list(SupportCandlesPattern)
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
        if SupportCandlesPattern.RAW in self:
            return True

        current_candle = chartdata.candle(index)
        previous_candle = chartdata.candle(index - 1)
        if SupportCandlesPattern.RAW in self:
            return True

        if SupportCandlesPattern.GREEN_RED in self:
            if not (
                previous_candle.side is MarketSide.BULLISH
                and current_candle.side is MarketSide.BEARISH
            ):
                return False

        elif SupportCandlesPattern.RED_GREEN in self:
            if not (
                previous_candle.side is MarketSide.BEARISH
                and current_candle.side is MarketSide.BULLISH
            ):
                return False

        if SupportCandlesPattern.HIGHER_LOW in self:
            if current_candle.low < previous_candle.low:
                return False
        if SupportCandlesPattern.HIGHER_BOTTOM in self:
            if current_candle.body_bottom < previous_candle.body_bottom:
                return False
        if SupportCandlesPattern.HIGHER_HIGH in self:
            if current_candle.high < previous_candle.high:
                return False
        if SupportCandlesPattern.HIGHER_TOP in self:
            if current_candle.body_top < previous_candle.body_top:
                return False

        if SupportCandlesPattern.LOWER_LOW in self:
            if current_candle.low > previous_candle.low:
                return False
        if SupportCandlesPattern.LOWER_BOTTOM in self:
            if current_candle.body_bottom > previous_candle.body_bottom:
                return False
        if SupportCandlesPattern.LOWER_HIGHT in self:
            if current_candle.high > previous_candle.high:
                return False
        if SupportCandlesPattern.LOWER_TOP in self:
            if current_candle.body_top > previous_candle.body_top:
                return False
        return True
