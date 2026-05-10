from ChartModule import Chart, Candle, ChartData, TimeFrame
from TradingModule import ExchangeAgent, Position
from TradingModule.commands import ChangeTakeProfit, TrailStoploss
from Coinex.api import CoinexFuturesAPI, CoinexTimeFrame
from datetime import datetime, timezone
import logging


logger = logging.getLogger("CoinexAgent")


class CoinexAgent(ExchangeAgent):
    def __init__(self, access_id: str, secret_key: str) -> None:
        self.coinex_api = CoinexFuturesAPI(access_id, secret_key)
        logger.info("Initialized")

    def check_chart(self, chart: Chart) -> bool:
        info = self.coinex_api.get_market_info(chart.symbol)
        if not info:
            return False
        chart.precision = info[0]["quote_ccy_precision"]
        return True

    def get_chartdata(self, chart: Chart, n_bars=100) -> ChartData | None:
        timeframe = coinex_timeframe_mapper(chart.timeframe)
        if not timeframe:
            logger.error(f"{chart.timeframe.value} not exist in coinex api")
        try:
            kline_res = self.coinex_api.get_kline(chart.symbol, timeframe, limit=n_bars)  # type: ignore
            if not kline_res:
                raise ValueError(f"{kline_res=}")
        except Exception as e:
            logger.error(f"fetching chart data failed: {e}")
            return None
        all_candles_list = []
        for candle in kline_res:
            candle_timestamp = candle.get("created_at")
            open = candle["open"]
            high = candle["high"]
            low = candle["low"]
            close = candle["close"]
            volume = candle["volume"]
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

    def get_candles_since(self, chart: Chart, time: datetime):
        return super().get_candles_since(chart, time)

    def open_position(self, position: Position):
        self.coinex_api.set_leverage(position.chart.symbol, position.leverage)

        order_result = self.coinex_api.place_order(
            position.chart.symbol,
            position.side.value.lower(),
            type="market",
            amount=position.volume,
        )

        if order_result is None:
            logger.error(f"Opening Position Failed: {position}")
            return None

        pos_id = order_result["created_at"]
        position.exchange_id = pos_id

        sl_res = self.change_stoploss(position, position.stoploss)
        tp_res = self.change_takeprofit(position, position.takeprofit)

        if not sl_res:
            TrailStoploss(position, self, position.stoploss)
        if not tp_res:
            ChangeTakeProfit(position, self, position.takeprofit)

        logging.info(f"Position Opened: {position}\n{order_result=}")
        entry_price = float(order_result["last_filled_price"])

        return entry_price

    def change_stoploss(self, position: Position, price) -> bool:
        res = self.coinex_api.place_stoploss(position.chart.symbol, price)
        if not res:
            logger.error(f"New SL Request Failed:{position=}\n{res=}")
            return False
        logging.debug(f"SL Changed of {position=}\n{res=}")
        return True

    def change_takeprofit(self, position: Position, price) -> bool:
        res = self.coinex_api.place_takeprofit(position.chart.symbol, price)
        if not res:
            logger.error(f"New TP Request Failed:{position=}\n{res=}")
            return False
        logging.debug(f"TP Changed of {position=}\n{res=}")
        return True

    def partial_close(self, position: Position, volume):
        res = self.coinex_api.close_position(position.chart.symbol, amount=volume)
        if not res:
            logger.error(f"Partial Close Failed: {position}\n{res=}")
            return None
        logging.debug(f"Partial Close for {position=}\n{res=}")
        return float(res["last_filled_price"])

    def close_position(self, position: Position):
        """
        return executed price if successful otherwise None
        """
        res = self.coinex_api.close_position(position.chart.symbol, amount="")
        if not res:
            logger.error(f"Close Position Failed: {position}\n{res=}")
            return None
        logging.debug(f"Position Close for {position=}\n{res=}")
        return res["last_filled_price"]

    def get_open_positions(self, chart: Chart):
        pass


def coinex_timeframe_mapper(timeframe: TimeFrame):
    match timeframe:
        case TimeFrame.one_minute:
            return CoinexTimeFrame.ONE_MINUTE
        case TimeFrame.three_minutes:
            return CoinexTimeFrame.THREE_MINUTES
        case TimeFrame.five_minutes:
            return CoinexTimeFrame.FIVE_MINUTES
        case TimeFrame.fifteen_minutes:
            return CoinexTimeFrame.FIFTEEN_MINUTES
        case TimeFrame.thirty_minutes:
            return CoinexTimeFrame.THIRTY_MINUTES
        case TimeFrame.one_hour:
            return CoinexTimeFrame.ONE_HOUR
        case TimeFrame.two_hours:
            return CoinexTimeFrame.TWO_HOURS
        case TimeFrame.four_hours:
            return CoinexTimeFrame.FOUR_HOURS
        case TimeFrame.six_hours:
            return CoinexTimeFrame.SIX_HOURS
        case TimeFrame.twelve_hours:
            return CoinexTimeFrame.TWELVE_HOURS
        case TimeFrame.one_day:
            return CoinexTimeFrame.ONE_DAY
        case TimeFrame.one_week:
            return CoinexTimeFrame.ONE_WEEK
    return None
