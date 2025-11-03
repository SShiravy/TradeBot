from ChartModule import Candle
from enum import Enum


class IndicatorCandleSource(Enum):
    High = "high"
    Low = "low"
    Top = "top"
    Bottom = "bottom"
    Close = "close"
    Open = "open"
    Volume = "volume"

    def __call__(self,candle:Candle)->float:
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
