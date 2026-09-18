from ChartModule.models import (
    ChartData,
    MarketSide,
    CandlesSource,
)
from ChartModule.Indicators.models import (
    Indicator,
    IndicatorPlotter,
    SupportCandlesPattern,
)
import numpy as np

from ChartModule.plot import ChartPane


class PivotPlotter(IndicatorPlotter):
    def __call__(
        self,
        pane: ChartPane,
        indicator_data: np.ndarray,
        show_all=True,
        source: CandlesSource = CandlesSource.Close,
    ) -> None:
        if indicator_data is None or len(indicator_data) == 0:
            return

        indices = indicator_data if show_all else indicator_data[-1:]
        for idx in indices:
            pane.mark_candle(int(idx), source=source, color="#e1b400")


class Pivot(Indicator):
    """
    Indices of pivot candles (local extrema over a left/right window).
    self.data: np.ndarray of int64 indices into chartdata, sorted ascending.
    down_pivot=True finds swing lows, False finds swing highs.
    """

    def __init__(
        self,
        source: CandlesSource,
        left: int = 3,
        right: int = 3,
        down_pivot: bool = True,
        support_conditions: SupportCandlesPattern = SupportCandlesPattern.RAW,
    ) -> None:
        super().__init__()
        self.source = source
        self.left = left
        self.right = right
        self.down_pivot = down_pivot
        self.support_conditions = support_conditions
        self.plotter = PivotPlotter()
        self._last_pivot_index: int = -(10**9)  # sentinel: "no pivot found yet"

    def export_configs(self) -> dict:
        configs = super().export_configs()
        configs.update(
            {
                "source": self.source.name,
                "left": self.left,
                "right": self.right,
                "down_pivot": self.down_pivot,
            }
        )
        return configs

    def _find_pivots(
        self, chartdata: ChartData, values: np.ndarray, scan_start: int, scan_stop: int
    ) -> list[int]:
        """
        Find pivot indices with candidate positions in [scan_start, scan_stop),
        each needing `left` bars before and `right` bars after within the
        full array (not just the scanned slice) to compare against.
        """
        window = self.left + self.right + 1
        n = len(values)
        pivots: list[int] = []

        lo = max(self.left, scan_start)
        hi = min(n - self.right, scan_stop)
        if hi <= lo:
            return pivots

        windows = np.lib.stride_tricks.sliding_window_view(values, window)
        extreme = windows.min(axis=1) if self.down_pivot else windows.max(axis=1)
        # windows[i] spans values[i : i+window]; its center is index i+left
        center_start = 0
        centers = np.arange(center_start, center_start + len(extreme)) + self.left
        is_extreme = np.isclose(values[centers], extreme)

        candidate_mask = is_extreme & (centers >= lo) & (centers < hi)
        candidates = centers[candidate_mask]

        for idx in candidates:
            idx = int(idx)
            if idx - self._last_pivot_index <= self.left:
                continue
            if (
                self.support_conditions is not SupportCandlesPattern.RAW
                and not self.support_conditions.check(chartdata, idx)
            ):
                continue
            pivots.append(idx)
            self._last_pivot_index = idx

        return pivots

    def _calculate(self, chartdata: ChartData, *args, **kwargs) -> np.ndarray:
        values = self.source(chartdata)
        self._last_pivot_index = -(10**9)
        pivots = self._find_pivots(
            chartdata, values, scan_start=0, scan_stop=len(values)
        )
        return np.array(pivots, dtype=np.int64)

    def _calculate_new(
        self, chartdata: ChartData, start: int, *args, **kwargs
    ) -> np.ndarray:
        values = self.source(chartdata)
        # candidates near `start` need `left` bars of prior context to be
        # scannable at all; anything before that was already resolved
        scan_start = max(0, start - self.left)
        pivots = self._find_pivots(
            chartdata, values, scan_start=scan_start, scan_stop=len(values)
        )
        return np.array(pivots, dtype=np.int64)

    def _merge(self, new_segment: np.ndarray) -> np.ndarray:
        return np.concatenate([self.data, new_segment])

    def check_candle_is_pivot(self, index: int, chartdata: ChartData) -> bool:
        self.set(chartdata)
        return index in self.data

    def forecast(self, *args, **kwargs) -> MarketSide:
        return MarketSide.NEUTRAL

    @property
    def major_pivot_index(self) -> int | None:
        """Index of the most extreme pivot found so far (highest high or lowest low)."""
        if self.data is None or len(self.data) == 0 or self.chartdata is None:
            return None
        values = self.source(self.chartdata)
        pivot_values = values[self.data]
        best = pivot_values.argmin() if self.down_pivot else pivot_values.argmax()
        return int(self.data[best])
