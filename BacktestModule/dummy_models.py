from copy import deepcopy
from ChartModule import ChartData, Chart
from TradingModule.PositionHandlers.model import PositionHandler
from TradingModule.models import ExchangeAgent, OrderSide, Position
from datetime import datetime
import logging

logger = logging.getLogger("DummyAgent")


class DummyAgent(ExchangeAgent):
    def __init__(
        self,
        real_agent: ExchangeAgent,
        open_positions=[],
        chartdata: ChartData | None = None,
        start_index=0,
    ) -> None:
        self.real_agent = real_agent
        self.current_price = 0.0
        self.open_positions = open_positions
        logger.info("dummy agent initilized")
        self.index = start_index
        self.chartdata = chartdata

    def check_chart(self, chart: Chart) -> bool:
        return self.real_agent.check_chart(chart)

    def get_chartdata(self, chart: Chart, n_bars=100) -> ChartData | None:
        if self.chartdata:
            candles = deepcopy(self.chartdata[: self.index])
            data = ChartData(self.chartdata.chart, candles, self.chartdata.indicators)
            logger.debug(f"agent get chartdata: {len(data)=}")
            return data
        return self.real_agent.get_chartdata(chart, n_bars)

    def get_candles_since(self, chart: Chart, time: datetime):
        return self.real_agent.get_candles_since(chart, time)

    def open_position(self, position: Position) -> float | None:
        return position.entry_price

    def get_open_positions(self, chart: Chart):
        return self.open_positions

    def change_stoploss(self, position: Position, price: float) -> bool:
        return True

    def change_takeprofit(self, position: Position, price: float) -> bool:
        return True

    def partial_close(self, position: Position, volume: float) -> float | None:
        logger.info(f"partial close {volume} on {self.current_price}")
        return self.current_price

    def close_position(self, position: Position) -> float | None:
        logger.info(f"close position on {self.current_price}")
        return self.current_price


class DummyPositionHanler(PositionHandler):
    def __init__(self) -> None:
        self.open_positions = []
        self.closed_positions = []

    async def generate_position(self, signal, *args, **kwargs) -> Position:
<<<<<<< HEAD:BacktestModule/dummy_agent.py
        return None # type:ignore
=======
        return None  # type:ignore
>>>>>>> master:BacktestModule/dummy_models.py

    def init_stoploss(self, entry_price: float, side: OrderSide) -> float:
        return 0.0

    def init_takeprofit(self, entry_price: float, side: OrderSide) -> float:
        return 0.0

    def export_config(self) -> dict:
        return super().export_config()
