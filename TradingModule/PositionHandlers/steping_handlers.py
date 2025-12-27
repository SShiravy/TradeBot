from ChartModule.models import Signal
from TradingModule.PositionHandlers.simple_handlers import SimpleCrypto, SimpleForex
from TradingModule.models import ExchangeAgent, Position, Trigger
from TradingModule.commands import TradeCommand
from TradingModule import commands
import numpy as np


class RiskFreeCrypto(SimpleCrypto):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        initial_volume: float = 0.05,
        leverage: int = 1,
        stoploss_percent: float = 5,
        targets_percents: list[float] = [1, 2, 3, 4],
        targets_volumes_percents: float | list[float] = [0.25, 0.5, 0.25, 0.25],
        trail_stop: bool = True,
        long_trade=True,
        short_trade=True,
    ) -> None:
        super().__init__(
            exchange_agent,
            initial_volume,
            leverage,
            stoploss_percent,
            targets_percents[0],
            long_trade=long_trade,
            short_trade=short_trade,
        )
        if isinstance(targets_volumes_percents, list) and len(
            targets_volumes_percents
        ) != len(targets_percents):
            raise ValueError(
                f"targets_volumes_percents param must be \
                             float or list[float] with same size as targets_percents\
                             {len(targets_volumes_percents)} != {len(targets_percents)}"
            )

        if isinstance(targets_volumes_percents, float | int):
            targets_volumes_percents = [float(targets_volumes_percents)] * len(
                targets_percents
            )

        if sum(targets_volumes_percents) > 1:
            raise ValueError(
                f"sum of {targets_volumes_percents} param must be 1\
                            {sum(targets_volumes_percents)}"
            )

        self.targets_percents = targets_percents
        self.targets_volumes_percents = targets_volumes_percents
        self.trail_stop = trail_stop

    def set_steps(self, pos: Position):
        steps = []
        for target, volume in zip(self.targets_percents, self.targets_volumes_percents):
            steps.append(
                Trigger(
                    price=abs(target / 100 + pos.side.factor()) * pos.entry_price,
                    volume=volume,
                )
            )
        pos.steps = steps

    def generate_position(
        self,
        signal: Signal,
        entry_price: float | None = None,
        position_id: str = "",
        *args,
        **kwargs,
    ) -> Position:
        pos = super().generate_position(
            signal, entry_price, position_id, *args, **kwargs
        )
        self.set_steps(pos)
        return pos

    def handler(
        self, position: Position, tick_prices: list[float]
    ) -> TradeCommand | None:
        direction = position.side.factor()
        ticks = np.array(tick_prices) * direction
        sl = position.stoploss * direction
        tp = position.takeprofit * direction
        cross = np.logical_or(ticks <= sl, ticks >= tp)
        if not cross.any():
            return None
        idx = np.argmax(cross)
        if ticks[idx] <= sl:
            return commands.StopLoss(position, self.exchange_agent)

        commands.ParitalClose(
            position, self.exchange_agent, position.current_step.volume
        )
        position.go_next_step()

        # if self.trail_stop: # TODO: complete here
        #     commands.TrailStoploss(position,self.exchange_agent,position.steps[position.curr])


class RiskFreeForex(SimpleForex):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        initial_volume: float = 0.01,
        stoploss_pip: int = 20,
        takeprofit_pip: int = 20,
        riskfree_trigger_pip: int = 10,
        long_trade: bool = True,
        short_trade: bool = True,
    ) -> None:
        super().__init__(
            exchange_agent,
            initial_volume,
            stoploss_pip,
            takeprofit_pip,
            long_trade,
            short_trade,
        )
        self.riskfree_trigger_pip = riskfree_trigger_pip

    def give_trigger_price(self, position: Position) -> float:
        if position.stoploss == position.entry_price:
            # when already riskfree triggered
            return position.takeprofit
        else:
            return (
                self.riskfree_trigger_pip * position.side.factor()
                + position.entry_price
            )

    def handler(
        self, position: Position, tick_prices: list[float]
    ) -> TradeCommand | None:
        direction = position.side.factor()
        res = super().handler(position, tick_prices)
        if res:
            return res
        direction = position.side.factor()

        ticks = np.array(tick_prices) * direction
        trigger = self.give_trigger_price(position) * direction

        cross = ticks >= trigger

        if cross.any():
            return commands.TrailStoploss(
                position, self.exchange_agent, position.entry_price
            )
