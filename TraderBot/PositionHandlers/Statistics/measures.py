from TraderBot.models import Position
from TraderBot.PositionHandlers.trades_pnl import PnLCalculator
from enum import Enum


class Measure(Enum):
    """
    Unit a price move is expressed in. Moves go through `PnLCalculator`, so they
    match `PnLReport.pnl_pips` / `PnLReport.pnl_percent` (percent includes leverage).
    """

    PIPS = "pips"
    PERCENT = "%"

    @property
    def label(self) -> str:
        return "Pips" if self is Measure.PIPS else "Percent (%)"

    @property
    def decimals(self) -> int:
        return 1 if self is Measure.PIPS else 3

    def format(self, value: float) -> str:
        suffix = " pips" if self is Measure.PIPS else "%"
        return f"{value:,.{self.decimals}f}{suffix}"

    def move(self, position: Position, from_price: float, to_price: float) -> float:
        """Signed move from `from_price` to `to_price`, positive in the position's favour."""
        if self is Measure.PIPS:
            return PnLCalculator.pips(
                position.chart, position.side, from_price, to_price
            )
        return PnLCalculator.percent(
            from_price, to_price, position.side, position.leverage
        )

    def price_distance(
        self, position: Position, reference_price: float, amount: float
    ) -> float:
        """Inverse of `move`: the absolute price distance worth `amount` at `reference_price`."""
        if self is Measure.PIPS:
            return amount * position.chart.pip_factor
        return amount / 100 / position.leverage * reference_price
