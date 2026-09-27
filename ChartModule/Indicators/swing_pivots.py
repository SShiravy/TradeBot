from ChartModule.models import Candle, ChartData, CandlesSource
from ChartModule.Indicators.models import Indicator, IndicatorPlotter, IndicatorRule
from ChartModule.plot import ChartPane
from dataclasses import dataclass, replace


@dataclass(slots=True, frozen=True)
class PivotPoint:
    index: int
    candle: Candle
    price: float
    is_high: bool
    confirmed_index: int
    confirmed: bool = True

    def __str__(self) -> str:
        side = "High" if self.is_high else "Low"
        tag = "" if self.confirmed else "*"
        return f"Pivot{side}{tag}|{self.candle.timestamp}|{self.price}"


class SwingPivotsPlotter(IndicatorPlotter):
    def __call__(
        self,
        pane: ChartPane,
        indicator_data: list[PivotPoint],
        show_live: bool = True,
        live_pivots: list[PivotPoint] | None = None,
        color: str = "#e1b400",
        live_color: str = "#8a8a8a",
    ) -> None:
        if not indicator_data:
            return

        for pivot in indicator_data:
            pane.mark_candle(
                pivot.index,
                source=CandlesSource.High if pivot.is_high else CandlesSource.Low,
                color=color,
            )

        if show_live and live_pivots:
            for pivot in live_pivots:
                pane.mark_candle(
                    pivot.index,
                    source=CandlesSource.High if pivot.is_high else CandlesSource.Low,
                    color=live_color,
                )


class SwingPivots(Indicator):
    """
    Causal, repainting swing pivot detector (Depth / Backstep).

    self.data: list[PivotPoint]        (confirmed pivots only)
    live_pivots: list[PivotPoint]      (0-2 currently running, unconfirmed)

    The scan carries running state between calls, so an incremental update
    resumes from the last seen candle instead of rescanning from bar 0.
    Backstep is re-applied over the whole cumulative raw-pivot history on
    every update, so `self.data` is always the ENTIRE confirmed list rebuilt
    from scratch -- never "just the new pivots". A late pivot can replace an
    earlier one, which is exactly why the raw history has to be kept.

    Indices are positions into the chartdata passed in. When that chartdata
    is a sliding window, indices recorded on an earlier call go stale by
    however many candles fell off the front, so every incremental update
    rebases the whole running state first -- see `_rebase`.
    """

    def __init__(
        self,
        depth: int = 12,
        backstep: int = 2,
        rules: list[IndicatorRule] = [],
    ) -> None:
        super().__init__(rules=rules)
        self.data: list[PivotPoint]
        self.live_pivots: list[PivotPoint] = []
        self.depth = depth
        self.backstep = backstep
        self.plotter = SwingPivotsPlotter()

        self._raw_pivots: list[PivotPoint] = []
        # scan state, carried between _calculate() and every _calculate_new()
        self._direction = 0  # 0 = tracking both, 1 = tracking a high, -1 = a low
        self._high_idx = self._high_last_update = 0
        self._high_price = 0.0
        self._low_idx = self._low_last_update = 0
        self._low_price = 0.0
        # where the last-seen candle sat in the window last time, so an
        # update can measure how far the window has slid and rebase.
        self._last_checked_index = 0

    def export_configs(self) -> dict:
        configs = super().export_configs()
        configs.update({"depth": self.depth, "backstep": self.backstep})
        return configs

    def _apply_backstep(
        self, pivots: list[PivotPoint], is_high: bool
    ) -> list[PivotPoint]:
        if self.backstep <= 0 or not pivots:
            return pivots

        factor = 1 if is_high else -1
        result: list[PivotPoint] = []
        for pivot in pivots:
            if result and pivot.index - result[-1].index < self.backstep:
                if (pivot.price - result[-1].price) * factor > 0:
                    result[-1] = pivot
                # else: new pivot is weaker -> discard it
            else:
                result.append(pivot)
        return result

    def _confirmed_from_raw(self) -> list[PivotPoint]:
        highs = self._apply_backstep([p for p in self._raw_pivots if p.is_high], True)
        lows = self._apply_backstep(
            [p for p in self._raw_pivots if not p.is_high], False
        )
        return sorted(highs + lows, key=lambda pivot: pivot.confirmed_index)

    def _rebase(self, shift: int) -> bool:
        """
        The window slid forward by `shift` bars. Move every recorded
        position back by the same amount so it still points at the same
        real candle, and drop the raw pivots that fell off the front.

        Returns False when the running extremes themselves scrolled out of
        the window -- their true price can no longer be reconstructed from
        what is left, so the caller must recompute from scratch instead.

        Without this the scan state stays pinned to the coordinates of
        whatever window it last saw: `i - self._low_last_update` is 0 on
        every subsequent bar, the depth test can never fire again, and the
        indicator silently freezes on its first result forever.
        """
        if self._low_idx - shift < 0 or self._high_idx - shift < 0:
            return False

        self._low_idx -= shift
        self._high_idx -= shift
        self._low_last_update = max(self._low_last_update - shift, 0)
        self._high_last_update = max(self._high_last_update - shift, 0)

        self._raw_pivots = [
            replace(p, index=p.index - shift, confirmed_index=p.confirmed_index - shift)
            for p in self._raw_pivots
            if p.index - shift >= 0
        ]
        return True

    def _scan(self, chartdata: ChartData, start: int, stop: int) -> list[PivotPoint]:
        """
        Walk bars [start, stop) forward from the current running state,
        appending every raw (pre-backstep) pivot it confirms.
        """
        highs = chartdata.high
        lows = chartdata.low
        found: list[PivotPoint] = []

        for i in range(start, stop):
            if self._direction <= 0:
                if lows[i] < self._low_price:
                    self._low_price = float(lows[i])
                    self._low_idx = i
                    self._low_last_update = i
                if i - self._low_last_update >= self.depth:
                    found.append(
                        PivotPoint(
                            self._low_idx,
                            chartdata.candle(self._low_idx),
                            self._low_price,
                            False,
                            i,
                            True,
                        )
                    )
                    self._direction = 1
                    self._high_price = float(highs[i])
                    self._high_idx = i
                    self._high_last_update = i

            if self._direction >= 0:
                if highs[i] > self._high_price:
                    self._high_price = float(highs[i])
                    self._high_idx = i
                    self._high_last_update = i
                if i - self._high_last_update >= self.depth:
                    found.append(
                        PivotPoint(
                            self._high_idx,
                            chartdata.candle(self._high_idx),
                            self._high_price,
                            True,
                            i,
                            True,
                        )
                    )
                    self._direction = -1
                    self._low_price = float(lows[i])
                    self._low_idx = i
                    self._low_last_update = i

        self._raw_pivots.extend(found)
        return found

    def _refresh_live_pivots(self, chartdata: ChartData) -> None:
        """The 0-2 extremes still being tracked, not yet confirmed by depth."""
        self.live_pivots = []
        last_index = len(chartdata) - 1
        if last_index < 0:
            return

        if self._direction <= 0:
            self.live_pivots.append(
                PivotPoint(
                    self._low_idx,
                    chartdata.candle(self._low_idx),
                    self._low_price,
                    False,
                    last_index,
                    False,
                )
            )
        if self._direction >= 0:
            self.live_pivots.append(
                PivotPoint(
                    self._high_idx,
                    chartdata.candle(self._high_idx),
                    self._high_price,
                    True,
                    last_index,
                    False,
                )
            )

    def _calculate(self, chartdata: ChartData, *args, **kwargs) -> list[PivotPoint]:
        self._raw_pivots = []
        self.live_pivots = []
        self._direction = 0
        self._high_idx = self._high_last_update = 0
        self._low_idx = self._low_last_update = 0

        if len(chartdata) == 0:
            return []

        # seed before the length check: a later incremental call resumes from
        # this state, and leaving the prices at 0.0 would make every real low
        # look like a new high and emit a pivot priced at zero.
        self._high_price = float(chartdata.high[0])
        self._low_price = float(chartdata.low[0])

        if len(chartdata) < 2:
            return []

        self._scan(chartdata, 1, len(chartdata))
        self._refresh_live_pivots(chartdata)
        self._last_checked_index = len(chartdata) - 1
        return self._confirmed_from_raw()

    def _calculate_new(
        self, chartdata: ChartData, start: int, *args, **kwargs
    ) -> list[PivotPoint]:
        # position of the last-seen candle in the NEW window vs where it was
        # recorded last time -> how far the window has slid forward. Rebase
        # before scanning: every index below is in the new window's frame.
        shift = self._last_checked_index - (start - 1)
        if shift > 0 and not self._rebase(shift):
            return self._calculate(chartdata, *args, **kwargs)

        new_pivots = self._scan(chartdata, start, len(chartdata))
        self._refresh_live_pivots(chartdata)
        self._last_checked_index = len(chartdata) - 1
        return new_pivots

    def _merge(self, new_segment: list[PivotPoint]) -> list[PivotPoint]:
        # backstep can retroactively replace an already-emitted pivot, so the
        # confirmed list is rebuilt from the full raw history rather than
        # appended to -- `new_segment` is already inside `_raw_pivots`.
        return self._confirmed_from_raw()
