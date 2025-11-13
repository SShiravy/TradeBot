from ChartModule import ChartData, Candle, Signal, MarketSide, IndicatorCandleSource
from datetime import datetime
from typing import TypeAlias
import finplot as fplt

fplt.candle_bull_body_color = "#26a69a"
fplt.candle_bull_color = "#26a69a"
fplt.legend_fill_color = "#FFFFFF"
fplt.legend_text_color = "#000000"


class PlotChart:
    def __init__(self, chartdata: ChartData) -> None:
        self.chartdata = chartdata
        self._ax = None

    @property
    def ax(self):
        if not self._ax:
            self._ax = fplt.create_plot(
                f"TimeFrame: {self.chartdata.chart.timeframe.value}"
            )
            self.plot()
        return self._ax

    @ax.setter
    def ax(self, value):
        self._ax = value

    def plot(self):
        df = self.chartdata.generate_dataframe()
        fplt.add_legend(ax=self.ax, text=f"{self.chartdata.chart.symbol}")

        fplt.candlestick_ochl(df[["open", "close", "high", "low"]], ax=self.ax)

    def show(self):
        if not self.ax:
            self.plot()
        fplt.show()

    def save_image(self, name=None, path="Images/") -> str:
        if not self.ax:
            self.plot()
        fplt.autoviewrestore(False)
        fplt.refresh()
        screenshot = self.ax.vb.win.grab()  # type: ignore
        if not name:
            name = str(self.chartdata.chart)
        image_path_name = path + name + ".png"
        screenshot.save(image_path_name)

        return image_path_name

    def draw_straight_line(
        self, start_candle: Candle, end_candle: Candle, source: IndicatorCandleSource
    ):
        color = (
            "#e20000"
            if source in [IndicatorCandleSource.Top, IndicatorCandleSource.High]
            else "#e2c800"
        )

        fplt.add_line(
            (start_candle.time, source(start_candle)),
            (end_candle.time, source(end_candle)),
            color=color,
            width=2,
            interactive=False,
            ax=self.ax,
        )

    def draw_horizontal_line(
        self,
        start_time: datetime,
        end_time: datetime,
        price: float,
        color: str = "#8b0072ff",
    ):
        fplt.add_line(
            (start_time, price),
            (end_time, price),
            color=color,
            style="--",
            width=5,
            ax=self.ax,
        )

    def draw_sl_tp_lines(
        self, start_time: datetime, end_time: datetime, tp_price: float, sl_price: float
    ):
        self.draw_horizontal_line(start_time, end_time, tp_price, "#09ff00b5")
        self.draw_horizontal_line(start_time, end_time, sl_price, "#ff0000d5")

    def mark_signal(self, signal: Signal):
        if signal.side is MarketSide.BULLISH:
            fplt.plot(
                signal.candle.time,
                signal.candle.low * 0.998,
                style="^",
                color="#1DBD1D",
                width=3,
                ax=self.ax,
                legend=signal.source + "_Signal",
            )
        else:
            fplt.plot(
                signal.candle.time,
                signal.candle.high * 1.002,
                style="v",
                color="#BD1D1D",
                width=3,
                ax=self.ax,
                legend=signal.source + "_Signal",
            )

    def mark_candle(
        self, candle: Candle, source: IndicatorCandleSource, legend: str | None = None
    ):
        color = (
            "#e20000"
            if source in [IndicatorCandleSource.Top, IndicatorCandleSource.High]
            else "#e2c800"
        )
        fplt.plot(
            candle.time,
            source(candle),
            style="o",
            color=color,
            width=1,
            ax=self.ax,
            legend=legend,
        )

    def linear_plot(self, x, y, legend: str | None = None):
        fplt.plot(x, y, legend=legend, style="-", ax=self.ax)


class TwoChartPlot:
    def __init__(self, base_chartdata: ChartData, second_chartdata: ChartData) -> None:
        self.base_plot = PlotChart(base_chartdata)
        self.second_plot = PlotChart(second_chartdata)

        ax1, ax2 = fplt.create_plot(
            f"TimeFrame: {base_chartdata.chart.timeframe.value}", rows=2
        )

        self.base_plot.ax = ax1
        self.base_plot.plot()

        self.second_plot.ax = ax2
        self.second_plot.plot()

    def show(self):
        fplt.show()

    def save_image(self, name=None, path="Images/") -> str:
        return self.base_plot.save_image(name, path)


Plot: TypeAlias = PlotChart | TwoChartPlot
