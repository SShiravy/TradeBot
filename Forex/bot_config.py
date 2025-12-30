from Forex.agent import ForexAgent
from ChartModule.Indicators import CVD
from ChartModule import Chart, ChartData
from TradingModule import ExchangeAgent
from DivergenceStrategy.divergence import Divergence, DivergenceTradeConfig
from dataclasses import dataclass, field
from datetime import timedelta


@dataclass(kw_only=True)
class ForexDiverTradeConfig(DivergenceTradeConfig):
    second_chart: Chart
    agent: ExchangeAgent = field(default=ForexAgent(), init=False)
    strategy: Divergence  # type: ignore[override]
    merge_two_chart_time: bool = field(default=False)

    def get_chartdata(self, n_bar: int | None = None) -> tuple[ChartData, ChartData]:  # type: ignore[override]
        mulitplier = 2 if self.merge_two_chart_time else 1
        base_chartdata = self.agent.get_chartdata(
            self.chart, n_bar if n_bar else self.n_candle_check
        )
        second_chartdata = self.agent.get_chartdata(
            self.second_chart,
            n_bar * mulitplier if n_bar else self.n_candle_check * mulitplier,
        )

        if base_chartdata is None or second_chartdata is None:
            raise ValueError(f"chart data is None from {self.agent.__class__.__name__}")

        if self.merge_two_chart_time:
            base_index = 0
            second_index = 0
            base_candles = []
            second_candles = []
            for _ in range(len(second_chartdata)):
                if base_index >= len(base_chartdata):
                    break
                base_time = base_chartdata[base_index].time.replace(
                    second=0, microsecond=0
                )
                second_time = second_chartdata[second_index].time.replace(
                    second=0, microsecond=0
                )
                if (base_time - second_time).seconds <= 60:
                    base_candles.append(base_chartdata[base_index])
                    second_candles.append(second_chartdata[second_index])
                    base_index += 1
                    second_index += 1
                    continue

                elif base_time > second_time:
                    second_index += 1
                    continue

                else:  # base_time<second_time:
                    base_index += 1
                    continue

            base_chartdata.candles = base_candles
            second_chartdata.candles = second_candles

        if self.heikingashi_chartdata:
            base_chartdata = base_chartdata.give_heikingashi_chartdata()
            second_chartdata = second_chartdata.give_heikingashi_chartdata()
        return base_chartdata, second_chartdata

    async def task(self):
        if not ForexAgent().check_market_open(self.chart):
            return timedelta(hours=2)
        return await super().task()


@dataclass(kw_only=True)
class CvdDiverTradeConfig(DivergenceTradeConfig):
    second_chart: Chart = field(init=False)
    agent: ExchangeAgent = field(default=ForexAgent())
    strategy: Divergence  # type: ignore[override]

    def get_chartdata(self) -> tuple[ChartData, ChartData]:  # type: ignore[override]
        base_chartdata = self.agent.get_chartdata(self.chart, self.n_candle_check)

        if base_chartdata is None:
            raise ValueError(f"chart data is None from {self.agent.__class__.__name__}")

        second_chartdata = CVD(self.chart).set(base_chartdata.candles)
        if self.heikingashi_chartdata:
            base_chartdata.give_heikingashi_chartdata()

        return base_chartdata, second_chartdata

    async def task(self):
        if not ForexAgent().check_market_open(self.chart):
            return timedelta(hours=2)
        return await super().task()
