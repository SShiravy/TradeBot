# TODO: check round with chart in creating position
# TODO: add if not self.check_market_open(position.chart) on begining of bot


def test_forex_cvd():
    from Forex.agent import ForexAgent
    from ChartModule import Chart, TimeFrame
    from ChartModule.Indicators import (
        CVD,
        SMA,
        EMA,
        Pivot,
        TrendLine,
        IndicatorCandleSource,
    )
    from ChartModule.plot import TwoChartPlot

    chart = Chart("XAUUSD!", TimeFrame.one_minute)
    agent = ForexAgent()
    chartdata = agent.get_chartdata(chart, 300)
    if not chartdata:
        raise TypeError("No chartdata")
    two_plot = TwoChartPlot(chartdata, CVD(chart).set(chartdata.candles))
    all_indicators = [
        SMA(10),
        EMA(30),
        Pivot(IndicatorCandleSource.High, 10, 10),
        TrendLine(IndicatorCandleSource.Low, 4, 100),
    ]
    for indicator in all_indicators:
        print(indicator.__class__.__name__)
        indicator.set(chartdata.candles)
        indicator.plot(two_plot.base_plot)

    two_plot.show()
    two_plot.save_image(name="ForexTestCVD")


if __name__ == "__main__":
    test_forex_cvd()
