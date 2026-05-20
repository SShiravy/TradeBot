from datetime import timedelta
from ChartModule.models import MarketSide, Signal
from ChartModule.plot import Plot
from TradingModule.PositionHandlers.ratio_handlers import (
    SlTpRatioCrypto,
    SlTpRatioForex,
)
from TradingModule.models import ExchangeAgent, OrderSide, Position, Trigger
from TradingModule.commands import TradeCommand
from TradingModule import commands
import numpy as np
import logging


logger = logging.getLogger("PositionHandler")


class RatioSteppingForex(SlTpRatioForex):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        stoploss_pip: int = 10,
        targets_ratio: list[float] = [1, 1.5, 2],
        initial_volume: float | list[float] = 0.01,
        trail_stop: bool = True,
        long_trade=True,
        short_trade=True,
    ) -> None:
        if isinstance(initial_volume, float | int):
            # make it list with same size as targets_pip if it's not
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
            stoploss_pip,
            long_trade=long_trade,
            short_trade=short_trade,
        )

        self.targets_ratio = targets_ratio
        self.targets_volumes_lot = initial_volume
        self.trail_stop = trail_stop

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
        sl_pip = abs(pos.stoploss - pos.entry_price)
        for ratio, volume in zip(self.targets_ratio, self.targets_volumes_lot):
            steps.append(
                Trigger(
                    price=round(
                        abs(pos.entry_price + pos.side.factor() * sl_pip * ratio),
                        pos.chart.precision,
                    ),
                    volume=volume,
                )
            )
        logger.debug(f"steps for position set to: {steps}")
        pos.steps = steps

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

    async def generate_position(
        self,
        signal: Signal,
        entry_price: float | None = None,
        plot: Plot | None = None,
        sl_base_price: float | None = None,
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

        if sl_base_price is None:
            sl_base_price = entry_price

        precision = signal.chart.precision
        sl = round(self.init_stoploss(sl_base_price, side), precision)
        sl_pip = abs(entry_price - sl)
        tp = round(abs(entry_price + side.factor() * sl_pip * self.ratio), precision)

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

        step = position.current_step
        if step is None:
            logger.warning(f"checking position that its next step is None! {position=}")
            step = position.previous_step
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


class RatioSteppingCrypto(SlTpRatioCrypto):
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        stoploss_percent: int = 10,
        targets_ratio: list[float] = [1, 1.5, 2],
        initial_volume: float | list[float] = 10,
        trail_stop: bool = True,
        long_trade=True,
        short_trade=True,
    ) -> None:
        if isinstance(initial_volume, float | int):
            # make it list with same size as targets_percent if it's not
            initial_volume = [float(initial_volume)] * len(targets_ratio)

        if len(targets_ratio) != len(initial_volume):
            raise ValueError(
                f"targets_volumes param must be \
                             float or list[float] with same size as targets_ratio\
                             {len(initial_volume)} != {len(targets_ratio)}"
            )

        super().__init__(
            exchange_agent,
            targets_ratio[-1],
            sum(initial_volume),
            stoploss_percent,
            long_trade=long_trade,
            short_trade=short_trade,
        )

        self.targets_ratio = targets_ratio
        self.targets_volumes = initial_volume
        self.trail_stop = trail_stop

    def export_config(self) -> dict:
        conf_dict = super().export_config()
        conf_dict.pop("riskfree_trigger_ratio")
        conf_dict.pop("ratio")
        conf_dict.update(
            {
                "targets_ratio": self.targets_ratio,
                "targets_volumes": self.targets_volumes,
                "trail_stop": self.trail_stop,
            }
        )
        return conf_dict

    def set_steps(self, pos: Position):
        steps = []
        sl_percent = abs(pos.entry_price - pos.stoploss) / pos.entry_price
        for ratio, volume in zip(self.targets_ratio, self.targets_volumes):
            steps.append(
                Trigger(
                    price=round(
                        abs(sl_percent * ratio + pos.side.factor()) * pos.entry_price,
                        pos.chart.precision,
                    ),
                    volume=volume,
                )
            )
        logger.debug(f"steps for position set to: {steps}")
        pos.steps = steps

    async def open_steps_position(self, pos: Position):
        # for step in pos.steps[1:]:  # first step is entry
        #     step_position = Position(
        #         pos.chart,
        #         pos.side,
        #         pos.entry_price,
        #         step.volume,
        #         stoploss=pos.stoploss,
        #         takeprofit=step.price,
        #         leverage=pos.leverage,
        #         source=f"{pos.id}",
        #         real_trade=True,
        #     )
        #     await commands.OpenPosition(step_position, self.exchange_agent).execute()
        pass

    async def generate_position(
        self,
        signal: Signal,
        entry_price: float | None = None,
        plot: Plot | None = None,
        sl_base_price: float | None = None,
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

        if sl_base_price is None:
            sl_base_price = entry_price

        precision = signal.chart.precision
        sl = round(self.init_stoploss(sl_base_price, side), precision)
        sl_percent = abs(entry_price - sl) / entry_price
        tp = round(
            abs(sl_percent * self.ratio + side.factor()) * entry_price, precision
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
        self.open_positions.append(position)
        logger.info(f"New Position on {position.chart}")
        logger.debug(f"The New Position {position}")

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

        step = position.current_step
        if step is None:
            logger.warning(f"checking position that its next step is None! {position=}")
            step = position.previous_step
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
