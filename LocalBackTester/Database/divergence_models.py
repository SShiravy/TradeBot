from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
import json
from LocalBackTester.Database.hashing import generate_hash
from DivergenceStrategy.divergence import DivergenceTradeConfig
from DivergenceStrategy.divergence import DivergenceSignal


class DiverSignalRow(SQLModel, table=True):
    __tablename__ = "Divergence_Signals"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)

    signal_timestamp: int

    baseline_start_timestamp: int
    baseline_end_timestamp: int
    secondline_start_timestamp: int
    secondline_end_timestamp: int

    side: str
    source: int = Field(foreign_key="Divergence_Backtests.id", index=True)

    @classmethod
    def generate_datapoint(cls, diver_signal: DivergenceSignal, source_id: int):
        datapoint = DiverSignalRow(
            signal_timestamp=diver_signal.candle.timestamp,
            baseline_start_timestamp=diver_signal.main_chart_line.start_candle.timestamp,
            baseline_end_timestamp=diver_signal.main_chart_line.end_candle.timestamp,
            secondline_start_timestamp=diver_signal.other_chart_line.start_candle.timestamp,
            secondline_end_timestamp=diver_signal.other_chart_line.end_candle.timestamp,
            side=diver_signal.side.value,
            source=source_id,
        )

        return datapoint


class DiverBacktestRow(SQLModel, table=True):
    __tablename__ = "Divergence_Backtests"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)

    symbol: str
    second_symbol: str | None
    timeframe: str

    start_candle_timestamp: int
    end_candle_timestamp: int

    merged_two_chart_time: bool

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    config_hash: str = Field(index=True, unique=True)
    config_json: str

    @classmethod
    def give_config_dict(cls, trade_config: DivergenceTradeConfig):
        conf_dict = trade_config.export_config()
        conf_dict.update(trade_config.strategy.export_config())

        return conf_dict

    @classmethod
    def give_config_hash(cls, trade_config: DivergenceTradeConfig):
        conf_dict = cls.give_config_dict(trade_config)
        return generate_hash(conf_dict)

    @classmethod
    def generate_datapoint(cls, trade_config: DivergenceTradeConfig):
        start_candle_timestamp = trade_config.get_chartdata()[0][0].timestamp
        end_candle_timestamp = trade_config.get_chartdata()[0][-1].timestamp
        conf_dict = cls.give_config_dict(trade_config)

        datapoint = DiverBacktestRow(
            config_json=json.dumps(conf_dict),
            config_hash=generate_hash(conf_dict),
            symbol=trade_config.chart.symbol,
            second_symbol=trade_config.second_chart.symbol,
            timeframe=trade_config.chart.timeframe.value,
            merged_two_chart_time=trade_config.merge_two_chart_time,
            start_candle_timestamp=start_candle_timestamp,
            end_candle_timestamp=end_candle_timestamp,
        )

        return datapoint
