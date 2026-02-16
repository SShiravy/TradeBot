from ChartModule import Chart, Candle, ChartData, TimeFrame
from TradingModule.models import ExchangeAgent, Position, OrderSide
from datetime import datetime, timezone
from enum import Enum
import mt5_wrapper as mt5
import logging


logger = logging.getLogger("ForexAgent")


class MarketState(Enum):
    OPEN = "open"
    CLOSED = "closed"
    CHECK_LATER = "check_later"
    NOT_RESPONDING = "not_responding"

    def wait_seconds(self) -> int:
        match self:
            case MarketState.OPEN:
                return 0
            case MarketState.CLOSED:
                return 3600  # wait for 1 hour and check again
            case MarketState.CHECK_LATER:
                return 120  # wait for 2 mins and check again
            case MarketState.NOT_RESPONDING:
                return 900  # wait for 15 mins and check again
            case _:
                return 1800  # default wait time


class ForexAgent(ExchangeAgent):
    def __new__(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = object.__new__(cls)
            if not mt5.initialize(
                r"C:\Program Files\Opo group MetaTrader 5\terminal64.exe"
            ):
                raise RuntimeError("MT5 initialize failed")
            logger.info("Initialized")
            cls.last_checked_time: None | datetime = None
            cls.last_checked_candle: None | Candle = None
            cls.market_state: MarketState = MarketState.NOT_RESPONDING
        return cls._instance

    def check_chart(self, chart: Chart) -> bool:
        symbol_info = mt5.symbol_info(chart.symbol)
        if symbol_info is None:
            raise RuntimeError(f"Failed to get symbol info for {chart.symbol}")

        chart.precision = len(str(symbol_info.point).split(".")[1])
        return True

    def prepare_chart(self, chart: Chart) -> bool:
        if not mt5.symbol_select(chart.symbol, True):
            raise ValueError(f"Failed to select symbol {chart.symbol}")

        symbol_info = mt5.symbol_info(chart.symbol)
        if symbol_info is None:
            raise RuntimeError(f"Failed to get symbol info for {chart.symbol}")

        return True

    @classmethod
    def correct_time(cls, raw_time: datetime, chart: Chart) -> datetime:
        info = mt5.symbol_info(chart.symbol)
        if not info:
            raise ValueError(f"{chart=} | {info=}")
        delta = datetime.fromtimestamp(info.time, timezone.utc) - datetime.now(
            timezone.utc
        )
        return raw_time - delta

    def check_market_open(self, chart: Chart) -> None | int:
        """
        :return: None if market open or seconds to wait if market closed
        :rtype: int | None
        """
        data = self.get_chartdata(
            Chart(chart.symbol, timeframe=TimeFrame.one_minute), n_bars=2
        )
        if data is None:
            logger.error(f"Failed to get chart data for market open check: {chart}")
            self.market_state = MarketState.NOT_RESPONDING
            return self.market_state.wait_seconds()
        now = datetime.now(timezone.utc)
        if self.last_checked_time is None or self.last_checked_candle is None:
            self.last_checked_time = now
            self.last_checked_candle = data.candles[-1]
            logger.info(f"Set last Checked time {chart}")
            self.market_state = MarketState.CHECK_LATER

        if (now - self.last_checked_time).total_seconds() > 60:
            self.last_checked_time = now
            self.market_state = MarketState.OPEN
            if (
                data.candles[-1].time - self.last_checked_candle.time
            ).total_seconds() < 60:
                logger.info(
                    f"Market seems closed for {chart} | last candle time: {self.last_checked_candle.time}"
                )
                self.market_state = MarketState.CLOSED
        logger.debug(f"Market State for {chart}: {self.market_state}")
        return self.market_state.wait_seconds()

    def get_chartdata(self, chart: Chart, n_bars: int = 100) -> ChartData | None:
        if not self.prepare_chart(chart):
            return None
        ohlcv_res = mt5.copy_rates_from_pos(
            chart.symbol, forex_timeframe_mapper(chart.timeframe), 0, n_bars
        )
        if ohlcv_res is None:
            logger.error(f"fetching chart data failed: {chart=}")
            return None

        all_candles_list = []
        for candle in ohlcv_res:
            candle_timestamp, open, high, low, close, volume, _, _ = candle

            candle_time = datetime.fromtimestamp(
                candle_timestamp, tz=timezone.utc
            ).replace(microsecond=0, second=0)

            all_candles_list.append(
                Candle(
                    float(open),
                    float(close),
                    float(high),
                    float(low),
                    float(volume),
                    candle_time,
                    chart.timeframe,
                )
            )

        chartdata = ChartData(chart, all_candles_list)
        return chartdata

    def get_candles_since(self, chart: Chart, time: datetime):
        return super().get_candles_since(chart, time)

    def open_position(self, position: Position) -> float | None:
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
            "comment": "PythonTraderBot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if not result or not result.request_id:
            logging.error(f"Opening position failed: {position}\n{mt5.last_error()=}")
            return None
        position.exchange_id = str(result.order)
        position.spread = round(result.ask - result.bid,position.chart.precision)
        logging.info(f"Position Opened: {position}\n{result=}")
        return result.price

    def change_stoploss(self, position: Position, price) -> bool:
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": int(position.exchange_id),
            "symbol": position.chart.symbol,
            "sl": price,
            "tp": position.takeprofit,
        }

        result = mt5.order_send(request)
        if not result:
            logger.error(f"New SL Request Failed:{position=}\n{result=}")
            return False
        logging.debug(f"SL Changed of {position=}\n{result=}")
        return True

    def change_takeprofit(self, position: Position, price) -> bool:
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": int(position.exchange_id),
            "symbol": position.chart.symbol,
            "sl": position.stoploss,
            "tp": price,
        }

        result = mt5.order_send(request)
        if not result:
            logger.error(f"New TP Request Failed:{position=}\n{result=}")
            return False
        logging.debug(f"TP Changed of {position=}\n{result=}")
        return True

    def partial_close(self, position: Position, volume) -> float | None:
        if position.side == OrderSide.BUY:
            trade_side = mt5.ORDER_TYPE_BUY
        else:
            trade_side = mt5.ORDER_TYPE_SELL

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.chart.symbol,
            "position": int(position.exchange_id),
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

    def close_position(self, position: Position) -> float | None:
        if position.side == OrderSide.BUY:
            trade_side = mt5.ORDER_TYPE_BUY
        else:
            trade_side = mt5.ORDER_TYPE_SELL

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.chart.symbol,
            "position": int(position.exchange_id),
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
