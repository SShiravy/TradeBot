from numba import njit
import numpy as np


# get signal
# get csv chart and tick handler
def tick_backtester(signal:Signal,chart:CsvChart):
    from numba import njit
    

@njit(cache=True)
def which_hits_first_nb(prices:np.ndarray, tp_price, sl_price, is_long, entry_idx=0):
    n = prices.shape[0]
    for i in range(entry_idx, n):
        p = prices[i]
        if is_long:
            if p >= tp_price:
                return i, 1  # TP
            if p <= sl_price:
                return i, -1  # SL
        else:
            if p <= tp_price:
                return i, 1
            if p >= sl_price:
                return i, -1
    return -1, 0 
# choose start tick
# generate position on that tick
# slice all next ticks (bid or ask based on pos side)
# call tick handler for pos 
# repeat two priviouse step until pos become closed




def handle_positions(self,candle:Candle,position_handler:PositionHandler):
        if isinstance(self.diver_config.chart,CsvChart):
            tickdata = self.diver_config.chart.tick_handler.get_ticks_for_candle(candle,self.diver_config.chart)
            for pos in position_handler.open_positions.copy():
                if pos.closed:
                    position_handler.closed_positions.append(pos)
                    position_handler.open_positions.remove(pos)
                    continue
                ticks = tickdata.bids if pos.side is OrderSide.BUY else tickdata.asks
                position_handler.handler(pos, ticks)
            self.diver_config.chart.tick_handler.trim(start_timestamp=tickdata[-1].timestamp)
        else:
            ticks = [
                        candle.open,
                        candle.low,
                        candle.high,
                        candle.close,
                    ]
            for pos in position_handler.open_positions.copy():
                if pos.closed:
                    position_handler.closed_positions.append(pos)
                    position_handler.open_positions.remove(pos)
                    continue
                position_handler.handler(pos, ticks)