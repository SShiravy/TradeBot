from ChartModule.models import Candle, Chart, ChartData
from LocalBackTester.models import CsvChart
from TraderBot.models import ExchangeAgent, Position
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import pandas as pd


class LocalAgent(ExchangeAgent):
    def prepare_chart(self, chart: CsvChart) -> bool:  # type: ignore[Override]
        """
        check symbol exist or not and
        change chart.precision
        """
        return Path(chart.csv_path).is_file()

    def get_chartdata(  # type: ignore[Override]
        self, chart: CsvChart, n_bars: int = 0
    ) -> ChartData | None:
        if not self.prepare_chart(chart):
            raise FileNotFoundError(
                f"CSV Chart: {chart} file not found in path: {chart.csv_path}"
            )

        df = pd.read_csv(chart.csv_path)
        float_cols = ["open", "high", "low", "close", "volume", "open_time"]
        df[float_cols] = df[float_cols].astype(float)

        candles = []
        timestamp_factor = 1000 if len(str(int(df.iloc[1]["open_time"]))) == 13 else 1
        for _, row in df.iloc[-n_bars:].iterrows():
            candle = Candle(
                time=datetime.fromtimestamp(
                    row["open_time"] / timestamp_factor, tz=timezone.utc
                ),
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
                timestamp=row["open_time"] / timestamp_factor,
            )
            candles.append(candle)
        candles.sort(key=lambda x: x.time)

        return ChartData(chart, candles)

    def get_candles_since(self, chart: Chart, time: datetime) -> list[Candle]:
        return super().get_candles_since(chart, time)

    def open_position(self, position: Position) -> float | None:
        """
        return executed price if successful otherwise None
        it should to return position id to executed order price
        """
        pass

    def get_open_positions(self, chart: Chart, *args, **kwargs) -> Any:
        pass

    def change_stoploss(self, position: Position, price: float) -> bool:
        return True

    def change_takeprofit(self, position: Position, price: float) -> bool:
        return True

    def partial_close(self, position: Position, volume: float) -> float | None:
        """
        return executed price if successful otherwise None
        """
        pass

    def close_position(self, position: Position) -> float | None:
        """
        return executed price if successful otherwise None
        """
        pass
