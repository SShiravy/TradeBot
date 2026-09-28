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
from ExchangeAgents.BitUnix.api import BitUnixAPI, BitUnixAPIError
import logging


logger = logging.getLogger("BitUnixAgent")


class BitUnixAgent(ExchangeAgent):
    """
    Hedge mode. A Position is one bitunix position: a market order opens the volume
    of its take profit triggers, each trigger gets a tp order closing its volume and
    the stoploss is the position tp/sl, which closes whatever is left.
    """

    def __init__(
        self, api_key: str, secret_key: str, stop_type: str = "MARK_PRICE"
    ) -> None:
        self.api = BitUnixAPI(api_key, secret_key)
        self.stop_type = stop_type
        self.qty_precisions: dict[str, int] = {}
        # realized pnl of each bitunix position already reported
        self.reported_pnl: dict[str, float] = {}
        logger.info("Initialized")

    def prepare_chart(self, chart: Chart) -> bool:
        pairs = self.api.get_trading_pairs(chart.symbol)
        if not pairs:
            raise RuntimeError(f"Failed to get symbol info for {chart.symbol}")
        pair = pairs[0]
        chart.precision = int(pair["quotePrecision"])
        chart.pip_factor = round(10.0 ** (1 - chart.precision), chart.precision)
        chart.contract_size = 1  # volumes are in the base coin
        self.qty_precisions[chart.symbol] = int(pair["basePrecision"])
        logger.debug(f"{chart=}")
        return True

    def get_chartdata(self, chart: Chart, n_bars: int = 100) -> ChartData | None:
        # bitunix gives closed candles only, newest first and 200 per request
        candles: dict[int, dict] = {}
        end_time = None
        n_closed = max(n_bars - 1, 1)
        try:
            while len(candles) < n_closed:
                page = self.api.get_kline(
                    chart.symbol,
                    chart.timeframe.value,
                    min(200, n_closed - len(candles)),
                    end_time,
                )
                if not page or int(page[-1]["time"]) // 1000 in candles:
                    break
                candles.update({int(c["time"]) // 1000: c for c in page})
                # the oldest open time, an unaligned end time makes bitunix skip a candle
                end_time = int(page[-1]["time"])
        except BitUnixAPIError as error:
            logger.error(f"fetching chart data failed: {chart=}\n{error}")
            return None
        if not candles:
            logger.error(f"fetching chart data failed: {chart=}")
            return None

        timestamps = sorted(candles)
        rows = [candles[t] for t in timestamps]
        # mt5 and other exchanges gives the not closed candle as the last one and the bots drop it so we add one dummy candle at the end
        last_close = float(rows[-1]["close"])
        timestamps.append(timestamps[-1] + chart.timeframe.minutes * 60)
        rows.append(
            {
                "open": last_close,
                "high": last_close,
                "low": last_close,
                "close": last_close,
                "baseVol": 0,
            }
        )
        return ChartData(
            chart=chart,
            timestamps=np.array(timestamps, dtype=np.int64),
            open=np.array([float(r["open"]) for r in rows]),
            high=np.array([float(r["high"]) for r in rows]),
            low=np.array([float(r["low"]) for r in rows]),
            close=np.array([float(r["close"]) for r in rows]),
            volume=np.array([float(r["baseVol"]) for r in rows]),
        )

    def _last_price(self, symbol: str) -> float:
        return float(self.api.get_tickers(symbol)[0]["lastPrice"])

    def get_candles_since(self, chart: Chart, timestamp: int):
        return super().get_candles_since(chart, timestamp)

    def get_current_tick(self, chart: Chart, side: PositionSide | None = None) -> float:
        try:
            depth = self.api.get_depth(chart.symbol)
        except BitUnixAPIError as error:
            raise LookupError(f"Failed to get tick data for {chart.symbol}") from error
        ask = float(depth["asks"][0][0])
        bid = float(depth["bids"][0][0])
        if side is PositionSide.LONG:
            return ask
        if side is PositionSide.SHORT:
            return bid
        return (ask + bid) / 2

    def _qty(self, position: Position, volume: float) -> str:
        precision = self.qty_precisions.get(position.chart.symbol, 8)
        return f"{volume:.{precision}f}"

    def _price(self, position: Position, price: float) -> str:
        return f"{price:.{position.chart.precision}f}"

    def open_position(self, position: Position) -> float | None:
        symbol = position.chart.symbol
        side = "BUY" if position.side is PositionSide.LONG else "SELL"
        triggers = [t for t in position.steps if isinstance(t.event, TakeProfitHit)]
        try:
            self.api.change_leverage(symbol, position.leverage)
        except BitUnixAPIError as error:
            logger.warning(f"Changing leverage of {symbol} failed: {error}")

        try:
            res = self.api.place_order(
                symbol, side, "MARKET", self._qty(position, position.volume), "OPEN"
            )
            logger.info(f"Market order of {position}: {res}")
            rows = self.api.get_pending_positions(symbol)
            row = next(r for r in rows if r["side"] == position.side.name)
        except (BitUnixAPIError, StopIteration) as error:
            logger.error(f"Opening position failed: {position}\n{error}")
            return None
        position.exchange_id = str(row["positionId"])
        position.volume = float(row["qty"])
        position.stoploss.volume = position.volume
        self.reported_pnl[position.exchange_id] = 0.0

        try:
            res = self.api.place_position_tp_sl_order(
                symbol,
                position.exchange_id,
                self._price(position, position.stoploss.price),
                self.stop_type,
            )
            position.stoploss.exchange_id = str(res.get("orderId", ""))
        except BitUnixAPIError as error:
            logger.error(f"Placing stoploss failed: {position}\n{error}")

        for trigger in triggers:
            try:
                res = self.api.place_tp_sl_order(
                    symbol,
                    position.exchange_id,
                    tp_price=self._price(position, trigger.price),
                    tp_qty=self._qty(position, trigger.volume),
                    stop_type=self.stop_type,
                )
                trigger.exchange_id = str(res["orderId"])
            except (BitUnixAPIError, KeyError) as error:
                logger.error(f"Placing trigger {trigger.price} failed: {error}")
        logger.info(f"Position Opened: {position}")
        return round(float(row["avgOpenPrice"]), position.chart.precision)

    def change_stoploss(self, position: Position, price) -> bool:
        try:
            self.api.modify_position_tp_sl_order(
                position.chart.symbol,
                position.exchange_id,
                self._price(position, price),
                self.stop_type,
            )
        except BitUnixAPIError as error:
            if error.code == 30004:  # position doesn't exist, already closed
                return True
            logger.error(f"New SL Request Failed:{position=}\n{error}")
            return False
        logger.debug(f"SL Changed of {position=}")
        return True

    def change_takeprofit(self, position: Position, price) -> bool:
        # the farthest trigger not hit yet
        trigger = next(
            (
                t
                for t in position.steps[::-1]
                if t.exchange_id and not t.triggered_timestamp
            ),
            None,
        )
        if trigger is None:
            return False
        try:
            self.api.modify_tp_sl_order(
                trigger.exchange_id,
                self._price(position, price),
                self._qty(position, trigger.volume),
                self.stop_type,
            )
        except BitUnixAPIError as error:
            logger.error(f"New TP Request Failed:{position=}\n{error}")
            return False
        logger.debug(f"TP Changed of {position=}")
        return True

    def bitunix_to_position(self, row: dict) -> Position:
        side = PositionSide.LONG if row["side"] == "LONG" else PositionSide.SHORT
        volume = float(row["qty"])
        pos = Position(
            chart=Chart(row["symbol"], TimeFrame.one_minute),
            side=side,
            entry_price=float(row["avgOpenPrice"]),
            volume=volume,
            stoploss=Trigger(0.0, StopLossHit(), volume, -side.factor),
            triggers=[],
            leverage=int(row.get("leverage") or 1),
            source="BitUnix",
        )
        pos.exchange_id = str(row["positionId"])
        return pos

    def get_open_positions(self, chart: Chart | None = None) -> list[Position]:
        try:
            rows = self.api.get_pending_positions(chart.symbol if chart else None)
        except BitUnixAPIError as error:
            logger.error(f"Getting open positions failed: {error}")
            return []
        return [self.bitunix_to_position(row) for row in rows or []]

    def check_position_closed(self, position: Position):
        """
        A trigger whose tp order is gone is hit. What closed since the last check is
        reported from bitunix realized pnl, shared by volume between the hit
        triggers and, once the position is closed, the stoploss
        """
        symbol = position.chart.symbol
        waiting = [
            t
            for t in position.steps
            if isinstance(t.event, TakeProfitHit)
            and t.exchange_id
            and not t.triggered_timestamp
        ]
        try:
            rows = self.api.get_pending_positions(symbol, position.exchange_id)
            row = next(
                (r for r in rows or [] if r["positionId"] == position.exchange_id), None
            )
            if row is not None:
                if float(row["qty"]) >= position.stoploss.volume:
                    return None  # nothing closed yet
                pending = {
                    str(o["id"])
                    for o in self.api.get_pending_tp_sl_orders(
                        symbol, position.exchange_id
                    )
                }
                hits = [t for t in waiting if t.exchange_id not in pending]
                hit_volume = sum(t.volume for t in hits)
                if (
                    not hits
                    or float(row["qty"]) > position.stoploss.volume - hit_volume
                ):
                    # the tp fills aren't on the position yet, or it's closed by hand,
                    # which the stoploss report sums once the position is closed
                    return None
                pnl = float(row["realizedPNL"]) - float(row["fee"])
                sl_volume = 0.0
            else:
                history = self.api.get_history_positions(symbol, position.exchange_id)
                if not history:
                    return None  # not settled yet
                pnl = (
                    float(history[0]["realizedPNL"])
                    - float(history[0]["fee"])
                    + float(history[0].get("funding") or 0)
                )
                statuses = {
                    str(o["id"]): o.get("status", "")
                    for o in self.api.get_history_tp_sl_orders(symbol)
                }
                # the stoploss cancels the tp orders left, a triggered one is filled
                hits = [t for t in waiting if statuses.get(t.exchange_id) == "FILLED"]
                hit_volume = sum(t.volume for t in hits)
                sl_volume = round(position.stoploss.volume - hit_volume, 8)
        except BitUnixAPIError as error:
            logger.error(f"Checking {position} failed: {error}")
            return None

        new_pnl = pnl - self.reported_pnl.get(position.exchange_id, 0.0)
        self.reported_pnl[position.exchange_id] = pnl
        closed_volume = hit_volume + sl_volume
        now = TimeHandler.now()
        position.last_check_timestamp = now
        final_report = None
        for trigger in hits:
            report = PnLReportGenerator.from_pnl(
                position, new_pnl * trigger.volume / closed_volume, trigger.volume
            )
            final_report += report
            trigger.triggered_timestamp = now
            if isinstance(trigger.event, TakeProfitHit):
                trigger.event.pnl_report = report
            position.stoploss.volume = round(
                position.stoploss.volume - trigger.volume, 8
            )
        if sl_volume > 0:
            report = PnLReportGenerator.from_pnl(
                position, new_pnl * sl_volume / closed_volume, sl_volume
            )
            final_report += report
            if isinstance(position.stoploss.event, StopLossHit):
                position.stoploss.event.pnl_report += report
        if row is None:
            self.reported_pnl.pop(position.exchange_id, None)
        logger.info(f"{position.exchange_id=}|{len(hits)=}|{sl_volume=}|{new_pnl=}")
        return final_report

    def partial_close(self, position: Position, volume) -> float | None:
        pass

    def close_position(self, position: Position) -> float | None:
        pass
