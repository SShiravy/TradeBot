import logging
from TradingModule.models import Command



logger = logging.getLogger("Commands")


class OpenPosition(Command):
    def __init__(
        self,
        position: Position,
        exchange: ExchangeAgent,
        n_attempts: int = 2,
        report=True,
        trigger: Trigger | None = None,
    ):
        super().__init__(position, exchange, n_attempts, report)
        self.trigger = trigger

    def command(self, time):
        if self.position.real_trade:
            entry_price = self.exchange.open_position(self.position)
            if entry_price:
                self.position.entry_price = entry_price
                self.position.open_time = time
                if self.trigger:
                    self.trigger.exchange_id = self.position.exchange_id
            else:
                return False
        return True


class TrailStoploss(Command):
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
        self.position.last_update_timestamp = time
        return True


class ChangeTakeProfit(Command):
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
        self.position.last_update_timestamp = time
        return True


class ParitalClose(Command):
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
        self.position.last_update_timestamp = time
        return True


class ClosePosition(Command):
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
        self.position.closed_timestamp = time
        return True


class StopLoss(Command):
    def __init__(
        self,
        position: Position,
        exchange: ExchangeAgent,
        n_attempts: int = 2,
        report=True,
        pnl: float | None = None,
    ):
        super().__init__(position, exchange, n_attempts, report)
        self.pnl = pnl

    async def execution_report(self):
        await TelegramReporter().position_closed(self.position)

    def command(self, time) -> bool:
        self.position.closed_timestamp = time
        self.position.update_pnl(self.position.stoploss, pnl=self.pnl)
        return True


class TakeProfit(Command):
    async def execution_report(self):
        await TelegramReporter().position_closed(self.position)

    def command(self, time) -> bool:
        self.position.closed_timestamp = time
        self.position.update_pnl(self.position.takeprofit)
        return True


class TrailStoplossbyStep(Command):
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
        new_sl = self.position.two_previous_step
        if new_sl is None:
            logger.warning(
                "trying to set new stoploss to two previous one which is None!"
            )
            return True
        if new_sl.price == self.position.stoploss:
            logger.warning(
                "trying to set new stoploss same as previous one, in TrailStopLosssbyStep"
            )
            return True
        new_sl_price = new_sl.price
        if self.position.previous_step.pip_trail_stop:
            new_sl_price = (
                new_sl_price
                - abs(self.position.previous_step.price - self.position.entry_price)
                * self.position.side.factor()
            )
            self.position.previous_step.price = self.position.entry_price
        if self.position.real_trade:
            if self.position.in_forex:
                tp_positions = self.exchange.get_open_positions(
                    comment_filter=self.position.id
                )
                if not tp_positions:
                    logger.warning(
                        f"no open position found for position {self.position.id} in TrailStoplossbyStep command!"
                    )
                    return False
                for tp_pos in tp_positions:
                    res = self.exchange.change_stoploss(tp_pos, new_sl_price)
                    logger.debug(
                        f"tp_pos (tp:{tp_pos.takeprofit}, sl:{tp_pos.stoploss}) | change sl res:{res}"
                    )

            else:
                return self.exchange.change_stoploss(self.position, new_sl_price)
        self.position.stoploss = new_sl_price
        self.position.last_update_timestamp = time
        logging.debug(
            f"TrailStopStep: id={self.position.id}, real={self.position.real_trade}, {self.position.stoploss}"
        )
        return True
