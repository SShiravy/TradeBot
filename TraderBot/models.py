import numpy as np
from ChartModule.models import (
    Chart,
    ChartData,
    MarketSide,
    Candle,
    Signal,
)
from Settings.timing import TimeHandler
from ChartModule.Indicators import Indicator, SupportCandleConditions
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from datetime import timezone
from typing import Any, Literal, Optional
from enum import Enum
import hashlib
import json
import uuid
import logging


command_logger = logging.getLogger("Commands")


class CommandStatus(Enum):
    DEFINED = "Defined"
    PENDING = "Pending"
    EXECUTED = "Executed"
    FAILED = "Failed"


@dataclass
class CommandContext:
    position: "Position"
    exchange_agent: "ExchangeAgent"
    reporter: "ReporterBot | None"


class Command(ABC):
    pending_commands = []
    __executed_record = {}
    __failed_record = {}
    N_ATTEMPTS = 2

    def __init__(self, bounded_command: "Command|None" = None):
        self.failed_attempt: int = 0
        self.__status = CommandStatus.DEFINED
        self.next_command = bounded_command
        self.define_timestamp: int = TimeHandler.now()
        self.send_timestamp: Optional[int] = None
        self.execution_timestamp: Optional[int] = None
        self.context: CommandContext
        command_logger.debug(self)

    @property
    def name(self):
        return self.__class__.__name__

    def __str__(self) -> str:
        return f"{self.name} {self.status.value}| define:{self.define_timestamp}, send:{self.send_timestamp}, execution:{self.execution_timestamp}  "

    def __record(self, command, record: dict):
        n = record.get(command.name, 0)
        record[command.name] = n + 1

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, value: CommandStatus):
        if self.__status == value:
            return
        if value is CommandStatus.PENDING:
            self.pending_commands.append(self)
        elif value is CommandStatus.EXECUTED:
            self.execution_timestamp = TimeHandler.now()
            self.pending_commands.remove(self)
            self.__record(self, self.__executed_record)
        elif value is CommandStatus.FAILED:
            self.pending_commands.remove(self)
            self.__record(self, self.__failed_record)
        self.__status = value

    def send(self, context: CommandContext, *args, **kwargs):
        self.context = context
        self.status = CommandStatus.PENDING

    @abstractmethod
    async def command(self) -> bool:
        pass

    async def execute(self) -> bool:
        """
        Execute Command
        """
        if self.status is CommandStatus.EXECUTED:
            command_logger.warning(
                f"attempt to execute already Executed {self.name} Command!"
            )
        if self.status is CommandStatus.FAILED:
            command_logger.warning(
                f"attempt to execute already Failed {self.name} Command!"
            )
        res = await self.command()
        if res:
            self.status = CommandStatus.EXECUTED
            if self.next_command:
                if self.next_command.status == CommandStatus.DEFINED:
                    self.next_command.send(self.context)
                    command_logger.debug(
                        f"next command {self.next_command.name} sended"
                    )
                else:
                    command_logger.warning(
                        f"bounded command status: {self.next_command.status}"
                    )
            return True

        else:
            self.failed_attempt += 1
            if self.failed_attempt > self.N_ATTEMPTS:
                self.status = CommandStatus.FAILED
            command_logger.error(
                f"{self.name} with {self.failed_attempt} failed attempts"
            )
            return False

    @classmethod
    async def execute_pending_commands(cls):
        all_commands = Command.pending_commands.copy()
        for command in all_commands:
            await command.execute()

    @classmethod
    def close_records(cls):
        msg = [
            "Trade Commands Summary:",
            f"Executed: {cls.__executed_record}",
            f"Failed: {cls.__failed_record}",
            f"Pending: {len(cls.pending_commands)}",
        ]

        msg = "\n".join(msg)
        cls.__failed_record = {}
        cls.__executed_record = {}
        return msg


class TriggerType(Enum):
    SL = "Stoploss"
    TP = "Takeprofit"
    TRAILING_STOPLOSS = "Trailing Stoploss"
    OTHER = "Other"


@dataclass(slots=True)
class Trigger:
    price: float
    volume: float = field(default=0.0)
    cross_direction: Literal[1, -1] = 1
    command: Command | None = field(default=None)
    type: TriggerType = field(default=TriggerType.OTHER)
    defined_timestamp: int = field(default_factory=TimeHandler.now, init=False)
    triggered_timestamp: int | None = field(default=None, init=False)
    exchange_id: str = field(default="", init=False)

    def __str__(self) -> str:
        return f"{asdict(self)}"

    def _check_cross(self, ticks: np.ndarray):
        res = (ticks - self.price) * self.cross_direction
        if np.any(res > 0):
            return True
        return False

    def execute(self):
        self.triggered_timestamp = TimeHandler.now()
        return self.command

    def check(self, ticks: np.ndarray) -> bool:
        if self.triggered_timestamp:
            return True
        if self._check_cross(ticks):
            self.execute()
            return True
        return False


class PositionType(Enum):
    LIMIT = "Limit"
    MARKET = "Market"


class PositionSide(Enum):
    LONG = "Long"
    SHORT = "Short"

    @classmethod
    def convert_market_side(cls, market_side: MarketSide):
        match market_side:
            case MarketSide.BEARISH:
                return cls.SHORT
            case MarketSide.BULLISH:
                return cls.LONG
            case MarketSide.NEUTRAL:
                raise TypeError(
                    f"Can not convert market side {market_side} to position side"
                )

    @property
    def factor(self):
        return 1 if self is PositionSide.LONG else -1


@dataclass(slots=True)
class Position:
    id: uuid.UUID | str = field(
        default_factory=lambda: uuid.uuid4().hex[:8], init=False
    )

    chart: Chart
    side: PositionSide
    entry_price: float
    volume: float
    triggers: list[Trigger]
    stoploss: Trigger
    leverage: int = 1
    type: PositionType = field(default=PositionType.MARKET)
    source: str = field(default="Unknown")

    defined_timestamp: int = field(
        default_factory=lambda: TimeHandler.now(), init=False
    )
    last_check_timestamp: int | None = field(default=None, init=False)
    open_timestamp: int | None = field(default=None, init=False)
    closed_timestamp: int | None = field(default=None, init=False)

    initial_stoploss: Trigger = field(init=False)
    exchange_id: str = field(default="", init=False)
    report_id: Any = field(default=None, init=False)

    _steps_cache: list[Trigger] | None = field(
        default=None, init=False, repr=False, compare=False
    )

    def __post_init__(self):
        self.initial_stoploss = self.stoploss

    @property
    def steps(self):
        if self._steps_cache is None:
            self._steps_cache = sorted(
                self.triggers,
                key=lambda t: t.price,
                reverse=self.side == PositionSide.SHORT,
            )
        return self._steps_cache

    def __str__(self):
        return f"{self.side}|{self.source}|{self.chart}|{self.open_timestamp}"

    def __hash__(self):
        raw = json.dumps(
            {
                "chart": str(self.chart),
                "side": self.side.value,
                "time": str(self.defined_timestamp),
                "source": self.source,
            },
            sort_keys=True,
        ).encode()
        return int(hashlib.sha256(raw).hexdigest(), 16)


class ExchangeAgent(ABC):
    @abstractmethod
    def prepare_chart(self, chart: Chart) -> bool:
        """
        check symbol exist or not and
        change chart.precision
        """
        pass

    @abstractmethod
    def get_chartdata(self, chart: Chart, n_bars: int = 100) -> ChartData | None:
        pass

    @abstractmethod
    def get_current_tick(self, chart: Chart) -> float:
        pass

    @abstractmethod
    def get_candles_since(self, chart: Chart, time: datetime) -> list[Candle]:
        chartdata = self.get_chartdata(chart, 3)
        if chartdata is None:
            return []
        candles = []
        for candle in chartdata:
            if datetime.fromtimestamp(candle.timestamp, tz=timezone.utc) < time:
                continue
            candles.append(candle)
        return candles

    @abstractmethod
    def open_position(self, position: Position) -> float | None:
        """
        return executed price if successful otherwise None
        it should change position_exchange_id
        """
        pass

    @abstractmethod
    def get_open_positions(self, *args, **kwargs) -> Any:
        pass

    @abstractmethod
    def change_stoploss(self, position: Position, price: float) -> bool:
        pass

    @abstractmethod
    def change_takeprofit(self, position: Position, price: float) -> bool:
        pass

    @abstractmethod
    def partial_close(self, position: Position, volume: float) -> float | None:
        """
        return executed price if successful otherwise None
        """
        pass

    @abstractmethod
    def close_position(self, position: Position) -> float | None:
        """
        return executed price if successful otherwise None
        """
        pass

    @abstractmethod
    def check_position_closed(self, *args, **kwargs) -> float | None:
        pass


class SignalPlotter:
    def __call__(self, plot, signal, indicators: list[Indicator] = [], *args, **kwargs):
        if indicators:
            for i in indicators:
                i.plot(plot)
        plot.mark_signal(signal)


class Strategy(ABC):
    def __init__(
        self,
        name: str,
        plotter: SignalPlotter,
        long_support_conditions: SupportCandleConditions,
        short_support_conditions: SupportCandleConditions,
        confirmation_indicators: list[Indicator] = [],
    ) -> None:
        self.name = name
        self.plotter = plotter
        self.confirmation_indicators = confirmation_indicators
        self.long_support_conditions = long_support_conditions
        self.short_support_conditions = short_support_conditions

    def get_indicators_confirmation(self, chartdata: ChartData) -> list[MarketSide]:
        if self.confirmation_indicators == []:
            return [MarketSide.NEUTRAL]
        all_forcasts = []
        for indicator in self.confirmation_indicators:
            indicator.set(chartdata)
            all_forcasts.append(indicator.forecast())
        return all_forcasts

    @abstractmethod
    def check_signal(
        self,
        chartdata: ChartData,
        check_long: bool = True,
        check_short: bool = True,
        *args,
        **kwargs,
    ) -> Signal | None:
        pass

    def export_config(self):
        indicators_configs = []
        for indicator in self.confirmation_indicators:
            indicators_configs.append(indicator.export_configs())
        return {
            "long_support_conditions": self.long_support_conditions.value,
            "short_support_conditions": self.short_support_conditions.value,
            "indicators": indicators_configs,
        }


@dataclass(slots=True)
class PnLReport:
    chart: Chart
    side: PositionSide
    source: str
    first_time: int
    last_time: int

    pnl_dollar: float = field(default=0.0, init=False)
    pnl_percent: float = field(default=0.0, init=False)
    pnl_pips: float = field(default=0.0, init=False)

    wins: int = field(default=0, init=False)
    flats: int = field(default=0, init=False)
    loses: int = field(default=0, init=False)

    triggered_steps: dict[int, int] = field(default_factory=dict, init=False)

    max_win_in_a_row: int = field(default=0, init=False)
    max_lose_in_a_row: int = field(default=0, init=False)

    total_positions: int = field(default=1, init=False)
    overall_report: bool = field(default=False, init=False)

    @property
    def identifier(self) -> str:
        return f"{self.source}_{self.side}_{self.chart}"

    def duration(self):
        return timedelta(seconds=self.last_time - self.first_time)

    def __add__(self, other: "PnLReport | int | float") -> "PnLReport":
        if isinstance(other, (int, float)):
            return self
        if not isinstance(other, PnLReport):
            return NotImplemented

        merged = PnLReport(
            chart=self.chart,
            side=self.side,
            source=self.source,
            first_time=min(self.first_time, other.first_time),
            last_time=max(self.last_time, other.last_time),
        )
        merged.pnl_dollar = self.pnl_dollar + other.pnl_dollar
        merged.pnl_percent = self.pnl_percent + other.pnl_percent
        merged.pnl_pips = self.pnl_pips + other.pnl_pips
        merged.wins = self.wins + other.wins
        merged.flats = self.flats + other.flats
        merged.loses = self.loses + other.loses

        merged.triggered_steps = dict(self.triggered_steps)
        for k, v in other.triggered_steps.items():
            merged.triggered_steps[k] = merged.triggered_steps.get(k, 0) + v

        merged.max_win_in_a_row = max(self.max_win_in_a_row, other.max_win_in_a_row)
        merged.max_lose_in_a_row = max(self.max_lose_in_a_row, other.max_lose_in_a_row)
        merged.total_positions = self.total_positions + other.total_positions
        merged.overall_report = (
            self.identifier != other.identifier
            or self.overall_report
            or other.overall_report
        )
        return merged

    __radd__ = __add__


class ReportMsgFormater(ABC):
    @abstractmethod
    def new_position(self, position: Position) -> str:
        pass

    @abstractmethod
    def position_closed(self, position: Position, pnl_report: PnLReport) -> str:
        pass

    @abstractmethod
    def sl_trailed(self, position: Position) -> str:
        pass

    @abstractmethod
    def trigger_hit(self, position: Position, pnl_report: PnLReport) -> str:
        pass

    @abstractmethod
    def new_signal(self, signal: Signal) -> str:
        pass


class ReporterBot(ABC):
    def __init__(
        self, name: str, signal_channel, report_channel, msg_formater: ReportMsgFormater
    ):
        self.name = name
        self.signal_channel = signal_channel
        self.report_channel = report_channel
        self.enable = True
        self.msg_formater = msg_formater

    def disable_reporting(self):
        self.enable = False
        logging.info(f"⚠️ {self.name} Reporting Disabled")

    def enable_reporting(self):
        self.enable = True
        logging.info(f"👍 {self.name} Reporting Enabled")

    @abstractmethod
    async def send_msg(
        self,
        msg,
        file_path: str | None = None,
        img_path: str | None = None,
        channel_id: Any = None,
        reply_id: None | int = None,
        *args,
        **kwargs,
    ) -> Any:
        """
        return message_id if successful otherwise None
        """
