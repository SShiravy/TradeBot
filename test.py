# TODO: check round with chart in creating position
from custom_logger import CustomLogger
import logging

CustomLogger(True, consol_log_level=logging.INFO)


async def test_forex_cvd(send_img=False):
    from Forex.agent import ForexAgent
    from ChartModule import Chart, TimeFrame, IndicatorCandleSource
    from TradingModule import TraderBot
    from ChartModule.Indicators import (
        CVD,
        SMA,
        EMA,
        Pivot,
        TrendLine,
    )
    from ChartModule.plot import TwoChartPlot

    chart = Chart("XAUUSD!", TimeFrame.five_minutes)
    agent = ForexAgent()
    chartdata = agent.get_chartdata(chart, 200)
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
        indicator.set(chartdata.candles)
        indicator.plot(two_plot.base_plot)

    two_plot.show()
    img_path = two_plot.save_image(name="ForexTestCVD")
    if send_img:
        await TraderBot().telegram_bot.send_photo_to_channel(img_path, "CVD 5m test")


def start_backtest():
    from BacktestModule import Backtest
    from BacktestModule.forex_configs import forex_fifteen_m_diver

    backtest = Backtest(forex_fifteen_m_diver, 1000)
    backtest.start_backtest(show_image=True)


if __name__ == "__main__":
    start_backtest()
    # import asyncio

    # asyncio.run(mio())
