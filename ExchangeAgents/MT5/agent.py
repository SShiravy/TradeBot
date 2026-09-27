import numpy as np
from ChartModule import Chart, ChartData, TimeFrame
from Settings.timing import TimeHandler
from TraderBot.PositionHandlers.trades_pnl import PnLReportGenerator
from TraderBot.events import StopLossHit, TakeProfitHit
from TraderBot.models import (
    ExchangeAgent,
    Position,
    PositionSide,
    Trigger,
)
from datetime import timedelta
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

    def __new__(cls, mt5_terminal_path: str, utc_shift: int | None = None):
        if not hasattr(cls, "_instance"):
            cls._instance = object.__new__(cls)
            if not mt5.initialize(mt5_terminal_path):
                raise RuntimeError("MT5 initialize failed")
            logger.info("Initialized")
            cls.last_checked_timestamp: None | int = None
            cls.market_state: MarketState = MarketState.CHECK_LATER
            if utc_shift:
                cls._UTC_SHIFT = utc_shift
            else:
                cls.set_utc_shift()
        return cls._instance

    @classmethod
    def select_chart(cls, chart: Chart) -> bool:
        if not mt5.symbol_select(chart.symbol, True):
            symbols = mt5.symbols_get()
            for s in symbols:
                if chart.symbol.lower() in s.name.lower():
                    chart.symbol = s.name
                    mt5.symbol_select(chart.symbol, True)
                    return True
            raise ValueError(f"Failed to select symbol {chart.symbol}")
        return True

    @classmethod
    def set_utc_shift(cls, symbol: str = "BTCUSD") -> int:
        chart = Chart(symbol, TimeFrame.one_minute)
        cls.select_chart(chart)
        info = mt5.symbol_info(chart.symbol)
        if not info:
            raise ValueError(f"{chart=} | {info=}")
        cls._UTC_SHIFT = TimeHandler.now() - info.time
        return cls._UTC_SHIFT

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
            timestamps=ohlcv_res["time"].astype(np.int64) + self._UTC_SHIFT,
            open=ohlcv_res["open"].astype(np.float64),
            high=ohlcv_res["high"].astype(np.float64),
            low=ohlcv_res["low"].astype(np.float64),
            close=ohlcv_res["close"].astype(np.float64),
            volume=ohlcv_res["tick_volume"].astype(np.float64),
        )

    def get_candles_since(self, chart: Chart, timestamp: int):
        return super().get_candles_since(chart, timestamp)

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
            if not isinstance(trigger.event, TakeProfitHit) or trigger.exchange_id:
                continue
            # Build request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.chart.symbol,
                "volume": trigger.volume,
                "type": trade_side,
                "price": price,
                "sl": position.stoploss.price,
                "tp": trigger.price,
                "deviation": 20,
                "magic": 80713,
                "comment": position.source,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
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
        if not entry_prices:
            logger.warning(f"Fail on Opening Position {position}")
        position.exchange_id = exchange_id if exchange_id else ""
        if not entry_prices:
            return None
        return round(sum(entry_prices) / len(entry_prices), position.chart.precision)

    def change_stoploss(self, position: Position, price) -> bool:
        for trigger in position.triggers:
            if trigger.triggered_timestamp:  # its exchange position is closed
                continue
            if not isinstance(trigger.event, TakeProfitHit) or not trigger.exchange_id:
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

    def get_current_tick(self, chart: Chart, side: PositionSide | None = None) -> float:
        if not self.select_chart(chart):
            raise LookupError(f"Failed to select {chart=}")

        tick = mt5.symbol_info_tick(chart.symbol)
        if tick is None:
            raise LookupError(f"Failed to get tick data for {chart.symbol}")

        if side is PositionSide.LONG:
            price = tick.ask
        elif side is PositionSide.SHORT:
            price = tick.bid
        else:
            price = (tick.ask + tick.bid) / 2

        return price

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
            stoploss=Trigger(mt5_pos.sl, StopLossHit(), mt5_pos.volume, side.factor),
            triggers=[
                Trigger(mt5_pos.tp, TakeProfitHit(), mt5_pos.volume, side.factor)
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

    def check_position_closed(self, position: Position):
        final_report = None
        sl_report = None
        day = int(timedelta(days=1).total_seconds())
        all_deals = mt5.history_deals_get(
            position.defined_timestamp - day,
            TimeHandler.now() + day,
        )
        for trigger in position.steps:
            if trigger.triggered_timestamp or not isinstance(
                trigger.event, TakeProfitHit
            ):
                continue

            ticket = int(trigger.exchange_id)

            if mt5.positions_get(ticket=ticket):
                continue

            # with a date range mt5 ignores the position filter and returns all deals
            deals = [d for d in all_deals or [] if d.position_id == ticket]
            if not deals:
                logger.warning(f"{ticket=} isn't open but no deals found for it yet")
                continue

            exits_pnl = []
            exits_volume = []
            tp_hit = False
            for deal in deals:
                if deal.reason == mt5.DEAL_REASON_EXPERT:
                    continue
                # many brokers charge commission on the entry deal. so pnl sum up all values
                if deal.entry in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_OUT_BY):
                    exits_volume.append(deal.volume)
                    tp_hit = deal.reason == mt5.DEAL_REASON_TP
                exits_pnl.append(deal.profit + deal.commission + deal.swap + deal.fee)

            pnl = sum(exits_pnl)
            volume = sum(exits_volume)
            if volume < trigger.volume:
                logger.debug(
                    f"Trigger doesn't filled yet. filled {volume=}|{trigger.volume=}"
                )
                continue
            now = TimeHandler.now()
            position.last_check_timestamp = now
            report = PnLReportGenerator.from_pnl(position, pnl, volume)
            final_report += report
            if tp_hit:
                trigger.triggered_timestamp = now
                trigger.event.pnl_report = report
                position.stoploss.volume = round(position.stoploss.volume - volume, 8)
            else:
                # left untriggered (not a tp), so it's summed again next check
                sl_report += report
            logger.info(f"{ticket=}|{tp_hit=}|{exits_pnl=}|{exits_volume}|{pnl}")

        if sl_report and isinstance(position.stoploss.event, StopLossHit):
            position.stoploss.event.pnl_report += sl_report
        return final_report


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
