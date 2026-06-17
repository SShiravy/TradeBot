from ChartModule.models import Signal
from TradingModule.models import OrderSide, Position
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger("TradingConstraint")
# TODO: add n_bar param in checks


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

    def __str__(self) -> str:
        return self.__class__.__name__


class SideConstraint(TradingConstraint):
    def __init__(self, n_pos_each_side: int = 1, n_bar: int = 10) -> None:
        super().__init__()
        self.n_pos_each_side = n_pos_each_side
        self.untill_n_bar = n_bar

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
        for pos in open_positions:
            if pos.side == new_position.side:
                same_side_counter += 1
            if same_side_counter >= self.n_pos_each_side:
                return False
        logger.debug(
            f"{same_side_counter=} | {len(open_positions)=} | {open_positions}"
        )
        return True


class LoseInRowConstraint(TradingConstraint):
    def __init__(
        self, n_long_lose: int = 3, n_short_lose: int = 3, n_bar: int = 10
    ) -> None:
        super().__init__()
        self.n_long_lose = n_long_lose
        self.n_short_lose = n_short_lose

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
            if new_position.side is OrderSide.BUY
            else self.n_short_lose
        )
        for pos in closed_positions[::-1]:
            if pos.side == new_position.side:
                lose_in_row_counter += 1
            else:
                return True
            if lose_in_row_counter >= constraint:
                return False
        return True
