from datetime import timedelta
from ChartModule.models import MarketSide, Signal
from ChartModule.plot import Plot
from TradingModule.PositionHandlers.model import PositionHandler
from TradingModule.PositionHandlers.ratio_handlers import (
    SlTpRatioCrypto,
)
from TradingModule.PositionHandlers.trading_constraints import TradingConstraint
from TradingModule.models import ExchangeAgent, OrderSide, Position, Trigger
from TradingModule.commands import TradeCommand
from TradingModule import commands
import numpy as np
import logging


logger = logging.getLogger("PositionHandler")


class SteppingHandlerForex(PositionHandler):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        stoploss_pip: int = 10,
        targets_ratio: list[float] = [1, 1.5, 2],
        targets_ratio_volumes: float | list[float] = 0.01,
        targets_in_pip: list[float] = [],
        targets_in_pip_volumes: float | list[float] = [],
        trail_stop: bool = True,
        long_trade=True,
        short_trade=True,
        trading_constraints: list[TradingConstraint] = [],
    ) -> None:
        if isinstance(targets_ratio_volumes, float | int):
            # make it list with same size as targets_ratio if it's not
            targets_ratio_volumes = [float(targets_ratio_volumes)] * len(targets_ratio)

        if len(targets_ratio) != len(targets_ratio_volumes):
            raise ValueError(
                f"targets_volumes_lot param must be \
                             float or list[float] with same size as targets_pip\
                             {len(targets_ratio_volumes)} != {len(targets_ratio)}"
            )

        if isinstance(targets_in_pip_volumes, float | int):
            # make it list with same size as targets_pip if it's not
            targets_in_pip_volumes = [float(targets_in_pip_volumes)] * len(
                targets_in_pip
            )

        if len(targets_in_pip) != len(targets_in_pip_volumes):
            raise ValueError(
                f"targets_volumes_lot param must be {targets_in_pip}\
                             float or list[float] with same size as targets_pip\
                             {len(targets_in_pip_volumes)} != {len(targets_in_pip)}"
            )

        initial_volume = sum(targets_ratio_volumes) + sum(targets_in_pip_volumes)
        super().__init__(
            exchange_agent,
            initial_volume,
            1,
            long_trade,
            short_trade,
            trading_constraints,
        )

        self.stoploss_pip = stoploss_pip / 10
        self.targets_ratio = targets_ratio
        self.targets_ratio_volumes = targets_ratio_volumes
        self.trail_stop = trail_stop
        self.targets_in_pip = targets_in_pip
        self.targets_in_pip_volumes = targets_in_pip_volumes

    def export_config(self) -> dict:
        conf_dict = super().export_config()
        conf_dict.pop("riskfree_trigger_ratio")
        conf_dict.pop("ratio")
        conf_dict.update(
            {
                "targets_ratio": self.targets_ratio,
                "targets_volumes_lot": self.targets_ratio_volumes,
                "trail_stop": self.trail_stop,
            }
        )
        return conf_dict

    def set_steps(self, pos: Position):
        steps = []
        for pip, volume in zip(self.targets_in_pip, self.targets_in_pip_volumes):
            steps.append(
                Trigger(
                    price=round(
                        abs(pos.entry_price + pos.side.factor() * pip / 10),
                        pos.chart.precision,
                    ),
                    volume=volume,
                    pip_trail_stop=True,
                )
            )

        sl_pip = abs(pos.stoploss - pos.entry_price)
        for ratio, volume in zip(self.targets_ratio, self.targets_ratio_volumes):
            steps.append(
                Trigger(
                    price=round(
                        abs(pos.entry_price + pos.side.factor() * sl_pip * ratio),
                        pos.chart.precision,
                    ),
                    volume=volume,
                )
            )
        pos.steps = steps
        pos.takeprofit = pos.steps[-1].price

    async def open_steps_position(self, pos: Position):
        for step in pos.steps[1:]:  # first step is entry
            step_position = Position(
                pos.chart,
                pos.side,
                pos.entry_price,
                step.volume,
                stoploss=pos.stoploss,
                takeprofit=step.price,
                leverage=pos.leverage,
                source=f"{pos.id}",
                real_trade=True,
            )
            await commands.OpenPosition(step_position, self.exchange_agent).execute()
            pos.entry_price = step_position.entry_price

    def init_stoploss(self, entry_price: float, side: OrderSide) -> float:
        return entry_price - side.factor() * self.stoploss_pip

    def init_takeprofit(self, entry_price: float, side: OrderSide) -> float:
        return 0.0

    async def generate_position(
        self,
        signal: Signal,
        entry_price: float | None = None,
        plot: Plot | None = None,
        sl_base_price: float | None = None,
        *args,
        **kwargs,
    ) -> Position | None:
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

        if sl_base_price is None:
            sl_base_price = entry_price

        precision = signal.chart.precision
        sl = round(self.init_stoploss(sl_base_price, side), precision)
        sl_pip = abs(entry_price - sl)
        tp = round(
            abs(entry_price + side.factor() * sl_pip * self.targets_ratio[-1]),
            precision,
        )

        position = Position(
            signal.chart,
            side,
            entry_price,
            self.initial_volume,
            sl,
            tp,
            self.leverage,
            signal.candle.time + timedelta(seconds=2),
            signal.source,
            real_trade=real_trade,
            plot=plot,
        )
        for constraint in self.trading_constraints:
            res = constraint.check(
                signal, position, self.open_positions, self.closed_positions
            )
            if res is False:
                logger.info(f"Opening New Position Denied due to the: {constraint}")
                return None

        self.open_positions.append(position)
        logger.info(f"New Position on {position.chart}")
        logger.debug(f"The New Position {position}")
        position.in_forex = True

        self.set_steps(position)
        if real_trade:
            await self.open_steps_position(position)
        return position

    def modify_init_sl_tp(self, position: Position):
        position.confiremed = True
        if not position.real_trade:
            return
        self.set_steps(position)
        tp_positions = self.exchange_agent.get_open_positions(
            comment_filter=position.id
        )
        try:
            for tp_pos, step in zip(tp_positions, position.steps[1:]):
                commands.ChangeTakeProfit(tp_pos, self.exchange_agent, step.price)
        except Exception as e:
            logger.error(
                f"Error occurred while modifying take profit: {e} for position {position} and {tp_positions=}"
            )

        logger.info(f"Position Updated on {position.chart}")

    def handler(
        self, position: Position, tick_prices: list[float]
    ) -> TradeCommand | None:
        if not position.confiremed:
            self.modify_init_sl_tp(position)
        if position.confiremed and not position.sended:
            commands.SendPositionSignal(position, self.exchange_agent)

        step = position.current_step
        if step is None:
            logger.warning(f"checking position that its next step is None! {position=}")
            step = position.steps[-1]
            position._current_step_index = len(position.steps) - 1
            # TODO: check above line!!!
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

        logger.info(
            f"Step hit for position {position.id} on {position.chart} with price {step.price} and volume {step.volume}"
        )
        trigger_command = commands.TriggerStep(
            position=position, exchange=self.exchange_agent, trigger=step
        )
        if self.trail_stop:
            trailstop = commands.TrailStoplossbyStep(
                position=position, exchange=self.exchange_agent
            )
            trailstop.bounded_command = trigger_command
        return trigger_command


class SteppingHandlerCrypto(SlTpRatioCrypto):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        leverage: int = 1,
        stoploss_percent: float = 3,
        targets_ratio: list[float] = [1, 1.5, 2],
        initial_volume: float | list[float] = 0.5,
        trail_stop: bool = True,
        long_trade=True,
        short_trade=True,
        trading_constraints: list[TradingConstraint] = [],
    ) -> None:
        if isinstance(initial_volume, float | int):
            # make it list with same size as targets_ratio if it's not
            initial_volume = [float(initial_volume)] * len(targets_ratio)

        if len(targets_ratio) != len(initial_volume):
            raise ValueError(
                f"targets_volumes_lot param must be \
                             float or list[float] with same size as targets_pip\
                             {len(initial_volume)} != {len(targets_ratio)}"
            )

        super().__init__(
            exchange_agent,
            targets_ratio[-1],
            sum(initial_volume),
            leverage=leverage,
            stoploss_percent=stoploss_percent,
            long_trade=long_trade,
            short_trade=short_trade,
        )

        self.targets_ratio = targets_ratio
        self.targets_volumes_lot = initial_volume
        self.trail_stop = trail_stop
        self.trading_constraints = trading_constraints

    def export_config(self) -> dict:
        conf_dict = super().export_config()
        conf_dict.pop("riskfree_trigger_ratio")
        conf_dict.pop("ratio")
        conf_dict.update(
            {
                "targets_ratio": self.targets_ratio,
                "targets_volumes_lot": self.targets_volumes_lot,
                "trail_stop": self.trail_stop,
            }
        )
        return conf_dict

    def set_steps(self, pos: Position):
        steps = []
        sl_percent = abs(pos.stoploss / pos.entry_price - 1) * 100
        for ratio, volume in zip(self.targets_ratio, self.targets_volumes_lot):
            steps.append(
                Trigger(
                    price=round(
                        abs(sl_percent * ratio / 100 + pos.side.factor())
                        * pos.entry_price,
                        pos.chart.precision,
                    ),
                    volume=volume,
                )
            )
        logger.debug(f"steps for position set to: {steps}")
        pos.steps = steps

    async def open_steps_position(self, pos: Position):
        pass

    async def generate_position(
        self,
        signal: Signal,
        entry_price: float | None = None,
        plot: Plot | None = None,
        sl_base_price: float | None = None,
        *args,
        **kwargs,
    ) -> Position | None:
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

        if sl_base_price is None:
            sl_base_price = entry_price

        precision = signal.chart.precision
        sl = round(self.init_stoploss(sl_base_price, side), precision)
        # sl_percent = abs(entry_price - sl) / entry_price
        # tp = round(
        #     abs(sl_percent * self.ratio + side.factor()) * entry_price, precision
        # )

        position = Position(
            signal.chart,
            side,
            entry_price,
            self.initial_volume,
            sl,
            0,
            self.leverage,
            signal.candle.time + timedelta(seconds=2),
            signal.source,
            real_trade=real_trade,
            plot=plot,
        )
        for constraint in self.trading_constraints:
            res = constraint.check(
                signal, position, self.open_positions, self.closed_positions
            )
            if res is False:
                logger.info(f"Opening New Position Denied due to the: {constraint}")
                logger.debug(
                    f"open_pos: {self.open_positions=} | closed_pos: {self.closed_positions} | new_pos: {position}"
                )
                return None

        self.open_positions.append(position)
        logger.info(f"New Position on {position.chart}")
        logger.debug(f"The New Position {position}")

        self.set_steps(position)
        if real_trade:
            await commands.OpenPosition(position, self.exchange_agent).execute()
        return position

    def modify_init_sl_tp(self, position: Position):
        position.confiremed = True
        # update positions if needed
        logger.info(f"Position Updated on {position.chart}")

    def handler(
        self, position: Position, tick_prices: list[float]
    ) -> TradeCommand | None:
        if not position.confiremed:
            self.modify_init_sl_tp(position)
        if position.confiremed and not position.sended:
            position.takeprofit = position.steps[-1].price
            commands.SendPositionSignal(position, self.exchange_agent)

        step = position.current_step
        if step is None:
            logger.warning(f"checking position that its next step is None! {position=}")
            step = position.steps[-1]
            position._current_step_index = len(position.steps) - 1
            # TODO: check above line!!!
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

        logger.info(
            f"Step hit for position {position.id} on {position.chart} with price {step.price} and volume {step.volume}"
        )
        trigger_command = commands.TriggerStep(
            position=position, exchange=self.exchange_agent, trigger=step
        )
        if self.trail_stop:
            trailstop = commands.TrailStoplossbyStep(
                position=position, exchange=self.exchange_agent
            )
            trailstop.bounded_command = trigger_command
        return trigger_command
