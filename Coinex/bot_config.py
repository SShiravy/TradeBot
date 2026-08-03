from Coinex import CoinexAgent
from ChartModule import Chart, ChartData
from DivergenceStrategy import Divergence, TwoChartDiverTradeConfig
from dataclasses import dataclass


@dataclass(kw_only=True)
class CoinexDiverTradeConfig(TwoChartDiverTradeConfig):
    second_chart: Chart
    agent: CoinexAgent  # type: ignore[override]
    strategy: Divergence  # type: ignore[override]

    def get_chartdata(self, n_bar: int | None = None) -> tuple[ChartData, ChartData]:  # type: ignore[override]
        base_chartdata = self.agent.get_chartdata(
            self.chart, n_bar if n_bar else self.n_candle_check
        )
        other_chartdata = self.agent.get_chartdata(
            self.second_chart, n_bar if n_bar else self.n_candle_check
        )

        if base_chartdata is None or other_chartdata is None:
            raise ValueError(f"chart data is None from {self.agent.__class__.__name__}")

        crosspair_chart = Chart(
            symbol=base_chartdata.chart.symbol.replace("USDT", "")
            + other_chartdata.chart.symbol.replace("USDT", ""),
            timeframe=base_chartdata.chart.timeframe,
            precision=base_chartdata.chart.precision,
        )
        second_chartdata = ChartData.generate_crosspair(
            base_chartdata, other_chartdata, crosspair_chart
        )
        if self.heikingashi_chartdata:
            base_chartdata = base_chartdata.give_heikingashi_chartdata()
            second_chartdata = second_chartdata.give_heikingashi_chartdata()
        return base_chartdata, second_chartdata
