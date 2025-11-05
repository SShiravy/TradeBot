from ChartModule import Chart, Candle, ChartData, TimeFrame
from TradingModule import ExchangeAgent, Position, OrderSide
import mt5_wrapper as mt5
from datetime import datetime, timezone, timedelta
import logging


logger = logging.getLogger('ForexAgent')

class ForexAgent(ExchangeAgent):

    def __init__(self, check_market_is_open:bool=True) -> None:
        if not mt5.initialize():
                raise RuntimeError("MT5 initialize failed")
        logger.info("Initialized")
        self.check_market_is_open = check_market_is_open
    

    def check_chart(self,chart: Chart)->bool:
        symbol_info = mt5.symbol_info(chart.symbol)
        if symbol_info is None:
            raise RuntimeError(f"Failed to get symbol info for {chart.symbol}")

        chart.precision = len(str(symbol_info.point).split('.')[1])
        return True
    
    def prepare_chart(self,chart: Chart)->bool:
        if not mt5.symbol_select(chart.symbol, True):
            raise ValueError(f"Failed to select symbol {chart.symbol}")

        symbol_info = mt5.symbol_info(chart.symbol)
        if symbol_info is None:
            raise RuntimeError(f"Failed to get symbol info for {chart.symbol}")

        return True
    @classmethod
    def correct_time(cls,raw_time:datetime,chart:Chart):
        info = mt5.symbol_info(chart.symbol)
        if not info:
            return False
        delta = datetime.fromtimestamp(info.time,timezone.utc)-datetime.now(timezone.utc)
        return raw_time-delta

    def check_market_open(self,chart:Chart)->bool:
        if not self.check_market_is_open:
            return True
        if not self.prepare_chart(chart):
            return False
        now = datetime.now(tz=timezone.utc)
        tick = mt5.symbol_info_tick(chart.symbol)
        if tick is None:
            logger.error(f"Forex Failed to get tick data for {chart.symbol}")
            return False
        last_tick_time = self.correct_time(datetime.fromtimestamp(tick.time),chart)
        if not last_tick_time:
            return False
        if abs(last_tick_time.replace(minute=0,second=0,microsecond=0)-\
            now.replace(second=0,microsecond=0)) > timedelta(minutes=1):
            return False
        return True


    def get_chartdata(self, chart: Chart, n_bars: int = 100) -> ChartData | None:
        if not self.check_market_open(chart):
            return None
        if not self.prepare_chart(chart):
            return None

        ohlcv_res = mt5.copy_rates_from_pos(
            chart.symbol, forex_timeframe_mapper(chart.timeframe), 0, n_bars
        )
        if ohlcv_res is None:
            logger.error(f"fetching chart data failed: {chart=}")
            return None
        
        logger.info(f"{len(ohlcv_res)} ohlcv fetched for {chart}")

        all_candles_list = []
        for candle in ohlcv_res:
            candle_timestamp, open, high, low, close, volume, _, _ = candle

            candle_time = (
                datetime.fromtimestamp(candle_timestamp, tz=timezone.utc)
            )

            all_candles_list.append(
                Candle(
                    float(open),
                    float(close),
                    float(high),
                    float(low),
                    float(volume),
                    candle_time.replace(microsecond=0),
                    chart.timeframe,
                )
            )

        chartdata = ChartData(chart, all_candles_list)
        logger.debug(str(chartdata)+" Generated")

        return chartdata


    def open_position(self, position: Position)->str|None:
        if not self.prepare_chart(position.chart):
            return None
        
        tick = mt5.symbol_info_tick(position.chart.symbol)
        if tick is None:
            logger.error(f"Forex Failed to get tick data for {position.chart.symbol}")
            return None

        if position.side == OrderSide.BUY:
            price = tick.ask
            trade_side = mt5.ORDER_TYPE_BUY
        else:
            price = tick.bid
            trade_side = mt5.ORDER_TYPE_SELL

        # Build request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.chart.symbol,
            "volume": position.volume,
            "type": trade_side,
            "price": price,
            "sl": position.stoploss,
            "tp": position.takeprofit,
            "deviation": 20,
            "magic": 80713,
            "comment": "Python Trader Bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if not result:
            logging.error(f"Opening position failed: {position}\n{mt5.last_error()=}")
            return None
        position.entry_price = result.price
        logging.info(f"Position Opened: {position}\n{result=}")
        return str(result.order)


    def change_stoploss(self, position: Position, price) -> bool:
        if not position.id:
            logger.error(f"position have no id:\n{position=}")
            return False
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": int(position.id),
            "symbol": position.chart.symbol,
            "sl": price,
            "tp": position.takeprofit
        }

        result = mt5.order_send(request)
        if not result:
            logger.error(f"New SL Request Failed:{position=}\n{result=}")
            return False
        logging.debug(f"SL Changed of {position=}\n{result=}")
        return True

    def change_takeprofit(self, position: Position, price) -> bool:
        if not position.id:
            logger.error(f"position have no id:\n{position=}")
            return False
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": int(position.id),
            "symbol": position.chart.symbol,
            "sl": position.takeprofit,
            "tp": price
        }

        result = mt5.order_send(request)
        if not result:
            logger.error(f"New TP Request Failed:{position=}\n{result=}")
            return False
        logging.debug(f"TP Changed of {position=}\n{result=}")
        return True

    def partial_close(self, position: Position, volume) -> float|None:
        """
        return executed price if successful otherwise None
        """
        if not position.id:
            logger.error(f"position have no id:\n{position=}")
            return None

        if position.side == OrderSide.BUY:
            trade_side = mt5.ORDER_TYPE_BUY
        else:
            trade_side = mt5.ORDER_TYPE_SELL

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.chart.symbol,
            "position": position.id,
            "type": trade_side,
            "volume": volume,
            "deviation": 20,
        }

        result = mt5.order_send(request)
        if not result:
            logger.error(f"Partial Close Request Failed:{position=}\n{result=}")
            return None
        logging.debug(f"Partial Close for {position=}\n{result=}")
        return result.price

    def close_position(self, position: Position)->float|None:
        """
        return executed price if successful otherwise None
        """
        if not position.id:
            logger.error(f"position have no id:\n{position=}")
            return None

        if position.side == OrderSide.BUY:
            trade_side = mt5.ORDER_TYPE_BUY
        else:
            trade_side = mt5.ORDER_TYPE_SELL

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.chart.symbol,
            "position": position.id,
            "type": trade_side,
            "volume": position.volume,
            "deviation": 20,
        }

        result = mt5.order_send(request)
        if not result:
            logger.error(f"Close Position Failed: {position}\n{result=}")
            return None
        logging.debug(f"Position Close for {position=}\n{result=}")
        return result.price

    def get_open_positions(self, chart: Chart):
        pass




def forex_timeframe_mapper(timeframe: TimeFrame):
    """
    Map enum to MT5 TIMEFRAME_ constant
    """
    mapping = {
        "1m": mt5.TIMEFRAME_M1,
        "2m": mt5.TIMEFRAME_M2,
        "3m": mt5.TIMEFRAME_M3,
        "4m": mt5.TIMEFRAME_M4,
        "5m": mt5.TIMEFRAME_M5,
        "6m": mt5.TIMEFRAME_M6,
        "10m": mt5.TIMEFRAME_M10,
        "12m": mt5.TIMEFRAME_M12,
        "15m": mt5.TIMEFRAME_M15,
        "20m": mt5.TIMEFRAME_M20,
        "30m": mt5.TIMEFRAME_M30,
        "1h": mt5.TIMEFRAME_H1,
        "2h": mt5.TIMEFRAME_H2,
        "3h": mt5.TIMEFRAME_H3,
        "4h": mt5.TIMEFRAME_H4,
        "6h": mt5.TIMEFRAME_H6,
        "8h": mt5.TIMEFRAME_H8,
        "12h": mt5.TIMEFRAME_H12,
        "1d": mt5.TIMEFRAME_D1,
        "1w": mt5.TIMEFRAME_W1,
        "1M": mt5.TIMEFRAME_MN1,
    }
    return mapping[timeframe.value]