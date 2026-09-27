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
    # slope/offset arithmetic in float64 leaves residues around 1e-15 relative,
    # which would otherwise read as a cross on a perfectly straight run.
    # Relative, so it scales across instruments (USDJPY ~150, BTCUSD ~60000);
    # the absolute floor only matters for sources that sit near zero.
    CROSS_RTOL: float = 1e-9
    CROSS_ATOL: float = 1e-12

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
    def _crosses(
        cls,
        window_values: np.ndarray,
        predicted: np.ndarray,
        cross_multiplier: int,
    ) -> bool:
        """
        Whether any value breaks through the line. A value sitting within
        tolerance of the line counts as touching it, not crossing it.
        """
        deviation = (window_values - predicted) * cross_multiplier
        tolerance = cls.CROSS_ATOL + cls.CROSS_RTOL * np.abs(predicted)
        return bool(np.any(deviation < -tolerance))

    @staticmethod
    def _exact_index(timestamps: np.ndarray, timestamp: int) -> int | None:
        """
        Index of `timestamp`, or None when this chart holds no candle at that
        exact time -- a missing bar, or a range reaching past its history.
        """
        idx = int(np.searchsorted(timestamps, timestamp))
        if idx >= timestamps.shape[0] or int(timestamps[idx]) != int(timestamp):
            return None
        return idx

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
        start_idx = cls._exact_index(timestamps, start_timestamp)
        end_idx = cls._exact_index(timestamps, end_timestamp)

        # the two charts are fetched separately, so one can lag or skip a bar
        if start_idx is None or end_idx is None:
            return None

        if start_idx >= end_idx:
            raise ValueError("Start point came after End point!")

        if end_idx >= anchor_values.shape[0]:
            # anchor_values must be one value per candle of `timestamps`;
            # an indicator series that drifted out of step with its chart
            # would otherwise be read at the wrong bar
            raise ValueError(
                f"anchor_values has {anchor_values.shape[0]} values for "
                f"{timestamps.shape[0]} timestamps -- they must align"
            )

        check_values = anchor_values if check_values is None else check_values
        step = end_idx - start_idx + 1

        if valid_step is not None and not valid_step(start_idx):
            return None

        start_value = anchor_values[start_idx]
        end_value = anchor_values[end_idx]

        # an indicator is undefined until it warms up (RSI/ATR leave NaN
        # there). NaN would sail through the cross check below, since every
        # comparison against NaN is False, and yield a NaN line.
        if np.isnan(start_value) or np.isnan(end_value):
            return None

        slope = (end_value - start_value) / (step - 1)

        offset_from_start = np.arange(0, step, dtype=np.float64)
        predicted = start_value + offset_from_start * slope
        window_values = check_values[start_idx : end_idx + 1]

        if np.isnan(window_values).any():
            return None

        if cls._crosses(window_values, predicted, cross_multiplier):
            return None

        return Line(
            start_value=float(start_value),
            end_value=float(end_value),
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            step=step,
        )

    def validate_line_at(
        self,
        chartdata: ChartData,
        start_timestamp: int,
        end_timestamp: int,
        timestamps: np.ndarray | None = None,
    ) -> Line | None:
        """
        Re-draw a line found on one chart onto ANOTHER chart, between the
        same two timestamps, and check that chart's own values never cross
        it. Used for the second leg of a divergence.

        `support_conditions` is deliberately NOT applied here. It describes
        the candle pattern that qualifies the SETUP, which lives on the base
        chart -- `iter_value_lines` already enforces it when anchoring the
        base line. Re-testing it against the other chart's candles adds an
        unrelated requirement and silently throws away valid divergences
        (it rejected most of them with a non-RAW pattern). The oscillator
        variant, which validates its second leg through
        `validate_value_line` directly, never applied it either.
        """
        anchor_values = self.source(chartdata)
        check_values = self.cross_check_source(chartdata)

        timestamps = timestamps if timestamps is not None else chartdata.timestamps
        return self.validate_value_line(
            anchor_values=anchor_values,
            timestamps=timestamps,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            cross_multiplier=self._cross_multiplier(),
            check_values=check_values,
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

            if step <= min_step:
                continue

            if valid_step is not None and not valid_step(start_index):
                continue

            start_value = anchor_values[start_index]
            slope = (end_value - start_value) / (step - 1)

            offset_from_start = np.arange(0, step, dtype=np.float64)
            predicted = start_value + offset_from_start * slope
            if cls._crosses(window_values[-step:], predicted, cross_multiplier):
                continue
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
