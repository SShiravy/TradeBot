from dataclasses import dataclass, field
from typing import Any, Callable, Iterator

from ChartModule.models import Candle, ChartData, MarketSide, CandlesSource
from ChartModule.Indicators.models import Indicator, SupportCandlesPattern
from ChartModule.plot import ChartPlot
import numpy as np


@dataclass(slots=True, frozen=True)
class Line:
    start_value: float
    end_value: float
    start_timestamp: int
    end_timestamp: int
    step: int  # number of values spanned between start and end, timeframe-agnostic

    @property
    def slope(self) -> float:
        return (self.end_value - self.start_value) / self.step

    def direction(self) -> MarketSide:
        if self.start_value > self.end_value:
            return MarketSide.BEARISH
        if self.start_value < self.end_value:
            return MarketSide.BULLISH
        return MarketSide.NEUTRAL

    def value_at(self, step_from_start: int) -> float:
        """Predicted value at a given number of steps past start_index, along the line."""
        return self.start_value + step_from_start * self.slope

    def plot(self, plot: "ChartPlot", chartdata: ChartData):
        start_index = chartdata.timestamp_index(self.start_timestamp)
        end_index = chartdata.timestamp_index(self.end_timestamp)
        plot.draw_chart_line(
            self.start_value,
            self.start_timestamp,
            self.end_value,
            self.end_timestamp,
            self.direction(),
        )


class LineFinder(Indicator):
    def __init__(
        self,
        source: CandlesSource,
        min_step: int,
        max_step: int,
        cross_check_source: CandlesSource | None = None,
        support_conditions: SupportCandlesPattern = SupportCandlesPattern.RAW,
    ) -> None:
        super().__init__()
        self.source = source
        self.cross_check_source = cross_check_source or source
        self.min_step = min_step
        self.max_step = max_step
        self.support_conditions = support_conditions

    def export_configs(self) -> dict:
        configs = super().export_configs()
        configs.update(
            {
                "source": self.source,
                "cross_check_source": self.cross_check_source,
                "min_step": self.min_step,
                "max_step": self.max_step,
                "support_conditions": self.support_conditions,
            }
        )
        return configs

    def _cross_multiplier(self) -> int:
        """
        Support-type lines (Low/Bottom) must stay at or below every value -> +1.
        Resistance-type lines (High/Top) must stay at or above every value -> -1.
        """
        if self.source in (CandlesSource.Low, CandlesSource.Bottom):
            return 1
        return -1

    @classmethod
    def iter_value_lines(
        cls,
        anchor_values: np.ndarray,
        timestamps: np.ndarray,
        end_index: int,
        min_step: int,
        max_step: int,
        cross_multiplier: int,
        check_values: np.ndarray | None = None,
        valid_step: Callable[[int], bool] | None = None,
    ) -> Iterator[Line]:
        if end_index < 0:
            end_index += len(anchor_values)

        check_values = anchor_values if check_values is None else check_values
        end_value = anchor_values[end_index]
        end_timestamp = int(timestamps[end_index])

        max_step = min(max_step, end_index)
        window_values = np.empty(max_step, dtype=np.float64)

        for step in range(1, max_step + 1):
            start_index = end_index - step
            window_values[step - 1] = check_values[start_index]

            if step < min_step:
                continue

            if valid_step is not None and not valid_step(start_index):
                continue

            start_value = anchor_values[start_index]
            slope = (end_value - start_value) / step

            offset_from_start = step - np.arange(1, step + 1, dtype=np.float64)
            predicted = start_value + offset_from_start * slope

            if np.any((window_values[:step] - predicted) * cross_multiplier < 0):
                continue

            yield Line(
                start_value=float(start_value),
                end_value=float(end_value),
                start_timestamp=int(timestamps[start_index]),
                end_timestamp=end_timestamp,
                step=step,
            )

    def iter_lines_at_index(
        self, chartdata: ChartData, end_index: int
    ) -> Iterator[Line]:
        if end_index < 0:
            end_index += len(chartdata)

        anchor_values = self.source(chartdata)
        check_values = self.cross_check_source(chartdata)

        valid_step = None
        if self.support_conditions is not SupportCandlesPattern.RAW:
            valid_step = lambda i: self.support_conditions.check(chartdata, i)

        yield from self.iter_value_lines(
            anchor_values=anchor_values,
            timestamps=chartdata.timestamps,
            end_index=end_index,
            min_step=self.min_step,
            max_step=self.max_step,
            cross_multiplier=self._cross_multiplier(),
            check_values=check_values,
            valid_step=valid_step,
        )

    def find_lines_at_index(self, chartdata: ChartData, end_index: int) -> list[Line]:
        return list(self.iter_lines_at_index(chartdata, end_index))

    def _calculate(self, chartdata: ChartData) -> list[Line]:
        return self.find_lines_at_index(chartdata, end_index=len(chartdata) - 1)

    def update(self, chartdata: ChartData, *args, **kwargs) -> Any:
        return self._calculate(chartdata)

    def forecast(self, *args, **kwargs) -> MarketSide:
        if not self.data:
            return MarketSide.NEUTRAL
        return self.data[-1].direction()

    def plot(self, plot: "ChartPlot", chartdata: ChartData):
        if not self.data:
            return
        self.data[-1].plot(plot, chartdata)
