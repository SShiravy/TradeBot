from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
import json
import hashlib
from DivergenceStrategy.divergence import DivergenceTradeConfig
from DivergenceStrategy.divergence import DivergenceSignal


def make_hash(payload: dict):
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))

    return hashlib.sha256(raw.encode()).hexdigest()


class DiverSignals(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    signal_timestamp: int

    baseline_start_timestamp: int
    baseline_end_timestamp: int
    secondline_start_timestamp: int
    secondline_end_timestamp: int

    side: str
    source: int = Field(foreign_key="backtestrun.id", index=True)

    @classmethod
    def give_datapoint(cls, diver_signal: DivergenceSignal, source_id: int):
        datapoint = DiverSignals(
            signal_timestamp=diver_signal.candle.signal_timestamp,
            baseline_start_timestamp=diver_signal.base_line.start_candle.timestamp,
            baseline_end_timestamp=diver_signal.base_line.end_candle.timestamp,
            secondline_start_timestamp=diver_signal.second_line.start_candle.timestamp,
            secondline_end_timestamp=diver_signal.second_line.end_candle.timestamp,
            side=diver_signal.side.value,
            source=source_id,
        )

        return datapoint


class DiverBacktests(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    symbol: str
    second_symbol: Optional[str] = None
    timeframe: str

    first_candle_timestamp: int
    last_candle_timestamp: int

    merged_two_chart_time: bool

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    config_hash: str = Field(index=True, unique=True)
    config_json: str

    @classmethod
    def give_datapoint(cls, trade_config: DivergenceTradeConfig):
        conf_dict = trade_config.export_config()
        conf_dict.update(trade_config.strategy.export_config())
        first_candle_timestamp = trade_config.get_chartdata()[0][0].timestamp
        last_candle_timestamp = trade_config.get_chartdata()[0][-1].timestamp

        datapoint = DiverBacktests(
            config_json=json.dumps(conf_dict),
            config_hash=make_hash(conf_dict),
            symbol=trade_config.chart.symbol,
            second_symbol=trade_config.second_chart.symbol,
            timeframe=trade_config.chart.timeframe.value,
            merged_two_chart_time=trade_config.merge_two_chart_time,
            first_candle_timestamp=first_candle_timestamp,
            last_candle_timestamp=last_candle_timestamp,
        )

        return datapoint
