from dataclasses import dataclass
from typing import Any, Callable, Iterator

from ChartModule.models import ChartData, MarketSide, CandlesSource
from ChartModule.Indicators.models import Indicator, SupportCandlesPattern
import numpy as np


@dataclass(slots=True, frozen=True)
class Line:
    start_value: float
    end_value: float
    start_timestamp: int
    end_timestamp: int
    step: int

    @property
    def slope(self) -> float:
        return (self.end_value - self.start_value) / self.step

    @property
    def direction(self) -> MarketSide:
        if self.start_value > self.end_value:
            return MarketSide.BEARISH
        if self.start_value < self.end_value:
            return MarketSide.BULLISH
        return MarketSide.NEUTRAL

    def value_at(self, step_from_start: int) -> float:
        return self.start_value + step_from_start * self.slope


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
        support-type lines (Low/Bottom) must stay at or below every value -> +1.
        resistance-type lines (High/Top) must stay at or above every value -> -1.
        """
        if self.source in (CandlesSource.Low, CandlesSource.Bottom):
            return 1
        return -1

    @classmethod
    def validate_value_line(
        cls,
        anchor_values: np.ndarray,
        timestamps: np.ndarray,
        start_timestamp: int,
        end_timestamp: int,
        cross_multiplier: int,
        check_values: np.ndarray | None = None,
        valid_step: Callable[[int], bool] | None = None,
    ) -> Line | None:
        start_idx = int(np.searchsorted(timestamps, start_timestamp))
        end_idx = int(np.searchsorted(timestamps, end_timestamp))

        if start_idx >= end_idx:
            raise ValueError("Start point came after End point!")

        check_values = anchor_values if check_values is None else check_values
        step = end_idx - start_idx + 1

        if valid_step is not None and not valid_step(start_idx):
            print("not valid")
            return None

        print(f"{start_idx=}|{end_idx}")
        start_value = anchor_values[start_idx]
        end_value = anchor_values[end_idx]
        slope = (end_value - start_value) / (step-1)

        offset_from_start = np.arange(0,step, dtype=np.float64)
        predicted = start_value + offset_from_start * slope
        window_values = check_values[start_idx : end_idx + 1]
        print(f'\n\n Second Chart line founded \n{step=} {start_value=} {end_value=}\n\n',"windo:\n",window_values,"\n\noffset:\n",offset_from_start,"\n\npredicted:\n",predicted,'\n\nres:\n',(window_values - predicted) * cross_multiplier)

        if np.any((window_values - predicted) * cross_multiplier < 0):
            return None

        return Line(
            start_value=float(start_value),
            end_value=float(end_value),
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            step=step,
        )

    def validate_line_at(
        self, chartdata: ChartData, start_timestamp: int, end_timestamp: int
    ) -> Line | None:
        anchor_values = self.source(chartdata)
        check_values = self.cross_check_source(chartdata)

        valid_step = None
        if self.support_conditions is not SupportCandlesPattern.RAW:
            valid_step = lambda i: self.support_conditions.check(chartdata, i)

        return self.validate_value_line(
            anchor_values=anchor_values,
            timestamps=chartdata.timestamps,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            cross_multiplier=self._cross_multiplier(),
            check_values=check_values,
            valid_step=valid_step,
        )

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
        window_values = np.zeros(max_step, dtype=np.float64)

        for step in range(1, max_step):
            start_index = end_index - step + 1
            window_values[-step] = check_values[start_index]

            if step < min_step:
                continue

            if valid_step is not None and not valid_step(start_index):
                continue

            start_value = anchor_values[start_index]
            slope = (end_value - start_value) / (step-1)

            offset_from_start = np.arange(0,step, dtype=np.float64)
            predicted = start_value + offset_from_start * slope
            if np.any((window_values[-step:] - predicted) * cross_multiplier < 0):
                continue
            print(f"The line {start_index=}|{end_index=}|{len(timestamps)}|{len(anchor_values)}")
            yield Line(
                start_value=float(start_value),
                end_value=float(end_value),
                start_timestamp=timestamps[start_index],
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

    def _calculate_new(self, chartdata: ChartData, start: int, *args, **kwargs) -> Any:
        pass

    def update(self, chartdata: ChartData, *args, **kwargs) -> Any:
        return self._calculate(chartdata)

    def forecast(self, *args, **kwargs) -> MarketSide:
        if not self.data:
            return MarketSide.NEUTRAL
        return self.data[-1].direction()
