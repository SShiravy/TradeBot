from ChartModule import Chart, Candle, ChartData, TimeFrame
from TradingModule import ExchangeAgent, Position
from TradingModule.commands import ChangeTakeProfit, TrailStoploss
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
            kline_res = self.bitunix_api.get_kline(chart.symbol, chart.timeframe.value, limit=n_bars)
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
        pass

    def change_stoploss(self, position: Position, price) -> bool:
        return True

    def change_takeprofit(self, position: Position, price) -> bool:
        return True

    def partial_close(self, position: Position, volume):
        pass

    def close_position(self, position: Position):
        pass

    def get_open_positions(self, chart: Chart, *args, **kwargs):
        pass
