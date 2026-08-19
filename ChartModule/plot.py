from ChartModule import ChartData, Candle, Signal, MarketSide, CandlesSource
from datetime import datetime, timezone
from typing import TypeAlias, Any
from abc import ABC, abstractmethod
import finplot as fplt

fplt.candle_bull_body_color = "#26a69a"
fplt.candle_bull_color = "#26a69a"
fplt.legend_fill_color = "#FFFFFF"
fplt.legend_text_color = "#000000"
fplt.display_timezone = timezone.utc


class BaseChartPlot(ABC):
    @abstractmethod
    def show(self):
        pass

    @abstractmethod
    def save_image(self, name=None, path="Images/") -> str:
        pass

    @property
    @abstractmethod
    def chart_plot(self) -> Any:
        pass

    @abstractmethod
    def give_chartdata(self) -> ChartData:
        pass


class ChartPlot(BaseChartPlot):
    def __init__(self, chartdata: ChartData, plot_n_candles: int = 100) -> None:
        self.chartdata = chartdata
        self._ax = None
        self._y_max = 0
        self._y_min = 100000000
        self.plot_n_candles = plot_n_candles

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

    @property
    def chart_plot(self):
        return self

    def give_chartdata(self) -> ChartData:
        return self.chartdata

    def set_y_range(self, boundaries: tuple[float, float]):
        self._y_min = min(self._y_min, boundaries[0] * 0.9995, boundaries[1] * 0.9995)
        self._y_max = max(self._y_max, boundaries[0] * 1.0001, boundaries[1] * 1.0001)

    def plot(self):
        if len(self.chartdata.candles) > self.plot_n_candles:
            self.chartdata.candles = self.chartdata.candles[-self.plot_n_candles :]
        df = self.chartdata.generate_dataframe()
        fplt.add_legend(ax=self.ax, text=f"{self.chartdata.chart.symbol}")

        fplt.candlestick_ochl(df[["open", "close", "high", "low"]], ax=self.ax)

        self.set_y_range((float(df["high"].max()), float(df["low"].min())))

    def show(self):
        if not self.ax:
            self.plot()
        fplt.set_y_range(self._y_min, self._y_max, self.ax)
        fplt.show()

    def save_image(self, name=None, path="Images/") -> str:
        if not self.ax:
            self.plot()
        fplt.set_y_range(self._y_min, self._y_max, self.ax)
        fplt.autoviewrestore(False)
        fplt.refresh()
        screenshot = self.ax.vb.win.grab()  # type: ignore
        if not name:
            name = str(self.chartdata.chart)
        image_path_name = path + name + ".png"
        screenshot.save(image_path_name)

        return image_path_name

    def draw_line(self, x1, y1, x2, y2, color="#cb00e2", width=1, ax=None):
        fplt.add_line(
            (x1, y1),
            (x2, y2),
            color=color,
            width=width,
            interactive=False,
            ax=self.ax if not ax else ax,
        )

    def draw_straight_line(
        self, start_candle: Candle, end_candle: Candle, source: CandlesSource, ax=None
    ):
        color = (
            "#e20000"
            if source in [CandlesSource.Top, CandlesSource.High]
            else "#e2c800"
        )

        fplt.add_line(
            (start_candle.time, source(start_candle)),
            (end_candle.time, source(end_candle)),
            color=color,
            width=2,
            interactive=False,
            ax=self.ax if not ax else ax,
        )

    def draw_horizontal_line(
        self,
        start_time: datetime,
        end_time: datetime,
        price: float,
        color: str = "#8b0072ff",
        ax=None,
    ):
        fplt.add_line(
            (start_time, price),
            (end_time, price),
            color=color,
            style="--",
            width=5,
            ax=self.ax if not ax else ax,
        )

    def draw_filled_rect(
        self,
        start_time: datetime,
        end_time: datetime,
        upper_price: float,
        lower_price: float,
        color: str = "#8b007240",
        ax=None,
    ):
        fplt.add_rect(
            (start_time, upper_price),
            (end_time, lower_price),
            color=color,
            interactive=False,
            ax=self.ax if not ax else ax,
        )

    def draw_sl_tp_lines(
        self, start_time: datetime, end_time: datetime, tp_price: float, sl_price: float
    ):
        self.draw_horizontal_line(start_time, end_time, tp_price, "#09ff00b5")
        self.draw_horizontal_line(start_time, end_time, sl_price, "#ff0000d5")

    def draw_label(
        self,
        time,
        price: float,
        text: str,
        color: str = "#000000",
        anchor: tuple[float, float] = (0.5, 0.5),
        ax=None,
    ):
        fplt.add_text(
            (time, price),
            text,
            color=color,
            anchor=anchor,
            ax=self.ax if not ax else ax,
        )

    def mark_signal(self, signal: Signal, ax=None):
        if signal.side is MarketSide.BULLISH:
            fplt.plot(
                signal.candle.time,
                signal.candle.low * 0.9995,
                style="^",
                color="#1DBD1D",
                width=3,
                ax=self.ax if not ax else ax,
                # legend=signal.source + "_Signal",
            )
        else:
            fplt.plot(
                signal.candle.time,
                signal.candle.high * 1.0005,
                style="v",
                color="#BD1D1D",
                width=3,
                ax=self.ax if not ax else ax,
                # legend=signal.source + "_Signal",
            )

    def mark_price(self, time, price: float, side: MarketSide, ax=None):
        if side is MarketSide.BULLISH:
            fplt.plot(
                time,
                price,
                style="^",
                color="#1DBD1D",
                width=3,
                ax=self.ax if not ax else ax,
            )
        else:
            fplt.plot(
                time,
                price,
                style="v",
                color="#BD1D1D",
                width=3,
                ax=self.ax if not ax else ax,
            )

    def mark_candle(
        self,
        candle: Candle,
        source=CandlesSource.Open,
        legend: str | None = None,
        color: str | None = None,
        ax=None,
    ):
        color = (
            color
            if color
            else (
                "#e20000"
                if source in [CandlesSource.Top, CandlesSource.High]
                else "#e2c800"
            )
        )
        fplt.plot(
            candle.time,
            source(candle),
            style="o",
            color=color,
            width=1,
            legend=legend,
            ax=self.ax if not ax else ax,
            # legend=legend,
        )

    def linear_plot(
        self,
        x,
        y,
        legend: str | None = None,
        color: str = "#410087",
        thickness=2,
        ax=None,
    ):
        fplt.plot(
            x,
            y,
            style="-",
            ax=self.ax if not ax else ax,
            color=color,
            legend=legend,
            width=thickness,
        )


class DoubleChartPlot(BaseChartPlot):
    def __init__(
        self,
        base_chartdata: ChartData,
        second_chartdata: ChartData,
        plot_n_candles: int = 100,
    ) -> None:
        self.base_plot = ChartPlot(base_chartdata, plot_n_candles=plot_n_candles)
        self.second_plot = ChartPlot(second_chartdata, plot_n_candles=plot_n_candles)
        self.plot_n_candles = plot_n_candles

        ax1, ax2 = fplt.create_plot(
            f"TimeFrame: {base_chartdata.chart.timeframe.value}", rows=2
        )

        self.base_plot.ax = ax1
        self.base_plot.plot()

        self.second_plot.ax = ax2
        self.second_plot.plot()

    @property
    def chart_plot(self):
        return self.base_plot

    def give_chartdata(self) -> ChartData:
        return self.base_plot.chartdata

    def show(self):
        self.base_plot.show()

    def save_image(self, name=None, path="Images/") -> str:
        return self.base_plot.save_image(name, path)


class ChartWithOscillatorPlot(ChartPlot):
    def __init__(
        self,
        base_chartdata: ChartData,
        oscillator_data: dict[int, float],
        plot_n_candles: int = 100,
        label: str = "Oscillator",
        color: str = "#002576",
    ) -> None:
        self.base_plot = ChartPlot(base_chartdata, plot_n_candles=plot_n_candles)
        self.oscillator_data = oscillator_data
        self.plot_n_candles = plot_n_candles

        ax1, ax2 = fplt.create_plot(
            f"TimeFrame: {base_chartdata.chart.timeframe.value}", rows=2
        )
        self._ax = ax1

        self.base_plot.ax = ax1
        self.base_plot.plot()

        fplt.plot(
            oscillator_data.keys(),
            oscillator_data.values(),
            ax=ax2,
            legend=label,
            color=color,
            width=1,
        )
        self.oscillator_ax = ax2

    @property
    def chart_plot(self):
        return self.base_plot

    def give_chartdata(self) -> ChartData:
        return self.base_plot.chartdata

    def show(self):
        self.base_plot.show()

    def save_image(self, name=None, path="Images/") -> str:
        return self.base_plot.save_image(name, path)


Plot: TypeAlias = ChartPlot | DoubleChartPlot
