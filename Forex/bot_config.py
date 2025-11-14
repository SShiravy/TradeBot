from Forex.agent import ForexAgent
from ChartModule.Indicators import CVD
from ChartModule import Chart, ChartData
from TradingModule import ExchangeAgent
from TradingModule.Strategies import Divergence, DivergenceTradeConfig
from dataclasses import dataclass, field


# TODO: implement two days off in task , and one houre off


@dataclass(kw_only=True)
class ForexDiverTradeConfig(DivergenceTradeConfig):
    second_chart: Chart
    agent: ExchangeAgent = field(default=ForexAgent())
    strategy: Divergence  # type: ignore[override]


@dataclass(kw_only=True)
class CvdDiverTradeConfig(DivergenceTradeConfig):
    second_chart: Chart = field(init=False)
    agent: ExchangeAgent = field(default=ForexAgent())
    strategy: Divergence  # type: ignore[override]

    def get_chartdata(self) -> tuple[ChartData, ChartData]:  # type: ignore[override]
        base_chartdata = self.agent.get_chartdata(self.chart, self.n_bar_check)

        if base_chartdata is None:
            raise ValueError(f"chart data is None from {self.agent.__class__.__name__}")

        second_chartdata = CVD(self.chart).set(base_chartdata.candles)

        return base_chartdata, second_chartdata
