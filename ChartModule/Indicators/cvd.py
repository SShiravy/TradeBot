from ChartModule.models import Candle, ChartData, Chart, MarketSide, IndicatorBaseModel
from ChartModule.plot import ChartPlot, DoubleChartPlot
from copy import copy as shallow_copy


class CVD(IndicatorBaseModel):
    def __init__(self, chart: Chart) -> None:
        super().__init__()
        self.chart = chart

    def _calculate(self) -> ChartData:
        cvd_candles: list[Candle] = []

        current_cvd = 0
        max_cvd = -10000000
        min_cvd = 10000000

        for candle in self.candles:
            if candle.side is MarketSide.BULLISH:
                volume_delta = candle.volume
            else:
                volume_delta = -candle.volume

            open_cvd = current_cvd
            current_cvd += volume_delta

            if current_cvd > max_cvd:
                max_cvd = max(current_cvd, max_cvd)
            if current_cvd < min_cvd:
                min_cvd = current_cvd

            body_bottom = min(open_cvd, current_cvd)
            body_top = max(open_cvd, current_cvd)
            cvd_candle = Candle(
                open_cvd, current_cvd, body_top, body_bottom, 0.0, candle.time
            )
            cvd_candles.append(cvd_candle)

        cvd_chart = shallow_copy(self.chart)
        cvd_chart.symbol = "CVD_" + cvd_chart.symbol
        return ChartData(cvd_chart, cvd_candles)

    def _forcast(self) -> MarketSide:
        return MarketSide.NEUTRAL

    def plot(self, plot: ChartPlot):
        return DoubleChartPlot(plot.chartdata, self.set(plot.chartdata.candles))
