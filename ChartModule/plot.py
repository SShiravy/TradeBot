import numpy as np
from typing import TypeAlias
from abc import ABC, abstractmethod
from pathlib import Path
import finplot as fplt
from Settings.timing import TimeHandler
from ChartModule import ChartData, Signal, MarketSide, CandlesSource


BEARISH_COLOR = "#c60000"
BULLISH_COLOR = "#17b000"


def apply_theme() -> None:
    """Global finplot styling"""
    fplt.candle_bull_body_color = "#159350"
    fplt.candle_bull_color = "#159350"
    fplt.legend_fill_color = "#FFFFFF"
    fplt.legend_text_color = "#000000"
    fplt.display_timezone = TimeHandler._tz
    fplt.right_margin_candles = 10


apply_theme()


class ChartPane:
    """
    One axis. Owns its own y-range tracking and every drawing primitive.
    A pane may or may not carry candle data -- an oscillator pane has none.
    """

    def __init__(self, ax, chartdata: ChartData | None = None) -> None:
        self.ax = ax
        self.chartdata = chartdata
        self._y_min: float | None = None
        self._y_max: float | None = None

    def extend_y_range(self, low: float, high: float, pad: float = 0.0005) -> None:
        low, high = min(low, high), max(low, high)
        low *= 1 - pad
        high *= 1 + pad
        self._y_min = low if self._y_min is None else min(self._y_min, low)
        self._y_max = high if self._y_max is None else max(self._y_max, high)

    def apply_y_range(self) -> None:
        if self._y_min is not None and self._y_max is not None:
            fplt.set_y_range(self._y_min, self._y_max, self.ax)

    def draw_candles(self, legend: str | None = None) -> None:
        if self.chartdata is None:
            raise ValueError("This pane has no chartdata to draw candles from")
        df = self.chartdata.generate_dataframe()
        if legend:
            fplt.add_legend(ax=self.ax, text=legend)
        fplt.candlestick_ochl(df[["open", "close", "high", "low"]], ax=self.ax)
        self.extend_y_range(min(self.chartdata.low), max(self.chartdata.high))

    def draw_line(self, x1, y1, x2, y2, color: str = "#cb00e2", width: int = 2) -> None:
        fplt.add_line(
            (x1, y1), (x2, y2), color=color, width=width, interactive=False, ax=self.ax
        )

    def draw_directional_line(
        self,
        start_timestamp: int,
        start_price: float,
        end_timestamp: int,
        end_price: float,
        side: MarketSide,
    ) -> None:
        color = BEARISH_COLOR if side is MarketSide.BEARISH else BULLISH_COLOR
        self.draw_line(
            start_timestamp, start_price, end_timestamp, end_price, color=color
        )

    def draw_horizontal_line(
        self,
        start_time: int,
        end_time: int,
        price: float,
        color: str = "#8b0072ff",
        width: int = 5,
    ) -> None:
        fplt.add_line(
            (start_time, price),
            (end_time, price),
            color=color,
            style="--",
            width=width,
            ax=self.ax,
        )

    def draw_filled_rect(
        self,
        start_time: int,
        end_time: int,
        upper_price: float,
        lower_price: float,
        color: str = "#8b007240",
    ) -> None:
        fplt.add_rect(
            (start_time, upper_price),
            (end_time, lower_price),
            color=color,
            interactive=False,
            ax=self.ax,
        )

    def mark_price(
        self, timestamp: int, price: float, side: MarketSide, legend: str | None = None
    ) -> None:
        bullish = side is MarketSide.BULLISH
        fplt.plot(
            timestamp,
            price,
            style="^" if bullish else "v",
            color=BULLISH_COLOR if bullish else BEARISH_COLOR,
            width=3,
            legend=legend,
            ax=self.ax,
        )

    def mark_candle(
        self,
        index: int,
        source: CandlesSource = CandlesSource.Open,
        legend: str | None = None,
        color: str | None = None,
    ) -> None:
        if self.chartdata is None:
            raise ValueError("This pane has no chartdata to mark a candle on")
        if color is None:
            color = (
                BEARISH_COLOR
                if source in (CandlesSource.Top, CandlesSource.High)
                else BULLISH_COLOR
            )
        values = source(self.chartdata)
        fplt.plot(
            int(self.chartdata.timestamps[index]),
            float(values[index]),
            style="o",
            color=color,
            width=1,
            legend=legend,
            ax=self.ax,
        )

    def draw_label(
        self,
        timestamp: int,
        price: float,
        text: str,
        color: str = "#000000",
        anchor: tuple[float, float] = (0.5, 0.5),
    ) -> None:
        fplt.add_text(
            (timestamp, price),
            text,
            color=color,
            anchor=anchor,
            ax=self.ax,
        )

    def mark_points(
        self,
        points: list[tuple[int, float]],
        legend: str | None = None,
        color: str = "#e1b400",
        width: int = 1,
    ) -> None:
        if not points:
            return
        x, y = zip(*points)
        fplt.plot(
            np.array(x),
            np.array(y, dtype=np.float64),
            style="o",
            color=color,
            width=width,
            legend=legend,
            ax=self.ax,
        )

    def linear_plot(
        self,
        x,
        y,
        legend: str | None = None,
        color: str = "#410087",
        thickness: int = 2,
    ) -> None:
        fplt.plot(
            x, y, style="-", ax=self.ax, color=color, legend=legend, width=thickness
        )


class ObjectPlotter(ABC):
    @abstractmethod
    def __call__(self, pane: ChartPane, *args, **kwargs) -> None: ...


class SignalPlotter(ObjectPlotter):
    def __call__(self, pane: ChartPane, signal: Signal) -> None:
        bullish = signal.side is MarketSide.BULLISH
        price = signal.candle.low * 0.9995 if bullish else signal.candle.high * 1.0005
        pane.mark_price(signal.candle.timestamp, price, signal.side)


class BaseChartFigure(ABC):
    def __init__(self, title: str, rows: int) -> None:
        axes = fplt.create_plot(title, rows=rows)
        self._axes = list(axes) if rows > 1 else [axes]
        self.panes: list[ChartPane] = []
        self._build()

    @abstractmethod
    def _build(self) -> None:
        """Populate self.panes and draw initial content."""

    @property
    def main_pane(self) -> ChartPane:
        return self.panes[0]

    @property
    def chartdata(self) -> ChartData:
        data = self.main_pane.chartdata
        if data is None:
            raise ValueError("Main pane has no chartdata")
        return data

    @staticmethod
    def _tail(chartdata: ChartData, n_candles: int) -> ChartData:
        """
        Last n_candles of chartdata, newest bar included. end_index has to
        be passed explicitly: subdata() defaults it to -1, which would drop
        the most recent candle -- the very one a signal fires on -- and only
        on the long-enough path, so charts would silently disagree about
        whether the newest bar is drawn.
        """
        if len(chartdata) <= n_candles:
            return chartdata
        return chartdata.subdata(
            start_index=len(chartdata) - n_candles,
            copy=True,
        )

    def show(self, blocking: bool = True) -> None:
        for pane in self.panes:
            pane.apply_y_range()
        fplt.show(qt_exec=blocking)

    def save_image(self, name: str | None = None, path: str = "Images/") -> str:
        for pane in self.panes:
            pane.apply_y_range()
        fplt.autoviewrestore(False)
        fplt.refresh()
        screenshot = self.main_pane.ax.vb.win.grab()
        name = name or str(self.chartdata.chart)

        # Qt writes nothing and raises nothing when the directory is
        # missing -- save() just returns False -- so create the folder
        # first and then insist the write actually happened. Reporters
        # build save_path from a strategy/bot name, so the folder usually
        # does not exist on the first run.
        directory = Path(path)
        directory.mkdir(parents=True, exist_ok=True)
        image_path = str(directory / f"{name}.png")
        if not screenshot.save(image_path):
            raise RuntimeError(f"Failed to write chart image to {image_path!r}")
        return image_path


class SingleChartFigure(BaseChartFigure):
    def __init__(self, chartdata: ChartData, plot_n_candles: int = 200) -> None:
        self._chartdata = chartdata
        self._plot_n_candles = plot_n_candles
        super().__init__(f"TimeFrame: {chartdata.chart.timeframe.value}", rows=1)

    def _build(self) -> None:
        data = self._tail(self._chartdata, self._plot_n_candles)
        pane = ChartPane(self._axes[0], data)
        pane.draw_candles(legend=str(data.chart))
        self.panes.append(pane)


class DoubleChartFigure(BaseChartFigure):
    def __init__(
        self,
        base_chartdata: ChartData,
        second_chartdata: ChartData,
        plot_n_candles: int = 100,
    ) -> None:
        self._base = base_chartdata
        self._second = second_chartdata
        self._plot_n_candles = plot_n_candles
        super().__init__(f"TimeFrame: {base_chartdata.chart.timeframe.value}", rows=2)

    def _build(self) -> None:
        for source, ax in ((self._base, self._axes[0]), (self._second, self._axes[1])):
            data = self._tail(source, self._plot_n_candles)
            pane = ChartPane(ax, data)
            pane.draw_candles(legend=str(data.chart))
            self.panes.append(pane)

    @property
    def second_pane(self) -> ChartPane:
        return self.panes[1]


class ChartWithOscillatorFigure(BaseChartFigure):
    def __init__(
        self,
        base_chartdata: ChartData,
        oscillator_values: np.ndarray,
        plot_n_candles: int = 100,
        label: str = "Oscillator",
        color: str = "#1F4BAB",
    ) -> None:
        self._base = base_chartdata
        self._oscillator_values = oscillator_values
        self._plot_n_candles = plot_n_candles
        self._label = label
        self._color = color
        super().__init__(f"TimeFrame: {base_chartdata.chart.timeframe.value}", rows=2)

    def _build(self) -> None:
        data = self._tail(self._base, self._plot_n_candles)
        main = ChartPane(self._axes[0], data)
        main.draw_candles(legend=str(data.chart))
        self.panes.append(main)

        # oscillator array is aligned with the full chartdata, so tail it identically
        tail_len = len(data)
        oscillator = self._oscillator_values[-tail_len:]

        osc_pane = ChartPane(self._axes[1])
        osc_pane.linear_plot(
            data.timestamps,
            oscillator,
            legend=self._label,
            color=self._color,
            thickness=1,
        )
        self.panes.append(osc_pane)

    @property
    def oscillator_pane(self) -> ChartPane:
        return self.panes[1]


Figure: TypeAlias = SingleChartFigure | DoubleChartFigure | ChartWithOscillatorFigure
