from custom_logger import CustomLogger
import logging

CustomLogger(True, consol_log_level=logging.INFO)


def test_moving_color():
    from BacktestModule.forex_configs import forex_one_m_diver
    from ChartModule.Indicators import MovingColor, MovingCandleLength
    import finplot as fplt

    config = forex_one_m_diver
    chartdata = config.agent.get_chartdata(config.chart, 3000)
    if chartdata is None:
        raise TypeError("mio")

    ax1, ax2 = fplt.create_plot(f"TimeFrame: {chartdata.chart.timeframe.value}", rows=2)
    df = chartdata.generate_dataframe()
    fplt.add_legend(ax=ax1, text=f"{chartdata.chart.symbol}")
    fplt.candlestick_ochl(df[["open", "close", "high", "low"]], ax=ax1)

    ml = MovingCandleLength(300)
    ml.set(chartdata.candles)
    ml.plot(ax2)
    mc = MovingColor(300)
    mc.set(chartdata.candles)
    mc.plot(ax2)
    fplt.show()


async def start_backtest():
    from BacktestModule import Backtest
    from BacktestModule.forex_configs import forex_one_m_diver

    # Check forex
    backtest = Backtest(forex_one_m_diver, 1000)
    await backtest.start_backtest(show_image=True)


if __name__ == "__main__":
    # test_moving_color()
    import asyncio
    # TODO: partial close
    # TODO: position handler with MA and control tp sl with it
    # TODO: multiple loss in a row for long and short handler
    # TODO: pos open candle should not check in position handler
    # TODO: add backtest bot

    asyncio.run(start_backtest())
