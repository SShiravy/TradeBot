from ChartModule.models import Signal
from TradingModule.models import PositionSide, Position
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger("TradingConstraint")


class TradingConstraint(ABC):
    @abstractmethod
    def check(
        self,
        signal: Signal,
        new_position: Position,
        open_positions: list = [],
        closed_positions: list = [],
    ) -> bool:
        pass

    def give_passed_candles(self, old_pos: Position, new_pos: Position):
        passed_candle = (new_pos.defined_timestamp - old_pos.defined_timestamp)// (
            new_pos.chart.timeframe.minutes * 60
        )
        return passed_candle

    def export_config(self) -> dict:
        return {
            "class": self.__class__.__name__,
            **self.__dict__,
        }

    def __str__(self) -> str:
        return self.__class__.__name__


class SideConstraint(TradingConstraint):
    def __init__(
        self,
        n_pos_each_side: int = 1,
        n_bar: int = 30,
        check_closed_positions: bool = True,
    ) -> None:
        super().__init__()
        self.n_pos_each_side = n_pos_each_side
        self.untill_n_bar = n_bar
        self.check_closed_positions = check_closed_positions

    def check(
        self,
        signal: Signal,
        new_position: Position,
        open_positions: list[Position] = [],
        closed_positions: list[Position] = [],
        *args,
        **kwargs,
    ) -> bool:
        same_side_counter = 0
        for pos in open_positions[::-1]:
            passed_candle = self.give_passed_candles(old_pos=pos, new_pos=new_position)
            if passed_candle >= self.untill_n_bar:
                continue
            if pos.side == new_position.side:
                same_side_counter += 1
            if same_side_counter >= self.n_pos_each_side:
                logger.info(
                    f"Side Constraint Filtered position: {same_side_counter=} | {pos.side=} | {new_position.side=} | {passed_candle}"
                )
                return False

        if not self.check_closed_positions:
            return True

        for pos in closed_positions[::-1]:
            passed_candle = self.give_passed_candles(old_pos=pos, new_pos=new_position)
            if passed_candle > self.untill_n_bar:
                continue
            if pos.side == new_position.side:
                same_side_counter += 1
            if same_side_counter >= self.n_pos_each_side:
                logger.info(
                    f"Side Constraint Filtered position: {same_side_counter=} | {pos.side=} | {new_position.side=} | {passed_candle}"
                )
                return False

        return True


class LoseInRowConstraint(TradingConstraint):
    def __init__(
        self, n_long_lose: int = 3, n_short_lose: int = 3, n_bar: int = 30
    ) -> None:
        super().__init__()
        self.n_long_lose = n_long_lose
        self.n_short_lose = n_short_lose
        self.n_bar = n_bar

    def check(
        self,
        signal: Signal,
        new_position: Position,
        open_positions: list[Position] = [],
        closed_positions: list[Position] = [],
        *args,
        **kwargs,
    ) -> bool:
        lose_in_row_counter = 0
        constraint = (
            self.n_long_lose
            if new_position.side is PositionSide.LONG
            else self.n_short_lose
        )
        for pos in closed_positions[::-1]:
            passed_candle = self.give_passed_candles(old_pos=pos, new_pos=new_position)
            if passed_candle > self.n_bar:
                continue
            if pos.side == new_position.side:
                if pos.pnl_dollar >= 0:
                    return True
                lose_in_row_counter += 1
            if lose_in_row_counter >= constraint:
                return False
        return True
