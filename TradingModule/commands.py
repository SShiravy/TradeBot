from TradingModule import Position, ExchangeAgent
from TradingModule.models import Trigger
from TradingModule.reporter import TelegramReporter
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from enum import Enum
from copy import copy
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
        self,
        position: Position,
        exchange: ExchangeAgent,
        n_attempts: int = 2,
        report=True,
    ):
        self.position = position
        self.exchange = exchange
        self.n_attempts = n_attempts
        self.failed_attempt: int = 0
        self.__status = TradeCommandStatus.PENDING
        self.report = report
        self.bounded_command: TradeCommand | None = None
        TradeCommand.all_pending_commands.append(self)

        logger.debug(self)

    def __str__(self) -> str:
        return f"{self.__class__.__name__} {self.status.value} on {self.position.chart}| report:{self.report}"

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

    async def execution_report(self):
        """
        report after successfull execution
        """
        pass

    async def execute(self, time: datetime | None = None) -> bool:
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

        if (
            self.bounded_command
            and self.bounded_command.status != TradeCommandStatus.EXECUTED
        ):
            return False

        if self.command(time):
            self.status = TradeCommandStatus.EXECUTED
            logger.info(
                str(self)
                + f" for {self.position.exchange_id if self.position.exchange_id else self.position.id}"
            )
            if self.report:
                await self.execution_report()
            return True

        else:
            self.failed_attempt += 1
            if self.failed_attempt > self.n_attempts:
                self.status = TradeCommandStatus.FAILED
                if self.report:
                    await TelegramReporter().log_report(
                        f"{self} with {self.failed_attempt} failed attempts"
                    )
            logger.error(f"{self} with {self.failed_attempt} failed attempts")
            return False

    @classmethod
    async def execute_pending_commands(cls, time: datetime | None = None, report=True):
        if time is None:
            time = datetime.now(timezone.utc)
        all_commands = copy(TradeCommand.all_pending_commands)
        for command in all_commands:
            command.report = report
            await command.execute(time)

    @classmethod
    def close_records(cls):
        msg = [
            "Trade Commands Summary:",
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
        if self.position.real_trade:
            entry_price = self.exchange.open_position(self.position)
            if entry_price:
                self.position.entry_price = entry_price
                self.position.open_time = time
            else:
                return False
        return True


class SendPositionSignal(TradeCommand):
    async def execution_report(self):
        await TelegramReporter().new_position(self.position)
        self.position.plot = None

    def command(self, time):
        self.position.sended = True
        self.position.last_update = time
        return True


class TrailStoploss(TradeCommand):
    def __init__(
        self,
        position: Position,
        exchange: ExchangeAgent,
        stoploss_price: float,
        n_attempts: int = 2,
        report=True,
    ):
        super().__init__(position, exchange, n_attempts, report)
        self.stoploss_price = stoploss_price

    async def execution_report(self):
        await TelegramReporter().trailing_sl(self.position)

    def command(self, time):
        if self.position.real_trade and not self.exchange.change_stoploss(
            self.position, self.stoploss_price
        ):
            return False
        self.position.stoploss = self.stoploss_price
        self.position.last_update = time
        return True


class ChangeTakeProfit(TradeCommand):
    def __init__(
        self,
        position: Position,
        exchange: ExchangeAgent,
        takeprofit_price: float,
        n_attempts: int = 2,
        report=True,
    ):
        super().__init__(position, exchange, n_attempts, report)
        self.takeprofit_price = takeprofit_price

    def command(self, time) -> bool:
        if self.position.real_trade and not self.exchange.change_takeprofit(
            self.position, self.takeprofit_price
        ):
            return False
        self.position.takeprofit = self.takeprofit_price
        self.position.last_update = time
        return True


class ParitalClose(TradeCommand):
    def __init__(
        self,
        position: Position,
        exchange: ExchangeAgent,
        volume: float,
        n_attempts: int = 2,
        exec_price=None,
        report=True,
    ):
        super().__init__(position, exchange, n_attempts, report)
        self.volume = volume
        self.exec_price = exec_price

    def command(self, time) -> bool:
        if self.position.real_trade:
            exec_price = self.exchange.partial_close(self.position, volume=self.volume)
            if exec_price:
                self.position.update_pnl(exec_price, self.volume)
            else:
                return False
        elif self.exec_price:
            self.position.update_pnl(self.exec_price, self.volume)
        self.position.last_update = time
        return True


class ClosePosition(TradeCommand):
    def __init__(
        self,
        position: Position,
        exchange: ExchangeAgent,
        n_attempts: int = 2,
        exec_price=None,
        report=True,
    ):
        super().__init__(position, exchange, n_attempts, report)
        self.exec_price = exec_price

    async def execution_report(self):
        await TelegramReporter().position_closed(self.position)

    def command(self, time):
        if self.position.real_trade:
            exec_price = self.exchange.close_position(self.position)
            if exec_price:
                self.position.update_pnl(exec_price)
            else:
                return False
        elif self.exec_price:
            self.position.update_pnl(self.exec_price)
        self.position.closed = time
        return True


class StopLoss(TradeCommand):
    async def execution_report(self):
        await TelegramReporter().position_closed(self.position)

    def command(self, time) -> bool:
        self.position.closed = time
        self.position.update_pnl(self.position.stoploss)
        return True


class TakeProfit(TradeCommand):
    async def execution_report(self):
        await TelegramReporter().position_closed(self.position)

    def command(self, time) -> bool:
        self.position.closed = time
        self.position.update_pnl(self.position.takeprofit)
        return True


class TriggerStep(TradeCommand):
    def __init__(
        self,
        position: Position,
        exchange: ExchangeAgent,
        trigger: Trigger,
        n_attempts: int = 2,
        exec_price=None,
        report=True,
    ):
        super().__init__(position, exchange, n_attempts, report)
        self.exec_price = exec_price
        self.trigger = trigger

    def command(self, time) -> bool:
        self.position.update_pnl(self.trigger.price, self.trigger.volume)
        self.position.go_next_step(time)
        return True

    async def execution_report(self):
        # TODO: complete here
        pass


class TrailStoplossbyStep(TradeCommand):
    def __init__(
        self,
        position: Position,
        exchange: ExchangeAgent,
        n_attempts: int = 2,
        report=True,
    ):
        super().__init__(position, exchange, n_attempts, report)

    async def execution_report(self):
        await TelegramReporter().trailing_sl(self.position)

    def command(self, time):
        new_sl = self.position.previous_step
        if new_sl.price == self.position.stoploss:
            logger.warning(
                "trying to set new stoploss same as previous one, in TrailStopLosssbyStep"
            )
            return True
        if self.position.real_trade and not self.exchange.change_stoploss(
            self.position, new_sl.price
        ):
            return False
        self.position.stoploss = new_sl.price
        self.position.last_update = time
        return True
