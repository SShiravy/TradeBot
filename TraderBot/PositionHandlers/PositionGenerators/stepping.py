from ChartModule.models import Signal
from TraderBot.PositionHandlers.manager import PositionGenerator
import TraderBot.Commands as commands
from TraderBot.models import (
    ExchangeAgent,
    PositionSide,
    Position,
    PositionType,
    Trigger,
    TriggerType,
)
import logging


logger = logging.getLogger("PositionManager")


class ForexStepping(PositionGenerator):
    def __init__(
        self,
        leverage: int = 1,
        sl_pip: int = 3,
        tp_ratio: list[float] = [1, 2, 3],
        tp_ratio_volumes: list[float] = [0.01, 0.01, 0.1],
        tp_pip: list[float] = [],
        tp_pip_volumes: list[float] = [],
        trail_stop: bool = True,
    ) -> None:
        if len(tp_ratio) != len(tp_ratio_volumes):
            raise ValueError(
                f"tp_volumes_lot param must be \
                             float or list[float] with same size as tp_pip\
                             {len(tp_ratio_volumes)} != {len(tp_ratio)}"
            )

        if len(tp_pip) != len(tp_pip_volumes):
            raise ValueError(
                f"tp_volumes_lot param must be {tp_pip}\
                             float or list[float] with same size as tp_pip\
                             {len(tp_pip_volumes)} != {len(tp_pip)}"
            )

        initial_volume = sum(tp_ratio_volumes) + sum(tp_pip_volumes)
        self.initial_volume = initial_volume
        self.leverage = leverage
        self.trail_stop = trail_stop
        self.sl_pip = sl_pip
        self.tp_pip = tp_pip
        self.tp_pip_volumes = tp_pip_volumes
        self.tp_ratio = tp_ratio
        self.tp_ratio_volumes = tp_ratio_volumes

    def init_stoploss(
        self, entry_price: float, side: PositionSide, pip_factor: float
    ) -> Trigger:
        return Trigger(
            price=entry_price - side.factor * self.sl_pip * pip_factor,
            volume=self.initial_volume,
            cross_direction=side.factor,
            command=commands.StopLoss(bounded_command=commands.StoplossHitReport()),
            type=TriggerType.SL,
        )

    def give_tp_trailstop_command(self, new_sl: float):
        return commands.TakeProfit(
            commands.TrailStoploss(
                new_stoploss=new_sl,
                bounded_command=commands.TriggerHitReport(trail_stop=True),
            )
        )

    def give_tp_command(self):
        return commands.TakeProfit(
            bounded_command=commands.TriggerHitReport(trail_stop=False)
        )

    def generate_triggers(
        self,
        entry_price: float,
        side: PositionSide,
        sl_price: float,
        pip_factor: float,
    ) -> list[Trigger]:
        steps: list[Trigger] = []
        for pip, volume in zip(self.tp_pip, self.tp_pip_volumes):
            steps.append(
                Trigger(
                    price=entry_price + pip * side.factor * pip_factor,
                    volume=volume,
                    cross_direction=side.factor,
                    type=TriggerType.TP,
                )
            )

        sl_distance = abs(sl_price - entry_price)
        for ratio, volume in zip(self.tp_ratio, self.tp_ratio_volumes):
            steps.append(
                Trigger(
                    price=entry_price + sl_distance * ratio * side.factor,
                    volume=volume,
                    cross_direction=side.factor,
                    type=TriggerType.TP,
                )
            )

        steps.sort(key=lambda t: t.price * side.factor)

        for i, step in enumerate(steps):
            if self.trail_stop:
                previous_price = steps[i - 1].price if i > 0 else entry_price
                step.command = self.give_tp_trailstop_command(previous_price)
            else:
                step.command = self.give_tp_command()

        return steps

    def export_config(self) -> dict:
        return {
            "Handler": self.__class__.__name__,
            "initial_volume": self.initial_volume,
            "leverage": self.leverage,
            "sl_pip": self.sl_pip,
            "tp_ratio": self.tp_ratio,
            "tp_ratio_volumes": self.tp_ratio_volumes,
            "tp_pip": self.tp_pip,
            "tp_pip_volumes": self.tp_pip_volumes,
        }

    async def generate(
        self,
        signal: Signal,
        entry_price: float,
        **kwargs,
    ) -> Position | None:
        """
        set sl_base_price parameter if needed
        """
        side = PositionSide.convert_market_side(signal.side)
        sl_base_price = kwargs.get("sl_base_price", entry_price)
        sl = self.init_stoploss(sl_base_price, side, signal.chart.pip_factor)
        triggers = self.generate_triggers(
            entry_price, side, sl.price, signal.chart.pip_factor
        )
        position = Position(
            signal.chart,
            side,
            entry_price,
            self.initial_volume,
            triggers,
            sl,
            self.leverage,
            type=PositionType.MARKET,
            source=signal.source,
        )

        logger.info(
            f"New Position on {position.chart} Generated by {self.__class__.__name__}"
        )
        return position
