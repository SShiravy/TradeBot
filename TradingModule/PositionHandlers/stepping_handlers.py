from datetime import timedelta
from ChartModule.models import MarketSide, Signal
from ChartModule.plot import Plot
from TradingModule.PositionHandlers.simple_handlers import SimpleForex
from TradingModule.models import ExchangeAgent, OrderSide, Position, Trigger
from TradingModule.commands import TradeCommand
from TradingModule import commands
import numpy as np
import logging


logger = logging.getLogger("PositionHandler")


class SteppingForex(SimpleForex):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        initial_volume: float = 0.03,
        stoploss_pip: int = 20,
        targets_pip: list[int] = [50, 100, 200],
        targets_volumes_lot: float | list[float] = [0.01, 0.01, 0.01],
        trail_stop: bool = True,
        long_trade=True,
        short_trade=True,
    ) -> None:
        if isinstance(targets_volumes_lot, float | int):
            # make it list with same size as targets_pip if it's not
            targets_volumes_lot = [float(targets_volumes_lot)] * len(targets_pip)

        if sum(targets_volumes_lot) > initial_volume:
            raise ValueError(
                f"sum of {targets_volumes_lot} param must be 1 {sum(targets_volumes_lot)}"
            )

        if len(targets_pip) != len(targets_volumes_lot):
            raise ValueError(
                f"targets_volumes_lot param must be \
                             float or list[float] with same size as targets_pip\
                             {len(targets_volumes_lot)} != {len(targets_pip)}"
            )

        super().__init__(
            exchange_agent,
            initial_volume,
            stoploss_pip,
            targets_pip[-1],
            long_trade=long_trade,
            short_trade=short_trade,
        )

        self.targets_pip = [tp/10 for tp in targets_pip]
        self.targets_volumes_lot = targets_volumes_lot
        self.trail_stop = trail_stop

    def set_steps(self, pos: Position):
        steps = []
        for target, volume in zip(self.targets_pip, self.targets_volumes_lot):
            steps.append(
                Trigger(
                    price=round(pos.entry_price + target * pos.side.factor(),
                                pos.chart.precision),
                    volume=volume,
                )
            )
        logger.debug(f"steps for position set to: {steps}")
        pos.steps = steps

    async def open_steps_position(self, pos: Position):
        for step in pos.steps:
            step_position = Position(
                pos.chart,
                pos.side,
                pos.entry_price,
                step.volume,
                stoploss=pos.stoploss,
                takeprofit=step.price,
                leverage=pos.leverage,
                source=f"{pos.source}|TakeProfit",
                real_trade=True,
            )
            await commands.OpenPosition(step_position, self.exchange_agent).execute()

    async def generate_position(
        self,
        signal: Signal,
        entry_price: float | None = None,
        plot: Plot | None = None,
        *args,
        **kwargs,
    ) -> Position:
        real_trade = False
        if signal.side is MarketSide.BEARISH:
            side = OrderSide.SELL
            if self.short_trade:
                real_trade = True
        else:  # signal.side is MarketSide.BULLISH:
            side = OrderSide.BUY
            if self.long_trade:
                real_trade = True
        if entry_price is None:
            entry_price = signal.candle.close

        precision = signal.chart.precision

        position = Position(
            signal.chart,
            side,
            entry_price,
            self.initial_volume,
            round(self.init_stoploss(entry_price, side), precision),
            round(entry_price + self.targets_pip[-1] * side.factor(), precision),
            self.leverage,
            signal.candle.time + timedelta(seconds=2),
            signal.source,
            real_trade=False,
            plot=plot,
        )
        self.open_positions.append(position)
        logger.info(f"New Position on {position.chart}")
        logger.debug(f"The New Position {position}")
        position.in_forex = True
        
        self.set_steps(position)
        if real_trade:
            await self.open_steps_position(position)
        return position


    def handler(
        self, position: Position, tick_prices: list[float]
    ) -> TradeCommand | None:
        if not position.confiremed:
            self.modify_init_sl_tp(position)
        # TODO: what about modifing steps?
        if position.confiremed and not position.sended:
            commands.SendPositionSignal(position, self.exchange_agent)

        step = position.next_step
        if step is None:
            logger.warning(f"checking position that its next step is None! {position=}")
            step = position.current_step
        
        direction = position.side.factor()
        ticks = np.array(tick_prices) * direction
        sl = position.stoploss * direction
        tp = step.price * direction
        cross = np.logical_or(ticks <= sl, ticks >= tp)
        if not cross.any():
            return None
        idx = np.argmax(cross)
        if ticks[idx] <= sl:
            return commands.StopLoss(position, self.exchange_agent)

        logger.info(f"Step hit for position {position.id} on {position.chart} with price {step.price} and volume {step.volume}")
        trigger_command = commands.TriggerStep(position=position, exchange=self.exchange_agent, trigger=step)
        if self.trail_stop:
            trailstop = commands.TrailStoplossbyStep(position=position,exchange=self.exchange_agent)
            trailstop.bounded_command = trigger_command
        return trigger_command