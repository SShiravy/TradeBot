from typing import Any
from Settings.timing import TimeHandler
from TraderBot.models import (
    PnLReport,
    Position,
    PositionSide,
    ReportMsgFormater,
    ReporterBot,
)
from ChartModule.models import Candle, Chart, ChartData, Signal, TimeFrame
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
import logging

from TraderBot.models import ExchangeAgent, Position

logger = logging.getLogger("Backtest")


class KlineSource(Enum):
    BINCANCE = "binance"
    OPOFINANCE_META = "opofinance"
    OTET_Meta = "otet"
    DUKASCOPY = "dukascopy"
    OTHER = "other"


class TickDataHandler:
    def __init__(
        self,
        parquet_path: str,
    ):
        logger.info(f"Reading TickData from: {parquet_path}")
        self.df = pd.read_parquet(
            parquet_path,
        )

        self.df = self.df.sort_values(
            "time",
        )

        self.timestamps = self.df["time"].to_numpy(dtype=np.int64)

    def get_ticks_from_timstamp_range(
        self,
        start_timestamp: int,
        end_timestamp: int,
    ) -> pd.DataFrame:
        left = np.searchsorted(
            self.timestamps,
            start_timestamp,
            side="left",
        )

        right = np.searchsorted(
            self.timestamps,
            end_timestamp + 1,
            side="left",
        )

        return self.df.iloc[left:right]

    def get_ticks_for_candle(self, candle: Candle, chart: Chart) -> pd.DataFrame:
        start_ts = candle.timestamp
        end_ts = start_ts + chart.timeframe.minutes * 60
        return self.get_ticks_from_timstamp_range(start_ts, end_ts)


@dataclass(slots=True)
class CsvChart(Chart):
    csv_path: str = field(default="")
    csv_source: KlineSource = field(default=KlineSource.OTHER)
    ticks_path: str | None = field(default=None)
    _tick_handler: TickDataHandler | None = field(default=None, init=False)

    def __str__(self) -> str:
        return f"Csv_{self.symbol}_{self.timeframe.value}{self.chart_type.value}"

    def export_config(self) -> dict:
        conf_dict = super(CsvChart, self).export_config()
        conf_dict.update(
            {
                "csv_path": self.csv_path,
                "csv_source": self.csv_source.value,
                "ticks_path": self.ticks_path,
            }
        )
        return conf_dict

    @property
    def total_bars_number(self) -> int:
        return len(pd.read_csv(self.csv_path))

    @property
    def tick_handler(self) -> TickDataHandler:
        if self.ticks_path is None:
            raise ValueError("ticks_path is not set for CsvChart")
        if self._tick_handler is None:
            self._tick_handler = TickDataHandler(self.ticks_path)
        return self._tick_handler


class BacktestAgent(ExchangeAgent):
    def __init__(self, real_agent: ExchangeAgent, csv_charts: list[CsvChart]) -> None:
        self.real_agent = real_agent
        data_dict = {}
        self.last_timestamp
        for chart in csv_charts:
            data_dict[str(chart)] = self.from_csv(chart)

        self.data_dict = data_dict

    @classmethod
    def from_csv(cls, chart: CsvChart, use_tick_volume: bool = False) -> "ChartData":
        volume_key = "tick_volume" if use_tick_volume else "volume"
        df = pd.read_csv(chart.csv_path)

        return ChartData(
            chart=chart,
            timestamps=df["open_time"].to_numpy(dtype=np.int64),
            open=df["open"].to_numpy(dtype=np.float64),
            high=df["high"].to_numpy(dtype=np.float64),
            low=df["low"].to_numpy(dtype=np.float64),
            close=df["close"].to_numpy(dtype=np.float64),
            volume=df[volume_key].to_numpy(dtype=np.float64),
        )

    def _find_chartdata(self, chart: CsvChart | Chart) -> ChartData:
        """
        The csv data of chart. A plain Chart, like the 1m one TradesManager
        checks positions on, gets the loaded data of its symbol and timeframe,
        or the symbol's finest timeframe when that one is not loaded.
        """
        chartdata = self.data_dict.get(str(chart))
        if chartdata is not None:
            return chartdata
        same_symbol = [
            data
            for data in self.data_dict.values()
            if data.chart.symbol == chart.symbol
        ]
        if not same_symbol:
            raise KeyError(f"no csv data loaded for {chart}")
        for data in same_symbol:
            if data.chart.timeframe == chart.timeframe:
                return data
        return min(same_symbol, key=lambda data: data.chart.timeframe.minutes)

    def _running_candle(self, chart: Chart) -> tuple[int, float]:
        """(timestamp, open) of the symbol's candle running at TimeHandler.now()"""
        chartdata = self._find_chartdata(Chart(chart.symbol, TimeFrame.one_minute))
        idx = int(np.searchsorted(chartdata.timestamps, TimeHandler.now(), "right"))
        idx = max(idx - 1, 0)
        return int(chartdata.timestamps[idx]), float(chartdata.open[idx])

    def first_n_candle(self, chart: CsvChart | Chart, n_candle: int = 150) -> ChartData:
        return self._find_chartdata(chart).subdata(start_index=0, end_index=n_candle)

    def last_n_candle(self, chart: CsvChart | Chart, n_candle: int = 150) -> ChartData:
        return self._find_chartdata(chart).subdata(start_index=-n_candle)

    def last_timestamp(self, chart: CsvChart | Chart):
        return self.last_n_candle(chart, 2)[-1].timestamp

    def prepare_chart(self, chart: Chart) -> bool:
        """
        Takes precision, pip_factor and contract_size from the real exchange.
        A copy is prepared, so a broker suffix the real agent puts on the
        symbol (XAUUSD -> XAUUSD!) does not change the csv chart's key.
        """
        spec = Chart(chart.symbol, chart.timeframe, chart.chart_type)
        if not self.real_agent.prepare_chart(spec):
            return False
        chart.precision = spec.precision
        chart.pip_factor = spec.pip_factor
        chart.contract_size = spec.contract_size
        return True

    def get_chartdata(self, chart: Chart, n_bars: int = 100) -> ChartData | None:
        timestamp = TimeHandler.now()
        chartdata = self._find_chartdata(chart)
        # past the csv's last candle (a higher timeframe ends first) keep its last bars
        idx = max(int(np.searchsorted(chartdata.timestamps, timestamp)), n_bars)
        return chartdata.subdata(idx - n_bars, idx)

    def get_current_tick(self, chart: Chart, side: PositionSide | None = None) -> float:
        """The open of the running candle, without spread."""
        return self._running_candle(chart)[1]

    def open_position(self, position: Position) -> float | None:
        """
        Fills at the open of the running candle, so the position is checked
        against that whole candle, not only the ones after it.
        """
        timestamp, price = self._running_candle(position.chart)
        position.last_check_timestamp = timestamp
        return price

    def get_open_positions(self, *args, **kwargs) -> Any:
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

    def check_position_closed(self, position: Position, *args, **kwargs):
        pass


class BacktestReportCollector(ReportMsgFormater):
    signals = []
    open_positions = []
    closed_positions = []
    pnl_reports = []

    def new_position(self, position: Position) -> str:
        logger.info("New Position")
        self.open_positions.append(position)
        return "OK"

    def position_closed(self, position: Position, pnl_report: PnLReport) -> str:
        if position not in self.open_positions:
            # tps hit in the same check each report the last one as triggered
            return "OK"
        logger.info("Position Closed")
        self.open_positions.remove(position)
        self.closed_positions.append(position)
        self.pnl_reports.append(pnl_report)
        return "OK"

    def sl_trailed(self, position: Position) -> str:
        logger.info("SL Trailed")
        return "OK"

    def trigger_hit(self, position: Position, pnl_report: PnLReport) -> str:
        logger.info("Trigger Hit")
        if position.steps[-1].triggered_timestamp:
            return self.position_closed(position, pnl_report)
        self.pnl_reports.append(pnl_report)
        return "OK"

    def new_signal(self, signal: Signal) -> str:
        logger.info("New Signal")
        self.signals.append(signal)
        return "OK"


class BacktestReporter(ReporterBot):
    def __init__(self):
        self.name = "Backtest Reporter"
        self.enable = True
        self.msg_formater = BacktestReportCollector()
        self.save_path = "BackTest/Records/"

    @property
    def all_signals(self):
        return self.msg_formater.signals

    async def send_msg(self, *args, **kwargs):
        return 1
