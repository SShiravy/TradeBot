from ChartModule.models import Candle, ChartData, MarketSide, IndicatorBaseModel
from ChartModule.Indicators.models import IndicatorCandleSource
import numpy as np



class Line:
    
    def __init__(self,source:IndicatorCandleSource,
                 start_candle:Candle,end_candle:Candle) -> None:
        self.source = source
        self.start_candle = start_candle
        self.end_candle = end_candle

    @property
    def slope(self) -> float:
        slope = self.source(self.start_candle) - self.source(self.start_candle) / (
            self.end_candle.time.timestamp() - self.start_candle.time.timestamp()
        ) 
        return round(slope,3)


    def direction(self) -> MarketSide:
        if not self.start_candle or not self.end_candle:
            return MarketSide.NEUTRAL
        if self.source(self.start_candle) > self.source(self.end_candle):
            return MarketSide.BEARISH
        elif self.source(self.start_candle) < self.source(self.end_candle):
            return MarketSide.BULLISH
        else:
            return MarketSide.NEUTRAL
    

class TrendLine(IndicatorBaseModel):

    def __init__(self, source:IndicatorCandleSource,
                 min_step:int, max_step:int) -> None:
        super().__init__()
        self.source = source
        self.min_step = min_step
        self.max_step = max_step
        
    def _calculate(self)->list[Line]:
        lines = []
        last_candle = self.candles[-1]
        len_candles = len(self.candles)
        source_list = []
        time_list = []
        for candle in self.candles[-2::-1]:
            candle_index = self.candles.index(candle)
            if len_candles - candle_index > self.max_step:
                break

            source_list.append(self.source(candle))
            time_list.append(candle.time.timestamp())
            if len_candles - 1 - candle_index < self.min_step:
                continue

            the_line = Line(self.source, candle, last_candle)

            expected_low = (
                np.array(time_list) - candle.time.timestamp()
            ) * the_line.slope + self.source(candle)

            if np.any(np.array(source_list) - expected_low < 0):
                # invalid (line crossed candles)
                continue

            lines.append(the_line)

        return lines

    def _forcast(self) -> MarketSide:
        return self.values[-1].direction        
