from TradingModule import Position, ExchangeAPI
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
    all_executed_commands = []
    all_failed_commands = []

    def __init__(self, position: Position, n_attempts: int = 2):
        self.position = position
        self.n_attempts = n_attempts
        self.failed_attempt: int = 0
        self.status = TradeCommandStatus.PENDING
        self.all_pending_commands.append(self)

        logger.debug(self)

    def __str__(self) -> str:
        return f"{__class__.__name__} {self.status.value} on {self.position.chart}"

    @abstractmethod
    def command(self, exchange: ExchangeAPI) -> bool:
        """
        Execute Command using proper methods in ExchangeAPI
        change position obj if its neccessary
        """
        pass

    def execute(self, exchange: ExchangeAPI) -> bool:
        """
        Execute Command and handle status
        """
        if self.status is TradeCommandStatus.EXECUTED:
            logger.warning(
                f"attempt to execute already Executed {self.__class__.__name__} Command!"
            )
        if self.status is TradeCommandStatus.FAILED:
            logger.warning(
                f"attempt to execute already Failed {self.__class__.__name__} Command!"
            )

        if self.command(exchange):
            self.status = TradeCommandStatus.EXECUTED
            self.all_pending_commands.remove(self)
            self.all_executed_commands.append(self)
            logger.debug(f"{self}")
            return True

        else:
            self.failed_attempt += 1
            if self.failed_attempt > self.n_attempts:
                self.status = TradeCommandStatus.FAILED
                self.all_pending_commands.remove(self)
                self.all_failed_commands.append(self)
            logger.error(f"{self} with {self.failed_attempt} failed attempts")
            return False

    @classmethod
    def execute_pending_commands(cls, exchange: ExchangeAPI):
        for command in cls.all_pending_commands:
            command.execute(exchange)

    @classmethod
    def close_records(cls):
        msg = f"Trade Commands' Record:\n\
                {len(cls.all_executed_commands)} Executed\n\
                {len(cls.all_failed_commands)} Failed\n\
                {len(cls.all_pending_commands)} still Pending"

        cls.all_executed_commands = []
        cls.all_failed_commands = []
        logger.debug(msg)
        return msg


# All Trade Commands Here ------------------


class OpenPosition(TradeCommand):
    def command(self, exchange: ExchangeAPI):
        pos_id = exchange.open_position(self.position)
        if pos_id:
            self.position.id = pos_id
            self.position.open_time = datetime.now(tz=timezone.utc)
            return True
        return False


class TrailStoploss(TradeCommand):
    def __init__(self, position: Position, stoploss_price: float, n_attempts: int = 2):
        super().__init__(position, n_attempts)
        self.stoploss_price = stoploss_price

    def command(self, exchange: ExchangeAPI):
        if exchange.change_stoploss(self.position, self.stoploss_price):
            self.position.stoploss = self.stoploss_price
            return True
        return False


class ChangeTakeProfit(TradeCommand):
    def __init__(
        self, position: Position, takeprofit_price: float, n_attempts: int = 2
    ):
        super().__init__(position, n_attempts)
        self.takeprofit_price = takeprofit_price

    def command(self, exchange: ExchangeAPI) -> bool:
        if exchange.change_takeprofit(self.position, self.takeprofit_price):
            self.position.takeprofit = self.takeprofit_price
            return True
        return False


class ParitalTakeProfit(TradeCommand):
    def __init__(self, position: Position, volume: float, n_attempts: int = 2):
        super().__init__(position, n_attempts)
        self.volume = volume

    def command(self, exchange: ExchangeAPI) -> bool:
        exec_price = exchange.partial_close(self.position, volume=self.volume)
        if exec_price:
            self.position.update_pnl(exec_price, self.volume)
            return True
        return False


class ClosePosition(TradeCommand):
    def command(self, exchange: ExchangeAPI):
        exec_price = exchange.close_position(self.position)
        if exec_price:
            self.position.update_pnl(exec_price)
            self.position.closed = datetime.now(tz=timezone.utc)
            return True
        return False


class StopLoss(TradeCommand):
    def __init__(self, position: Position, n_attempts: int = 2):
        super().__init__(position, n_attempts)

    def command(self, exchange: ExchangeAPI) -> bool:
        self.position.closed = datetime.now(tz=timezone.utc)
        self.position.update_pnl(self.position.stoploss)
        return True


class TakeProfit(TradeCommand):
    def __init__(self, position: Position, n_attempts: int = 2):
        super().__init__(position, n_attempts)

    def command(self, exchange: ExchangeAPI) -> bool:
        self.position.closed = datetime.now(tz=timezone.utc)
        self.position.update_pnl(self.position.takeprofit)
        return True
