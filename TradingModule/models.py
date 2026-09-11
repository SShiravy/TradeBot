import numpy as np
from ChartModule.models import (
    Chart,
    ChartData,
    MarketSide,
    Candle,
    Signal,
)
from ChartModule.timing import TimeHandler
from ChartModule.Indicators import IndicatorBaseModel, SupportCandleConditions
from dataclasses import asdict, dataclass, field
from datetime import datetime
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


class Command(ABC):
    pending_commands = []
    __executed_record = {}
    __failed_record = {}

    def __init__(
        self,
        n_attempts: int = 2,
    ):
        self.n_attempts = n_attempts
        self.failed_attempt: int = 0
        self.__status = CommandStatus.DEFINED
        self.next_command: Command | None = None
        self.define_timestamp: int = TimeHandler.now()
        self.send_timestamp: Optional[int] = None
        self.result_timestamp: Optional[int] = None
        command_logger.debug(self)
        # TODO: add times to str 
    
    @property
    def name(self):
        return self.__class__.__name__

    def __str__(self) -> str:
        return f"{self.name} {self.status.value}"

    def __record(self, command, record: dict):
        n = record.get(command.name, 0)
        record[command.name] = n + 1

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, value: CommandStatus):
        if value is CommandStatus.PENDING:
            Command.pending_commands.append(self)
        elif value is CommandStatus.EXECUTED:
            Command.pending_commands.remove(self)
            self.__record(self, Command.__executed_record)
        elif value is CommandStatus.FAILED:
            Command.pending_commands.remove(self)
            self.__record(self, Command.__failed_record)
        self.__status = value

    def send(self):
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
                    self.next_command.send()
                    command_logger.debug(f"next command {self.next_command.name} sended")
                else:
                    command_logger.warning(f"bounded command status: {self.next_command.status}")
            return True

        else:
            self.failed_attempt += 1
            if self.failed_attempt > self.n_attempts:
                self.status = CommandStatus.FAILED
            command_logger.error(f"{self.name} with {self.failed_attempt} failed attempts")
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
    cross_direction: Literal[1,-1] = 1
    command: Command | None = field(default=None)
    type: TriggerType = field(default=TriggerType.OTHER)
    defined_timestamp: int = TimeHandler.now()
    triggered_timestamp: int | None = field(default=None)
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
        if self.command:
            self.command.send()
            return self.command

    def check(self,ticks:np.ndarray)->bool:
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
                raise TypeError(f"Can not convert market side {market_side} to position side")

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
    entry_volume: float
    triggers: list[Trigger]
    stoploss: Trigger
    leverage: int = 1
    type:PositionType = field(default=PositionType.MARKET)
    source: str = field(default="Unknown")

    defined_timestamp: int = field(default_factory=lambda: TimeHandler.now(), init=False)
    last_check_timestamp: int | None = field(default=None, init=False)
    open_timestamp: int | None = field(default=None, init=False)
    closed_timestamp: int | None = field(default=None, init=False)

    initial_stoploss: Trigger = field(init=False)
    exchange_id: str = field(default="", init=False)

    _steps_cache: list[Trigger] | None = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self):
        self.initial_stoploss = self.stoploss

    @property
    def steps(self):
        if self._steps_cache is None:
            self._steps_cache = sorted(
                self.triggers, key=lambda t: t.price, reverse=self.side == PositionSide.SHORT
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
    def get_current_tick(self,chart:Chart)->float:
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


class Strategy(ABC):
    def __init__(
        self,
        name: str,
        long_support_conditions: SupportCandleConditions,
        short_support_conditions: SupportCandleConditions,
        confirmation_indicators: list[IndicatorBaseModel] = [],
    ) -> None:
        self.name = name
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

    @abstractmethod
    def draw(self, plot, signal, draw_indicators: bool = True, *args, **kwargs):
        if draw_indicators and self.confirmation_indicators:
            for indicator in self.confirmation_indicators:
                indicator.plot(plot)

    def export_config(self):
        indicators_configs = []
        for indicator in self.confirmation_indicators:
            indicators_configs.append(indicator.export_configs())
        return {
            "long_support_conditions": self.long_support_conditions.value,
            "short_support_conditions": self.short_support_conditions.value,
            "indicators": indicators_configs,
        }
