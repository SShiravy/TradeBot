import numpy as np

from ChartModule import Chart, ChartData, TimeFrame
from Settings.timing import TimeHandler
from TraderBot.models import ExchangeAgent, Position, PositionSide, Trigger, TriggerType
from datetime import datetime, timedelta, timezone
from Settings.config import settings
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
                return 900  # wait for 15m and check again
            case MarketState.CHECK_LATER:
                return 10  # wait for 1m and check again
            case MarketState.NOT_RESPONDING:
                return 240  # wait for 4m and check again
            case _:
                return 1800  # default 30m wait time


class MT5Agent(ExchangeAgent):
    _UTC_SHIFT: int = 0

    def __new__(cls, mt5_terminal_path: str = settings.METATRADER_TERMINAL_PATH):
        if not hasattr(cls, "_instance"):
            cls._instance = object.__new__(cls)
            if not mt5.initialize(mt5_terminal_path):
                raise RuntimeError("MT5 initialize failed")
            logger.info("Initialized")
            cls.last_checked_timestamp: None | int = None
            cls.market_state: MarketState = MarketState.CHECK_LATER
        return cls._instance

    def select_chart(self, chart: Chart) -> bool:
        if not mt5.symbol_select(chart.symbol, True):
            symbols = mt5.symbols_get()
            for s in symbols:
                if chart.symbol.lower() in s.name.lower():
                    chart.symbol = s.name
                    mt5.symbol_select(chart.symbol, True)
                    return True
            raise ValueError(f"Failed to select symbol {chart.symbol}")
        return True

    def prepare_chart(self, chart: Chart) -> bool:
        self.select_chart(chart)
        symbol_info = mt5.symbol_info(chart.symbol)
        if symbol_info is None:
            raise RuntimeError(f"Failed to get symbol info for {chart.symbol}")
        chart.pip_factor = symbol_info.point * 10
        chart.precision = symbol_info.digits
        chart.contract_size = symbol_info.trade_contract_size
        logger.debug(f"{chart=}")
        return True

    @classmethod
    def set_utc_shift(cls, chart: Chart) -> int:
        info = mt5.symbol_info(chart.symbol)
        if not info:
            raise ValueError(f"{chart=} | {info=}")
        cls._UTC_SHIFT = TimeHandler.now() - info.time
        return cls._UTC_SHIFT

    @classmethod
    def give_current_timestamp(cls, chart: Chart):
        info = mt5.symbol_info(chart.symbol)
        if not info:
            logger.error(
                f"Failed to get chart info for market open check: {chart=} | {info=}"
            )
            return 0
        return info.time

    def check_market_open(self, chart: Chart) -> None | int:
        """
        :return: None if market open or seconds to wait if market closed
        :rtype: int | None
        """
        current_timestamp = self.give_current_timestamp(chart)

        if current_timestamp == 0:
            self.market_state = MarketState.NOT_RESPONDING

        elif self.last_checked_timestamp is None:
            self.last_checked_timestamp = current_timestamp
            self.market_state = MarketState.CHECK_LATER

        elif self.last_checked_timestamp == current_timestamp:
            if self.market_state != MarketState.CHECK_LATER:
                self.market_state = MarketState.CLOSED

        else:
            self.market_state = MarketState.OPEN
            self.last_checked_timestamp = current_timestamp

        if self.market_state != MarketState.OPEN:
            logger.debug(f"Market State = {self.market_state}")
        return self.market_state.wait_seconds()

    def get_chartdata(self, chart: Chart, n_bars: int = 100) -> ChartData | None:
        if not self.select_chart(chart):
            return None
        ohlcv_res = mt5.copy_rates_from_pos(
            chart.symbol, forex_timeframe_mapper(chart.timeframe), 0, n_bars
        )
        if ohlcv_res is None:
            logger.error(f"fetching chart data failed: {chart=}")
            return None
        return ChartData(
            chart=chart,
            timestamps=ohlcv_res["time"].astype(np.int64) + self.set_utc_shift(chart),
            open=ohlcv_res["open"].astype(np.float64),
            high=ohlcv_res["high"].astype(np.float64),
            low=ohlcv_res["low"].astype(np.float64),
            close=ohlcv_res["close"].astype(np.float64),
            volume=ohlcv_res["tick_volume"].astype(np.float64),
        )

    def get_candles_since(self, chart: Chart, time: datetime):
        return super().get_candles_since(chart, time)

    def open_position(self, position: Position) -> float | None:
        if not self.select_chart(position.chart):
            return None

        tick = mt5.symbol_info_tick(position.chart.symbol)
        if tick is None:
            logger.error(f"Forex Failed to get tick data for {position.chart.symbol}")
            return None

        if position.side == PositionSide.LONG:
            price = tick.ask
            trade_side = mt5.ORDER_TYPE_BUY
        else:
            price = tick.bid
            trade_side = mt5.ORDER_TYPE_SELL

        exchange_id = None
        entry_prices = []
        for trigger in position.triggers:
            if trigger.type != TriggerType.TP or trigger.exchange_id:
                continue
            # Build request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.chart.symbol,
                "volume": trigger.volume,
                "type": trade_side,
                "price": price,
                "sl": position.stoploss,
                "tp": trigger.price,
                "deviation": 20,
                "magic": 80713,
                "comment": position.source,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            if not result or not result.request_id:
                logger.error(
                    f"Opening position failed: {position}\n{mt5.last_error()=}"
                )
                return None
            exchange_id = str(result.order)
            trigger.exchange_id = exchange_id
            entry_prices.append(result.price)
            logger.info(f"Position Opened: {position}\n{result=}")
        position.exchange_id = exchange_id if exchange_id else ""
        return round(sum(entry_prices) / len(entry_prices), position.chart.precision)

    def change_stoploss(self, position: Position, price) -> bool:
        for trigger in position.triggers:
            if trigger.type != TriggerType.TP or not trigger.exchange_id:
                continue
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": int(trigger.exchange_id),
                "symbol": position.chart.symbol,
                "sl": price,
                "tp": trigger.price,
            }

            result = mt5.order_send(request)
            if not result:
                logger.error(f"New SL Request Failed:{position=}\n{result=}")
                return False
        logger.debug(f"SL Changed of {position=}")
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
        logger.debug(f"TP Changed of {position=}\n{result=}")
        return True

    # TODO: implement below methods

    def get_current_tick(self, chart: Chart) -> float:
        return 0.0

    def partial_close(self, position: Position, volume) -> float | None:
        # if position.side == PositionSide.LONG:
        #     trade_side = mt5.ORDER_TYPE_BUY
        # else:
        #     trade_side = mt5.ORDER_TYPE_SELL

        # request = {
        #     "action": mt5.TRADE_ACTION_DEAL,
        #     "symbol": position.chart.symbol,
        #     "position": int(position.exchange_id),
        #     "type": trade_side,
        #     "volume": volume,
        #     "deviation": 20,
        # }

        # result = mt5.order_send(request)
        # if not result:
        #     logger.error(f"Partial Close Request Failed:{position=}\n{result=}")
        #     return None
        # logger.debug(f"Partial Close for {position=}\n{result=}")
        # return result.price
        pass

    def close_position(self, position: Position) -> float | None:
        # if position.side == PositionSide.LONG:
        #     trade_side = mt5.ORDER_TYPE_BUY
        # else:
        #     trade_side = mt5.ORDER_TYPE_SELL

        # request = {
        #     "action": mt5.TRADE_ACTION_DEAL,
        #     "symbol": position.chart.symbol,
        #     "position": int(position.exchange_id),
        #     "type": trade_side,
        #     "volume": position.volume,
        #     "deviation": 20,
        # }

        # result = mt5.order_send(request)
        # if not result:
        #     logger.error(f"Close Position Failed: {position}\n{result=}")
        #     return None
        # logger.debug(f"Position Close for {position=}\n{result=}")
        # return result.price
        pass

    def mt5_trade_to_position(self, mt5_pos: mt5.TradePosition) -> Position:
        side = (
            PositionSide.LONG
            if mt5_pos.type == mt5.ORDER_TYPE_BUY
            else PositionSide.SHORT
        )
        pos = Position(
            chart=Chart(mt5_pos.symbol, TimeFrame.one_minute),
            side=side,
            entry_price=mt5_pos.price_open,
            volume=mt5_pos.volume,
            stoploss=Trigger(
                mt5_pos.sl, mt5_pos.volume, side.factor, type=TriggerType.SL
            ),
            triggers=[
                Trigger(mt5_pos.tp, mt5_pos.volume, side.factor, type=TriggerType.TP)
            ],
            leverage=mt5_pos.volume,  # / mt5_pos.volume_real,  # type: ignore
            source=f"MetaTrader|{mt5_pos.comment}",
        )
        pos.exchange_id = str(mt5_pos.ticket)
        return pos

    def get_open_positions(
        self,
        chart: Chart | None = None,
        position_ticket: int | None = None,
        comment_filter: str = "",
    ) -> list[Position]:
        open_poses = mt5.positions_get(ticket=position_ticket)
        if not open_poses:
            return []
        filtered_poses = []
        for pos in open_poses:
            if comment_filter:
                if comment_filter not in pos.comment:
                    continue
            filtered_poses.append(self.mt5_trade_to_position(pos))
            logger.debug(f"mt5 filtered open pos: {open_poses}")
        return filtered_poses

    def check_position_closed(
        self,
        position_ticket: int | None = None,
        comment_filter: str = "",
    ) -> float | None:
        if not position_ticket and not comment_filter:
            logger.error("No Ticket nor comment_filter is given")
            return None
        position = mt5.positions_get(ticket=position_ticket)
        if position:
            return None
        to_time = datetime.now(timezone.utc)
        from_time = to_time - timedelta(days=3)
        deals = mt5.history_deals_get(from_time, to_time, ticket=position_ticket)
        if not deals:
            raise ValueError(
                f"Position isn't open but no deals found for ticket {position_ticket}"
            )
        profit = sum(d.profit + d.commission + d.swap for d in deals)
        logger.debug(
            f"Deals found for closed position {position_ticket}: {deals} \n{profit=}"
        )
        return profit


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
