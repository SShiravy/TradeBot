from ChartModule import Candle, ChartData, MarketSide
from enum import Enum, Flag


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


class SupportConditions(Flag):
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
        values_list = list(SupportConditions)
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
        if SupportConditions.RAW in self:
            return True
        if SupportConditions.Heikin_Ashi in self:
            candles = ChartData.heikinashi_candles(candles)

        if SupportConditions.GREEN_RED in self:
            if not (
                candles[-2].side is MarketSide.BULLISH
                and candles[-1].side is MarketSide.BEARISH
            ):
                return False

        elif SupportConditions.RED_GREEN in self:
            if not (
                candles[-2].side is MarketSide.BEARISH
                and candles[-1].side is MarketSide.BULLISH
            ):
                return False

        if SupportConditions.HIGHER_LOW in self:
            if candles[-1].low < candles[-2].low:
                return False
        if SupportConditions.HIGHER_BOTTOM in self:
            if candles[-1].body_bottom < candles[-2].body_bottom:
                return False
        if SupportConditions.HIGHER_HIGH in self:
            if candles[-1].high < candles[-2].high:
                return False
        if SupportConditions.HIGHER_TOP in self:
            if candles[-1].body_top < candles[-2].body_top:
                return False

        if SupportConditions.LOWER_LOW in self:
            if candles[-1].low > candles[-2].low:
                return False
        if SupportConditions.LOWER_BOTTOM in self:
            if candles[-1].body_bottom > candles[-2].body_bottom:
                return False
        if SupportConditions.LOWER_HIGHT in self:
            if candles[-1].high > candles[-2].high:
                return False
        if SupportConditions.LOWER_TOP in self:
            if candles[-1].body_top > candles[-2].body_top:
                return False
        return True
