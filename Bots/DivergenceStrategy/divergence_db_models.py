from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
import json
from Bots.DivergenceStrategy.old_oscillator_divergence import (
    OscillatorDiverConfig,
    OscillatorDiverSignal,
)
from Bots.DivergenceStrategy.oscillator_double_divergence import (
    OscillatorDoubleDiverConfig,
    OscillatorDoubleDiverSignal,
)
from LocalBackTester.Database.hashing import generate_hash, give_config_dict
from Bots.DivergenceStrategy import TwoChartDiverTradeConfig
from Bots.DivergenceStrategy import DivergenceSignal


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
    def generate_datapoint(cls, trade_config: TwoChartDiverTradeConfig):
        start_candle_timestamp = trade_config.get_chartdata()[0][0].timestamp
        end_candle_timestamp = trade_config.get_chartdata()[0][-1].timestamp
        conf_dict = give_config_dict(trade_config)

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


# Oscillator Diver -----------------------


class OscillatorDiverSignalRow(SQLModel, table=True):
    __tablename__ = "Oscillator_Divergence_Signals"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)

    signal_timestamp: int

    main_line_start_timestamp: int
    main_line_end_timestamp: int
    other_chart_line_start_price: float
    other_chart_line_end_price: float

    side: str
    source: int = Field(foreign_key="Oscillator_Divergence_Backtests.id", index=True)

    @classmethod
    def generate_datapoint(cls, diver_signal: OscillatorDiverSignal, source_id: int):
        datapoint = OscillatorDiverSignalRow(
            signal_timestamp=diver_signal.candle.timestamp,
            main_line_start_timestamp=diver_signal.main_chart_line.start_candle.timestamp,
            main_line_end_timestamp=diver_signal.main_chart_line.end_candle.timestamp,
            other_chart_line_start_price=diver_signal.other_chart_line_prices[0],
            other_chart_line_end_price=diver_signal.other_chart_line_prices[1],
            side=diver_signal.side.value,
            source=source_id,
        )
        return datapoint


class OscillatorDiverBacktestRow(SQLModel, table=True):
    __tablename__ = "Oscillator_Divergence_Backtests"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)

    symbol: str
    timeframe: str

    start_candle_timestamp: int
    end_candle_timestamp: int

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    config_hash: str = Field(index=True, unique=True)
    config_json: str

    @classmethod
    def generate_datapoint(
        cls, trade_config: OscillatorDiverConfig | OscillatorDoubleDiverConfig
    ):
        start_candle_timestamp = trade_config.get_chartdata()[0][0].timestamp
        end_candle_timestamp = trade_config.get_chartdata()[0][-1].timestamp
        conf_dict = give_config_dict(trade_config)

        datapoint = OscillatorDiverBacktestRow(
            config_json=json.dumps(conf_dict),
            config_hash=generate_hash(conf_dict),
            symbol=trade_config.chart.symbol,
            timeframe=trade_config.chart.timeframe.value,
            start_candle_timestamp=start_candle_timestamp,
            end_candle_timestamp=end_candle_timestamp,
        )

        return datapoint


# Oscillator Double Diver -----------------------


class OscillatorDoubleDiverSignalRow(SQLModel, table=True):
    __tablename__ = "Oscillator_Double_Divergence_Signals"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)

    signal_timestamp: int

    main_line_start_timestamp: int
    main_line_end_timestamp: int
    main_second_line_start_timestamp: int
    main_second_line_end_timestamp: int
    other_chart_line_start_price: float
    other_chart_line_end_price: float
    other_chart_second_line_start_price: float
    other_chart_second_line_end_price: float

    side: str
    source: int = Field(foreign_key="Oscillator_Divergence_Backtests.id", index=True)

    @classmethod
    def generate_datapoint(
        cls, diver_signal: OscillatorDoubleDiverSignal, source_id: int
    ):
        datapoint = OscillatorDoubleDiverSignalRow(
            signal_timestamp=diver_signal.candle.timestamp,
            main_line_start_timestamp=diver_signal.main_chart_line.start_candle.timestamp,
            main_line_end_timestamp=diver_signal.main_chart_line.end_candle.timestamp,
            main_second_line_end_timestamp=diver_signal.main_chart_second_line.start_candle.timestamp,
            main_second_line_start_timestamp=diver_signal.main_chart_second_line.end_candle.timestamp,
            other_chart_line_start_price=diver_signal.other_chart_line_prices[0],
            other_chart_line_end_price=diver_signal.other_chart_line_prices[1],
            other_chart_second_line_start_price=diver_signal.other_chart_second_line_prices[
                0
            ],
            other_chart_second_line_end_price=diver_signal.other_chart_second_line_prices[
                1
            ],
            side=diver_signal.side.value,
            source=source_id,
        )
        return datapoint
