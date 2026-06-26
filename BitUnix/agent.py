from ChartModule import Chart, Candle, ChartData
from TradingModule import ExchangeAgent, Position
from BitUnix.api import BitUnixAPI
from datetime import datetime, timezone
import logging


logger = logging.getLogger("BitUnixAgent")


class BitUnixAgent(ExchangeAgent):
    def __init__(self, access_id: str, secret_key: str) -> None:
        self.bitunix_api = BitUnixAPI(access_id, secret_key)
        logger.info("Initialized")

    def get_chartdata(self, chart: Chart, n_bars=100) -> ChartData | None:
        try:
            kline_res = self.bitunix_api.get_kline(
                chart.symbol, chart.timeframe.value, limit=n_bars
            )
            if not kline_res:
                raise ValueError(f"{kline_res=}")
        except Exception as e:
            logger.error(f"fetching chart data failed: {e}")
            return None
        all_candles_list = []
        for candle in kline_res[::-1]:
            candle_timestamp = int(candle["time"])
            open = candle["open"]
            high = candle["high"]
            low = candle["low"]
            close = candle["close"]
            volume = candle["quoteVol"]
            candle_time = datetime.fromtimestamp(
                candle_timestamp / 1000, tz=timezone.utc
            )  # type: ignore

            all_candles_list.append(
                Candle(
                    float(open),
                    float(close),
                    float(high),
                    float(low),
                    float(volume),
                    candle_time,
                    candle_timestamp,
                    chart.timeframe,
                )
            )

        chartdata = ChartData(chart, all_candles_list)
        return chartdata

    def check_chart(self, chart: Chart) -> bool:
        return super().check_chart(chart)

    def get_candles_since(self, chart: Chart, time: datetime):
        return super().get_candles_since(chart, time)

    def open_position(self, position: Position):
        leverage_res = self.bitunix_api.change_leverage(
            position.chart.symbol, leverage=position.leverage
        )
        logger.info(f"{leverage_res=}")

        res = self.bitunix_api.place_order(
            position.chart.symbol,
            position.side.name,
            "MARKET",
            str(position.volume),
            client_id=str(position.id),
            tp_price=str(position.takeprofit) if position.takeprofit != 0 else None,
            tp_order_type="MARKET" if position.takeprofit != 0 else None,
            tp_stop_type="MARK" if position.takeprofit != 0 else None,
            sl_price=str(position.stoploss),
            sl_order_type="MARKET",
            sl_stop_type="MARK",
        )
        order_id = res.get("orderId")
        if not order_id:
            logger.error(f"Opening Position Failed: {position}")
            return None
        logger.info(f"open position: {res}")

        positions_res = self.bitunix_api.get_pending_positions(position.chart.symbol)
        if not positions_res:
            logger.warning(f"Getting Position Info failed: {positions_res}")

        poisition_info = positions_res[0]  # type: ignore
        position.exchange_id = poisition_info["positionId"]

        if len(position.steps) > 1:
            logger.info(f"place {len(position.steps)} tp")
            for step in position.steps[1:]:  # first step is entry
                logger.debug(f"place step {step}")
                step_res = self.bitunix_api.place_tp_sl_order(
                    position.chart.symbol,
                    position_id=position.exchange_id,
                    tp_qty=str(step.volume),
                    tp_price=str(step.price),
                    tp_stop_type="MARK_PRICE",
                )
                logger.debug(f"{step_res=}")

        # TODO: return order entry price
        # TODO: check tp sl and modify it

        return poisition_info["avgOpenPrice"]

    def change_stoploss(self, position: Position, price) -> bool:
        res = self.bitunix_api.change_position_tp_sl_order(
            position.chart.symbol,
            position_id=position.exchange_id,
            sl_price=str(price),
            sl_stop_type="MARK",
        )
        logging.debug(f"Change SL for {position.exchange_id=} | {res=}")
        return True

    def change_takeprofit(self, position: Position, price) -> bool:
        return True

    def partial_close(self, position: Position, volume):
        pass

    def close_position(self, position: Position):
        pass

    def get_open_positions(self, chart: Chart, *args, **kwargs):
        pass
