from TradingModule import Position, ExchangeAgent
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from enum import Enum
import logging

logger = logging.getLogger("TradeCommand")


class TradeCommandStatus(Enum):
    PENDING = "Pending"
    EXECUTED = "Executed"
    FAILED = "Failed"


class TradeCommand(ABC):
    all_pending_commands = []
    __recorded_executed_commands = {}
    __recorded_failed_commands = {}

    def __init__(
        self, position: Position, exchange: ExchangeAgent, n_attempts: int = 2
    ):
        self.position = position
        self.n_attempts = n_attempts
        self.failed_attempt: int = 0
        self.__status = TradeCommandStatus.PENDING
        TradeCommand.all_pending_commands.append(self)
        self.exchange = exchange

        logger.debug(self)

    def __str__(self) -> str:
        return f"{self.__class__.__name__} {self.status.value} on {self.position.chart}"

    def __record(self, command, record: dict):
        n = record.get(command.__class__.__name__, 0)
        record[command.__class__.__name__] = n + 1

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, value: TradeCommandStatus):
        if value is TradeCommandStatus.EXECUTED:
            TradeCommand.all_pending_commands.remove(self)
            self.__record(self, TradeCommand.__recorded_executed_commands)
        elif value is TradeCommandStatus.FAILED:
            TradeCommand.all_pending_commands.remove(self)
            self.__record(self, TradeCommand.__recorded_failed_commands)
        self.__status = value

    @abstractmethod
    def command(self, time: datetime) -> bool:
        """
        Execute Command using proper methods in ExchangeAPI
        change position obj if its neccessary
        """
        pass

    def execute(self, time: datetime | None = None) -> bool:
        """
        Execute Command and handle status
        """
        if time is None:
            time = datetime.now(timezone.utc)
        if self.status is TradeCommandStatus.EXECUTED:
            logger.warning(
                f"attempt to execute already Executed {self.__class__.__name__} Command!"
            )
        if self.status is TradeCommandStatus.FAILED:
            logger.warning(
                f"attempt to execute already Failed {self.__class__.__name__} Command!"
            )

        if self.command(time):
            self.status = TradeCommandStatus.EXECUTED
            logger.info(str(self) + f" for {self.position.id}")
            return True

        else:
            self.failed_attempt += 1
            if self.failed_attempt > self.n_attempts:
                self.status = TradeCommandStatus.FAILED
            logger.error(f"{self} with {self.failed_attempt} failed attempts")
            return False

    @classmethod
    def execute_pending_commands(cls, time: datetime | None = None):
        if time is None:
            time = datetime.now(timezone.utc)
        for command in TradeCommand.all_pending_commands:
            command.execute(time)

    @classmethod
    def close_records(cls):
        msg = [
            "Trade Commands' Record:",
            f"Executed: {cls.__recorded_executed_commands}",
            f"Failed: {cls.__recorded_failed_commands}",
            f"Pending: {len(cls.all_pending_commands)}",
        ]

        msg = "\n".join(msg)
        cls.__recorded_failed_commands = {}
        cls.__recorded_executed_commands = {}
        return msg


# All Trade Commands Here ------------------


class OpenPosition(TradeCommand):
    def command(self, time):
        entry_price = self.exchange.open_position(self.position)
        if entry_price:
            self.position.entry_price = entry_price
            self.position.open_time = time
            return True
        return False


class TrailStoploss(TradeCommand):
    def __init__(
        self,
        position: Position,
        exchange: ExchangeAgent,
        stoploss_price: float,
        n_attempts: int = 2,
    ):
        super().__init__(position, exchange, n_attempts)
        self.stoploss_price = stoploss_price

    def command(self, time):
        if self.exchange.change_stoploss(self.position, self.stoploss_price):
            self.position.stoploss = self.stoploss_price
            self.position.last_update = time
            return True
        return False


class ChangeTakeProfit(TradeCommand):
    def __init__(
        self,
        position: Position,
        exchange: ExchangeAgent,
        takeprofit_price: float,
        n_attempts: int = 2,
    ):
        super().__init__(position, exchange, n_attempts)
        self.takeprofit_price = takeprofit_price

    def command(self, time) -> bool:
        if self.exchange.change_takeprofit(self.position, self.takeprofit_price):
            self.position.takeprofit = self.takeprofit_price
            self.position.last_update = time
            return True
        return False


class ParitalTakeProfit(TradeCommand):
    def __init__(
        self,
        position: Position,
        exchange: ExchangeAgent,
        volume: float,
        n_attempts: int = 2,
    ):
        super().__init__(position, exchange, n_attempts)
        self.volume = volume

    def command(self, time) -> bool:
        exec_price = self.exchange.partial_close(self.position, volume=self.volume)
        if exec_price:
            self.position.update_pnl(exec_price, self.volume)
            self.position.last_update = time
            return True
        return False


class ClosePosition(TradeCommand):
    def command(self, time):
        exec_price = self.exchange.close_position(self.position)
        if exec_price:
            self.position.update_pnl(exec_price)
            self.position.closed = time
            return True
        return False


class StopLoss(TradeCommand):
    def command(self, time) -> bool:
        self.position.closed = time
        self.position.update_pnl(self.position.stoploss)
        return True


class TakeProfit(TradeCommand):
    def command(self, time) -> bool:
        self.position.closed = time
        self.position.update_pnl(self.position.takeprofit)
        return True
