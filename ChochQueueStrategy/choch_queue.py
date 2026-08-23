from ChartModule.models import (
    Chart,
    Signal,
    ChartData,
    MarketSide,
    Candle,
    CandlesSource,
)
from ChartModule.Indicators import IndicatorBaseModel, SupportCandleConditions
from ChartModule.plot import ChartPlot
from TradingModule.trader_bot import TradeConfig
from TradingModule.models import Position, Strategy
from datetime import datetime
from dataclasses import dataclass, field
import pandas as pd
import logging


logger = logging.getLogger("ChochQueue")


@dataclass(slots=True)
class ChochModel:
    side: MarketSide
    break_candle: Candle
    break_level: float
    pivot_candle: Candle
    anchor: float | None
    is_choch: bool

    extreme: float = field(init=False)
    active: bool = field(default=True, init=False)
    retrace_level: float | None = field(default=None, init=False)
    validated: bool = field(default=False, init=False)
    touch_candle: Candle | None = field(default=None, init=False)

    def __post_init__(self):
        self.extreme = float("-inf") if self.side is MarketSide.BULLISH else float("inf")

    def __str__(self) -> str:
        kind = "CHoCH" if self.is_choch else "BOS"
        return (
            f"{kind}|{self.side}|{self.break_candle.time}"
            f"|active={self.active}|validated={self.validated}"
        )


@dataclass(slots=True, frozen=True)
class ChochSignal(Signal):
    source: str = field(default="ChochQueue", init=False)
    choch_model: ChochModel


class ChochQueueFilter(Strategy):
    def __init__(
        self,
        pivot_length: int = 50,
        backstep: int = 2,
        retrace_fib: float = 0.5,
        use_fibo_filter: bool = True,
        use_bos: bool = True,
        max_queue: int = 30,
        confirmation_indicators: list[IndicatorBaseModel] = [],
        long_support_conditions=SupportCandleConditions.RAW,
        short_support_conditions=SupportCandleConditions.RAW,
        name="ChochQueue",
    ) -> None:
        """
        backstep: kept only for backward compatibility with existing configs;
        the Pine source has no such filter on pivots, so it is unused here.

        use_bos: BOS breaks are ALWAYS computed and pushed into the internal
                 queue/state exactly like the Pine script - they still flip
                 bias, set range_low/range_high, etc., since later CHoCH
                 detection depends on that state evolving correctly.
                 True  -> validated BOS entries are also surfaced as tradable
                          signals and drawn (matches the Pine script).
                 False -> validated BOS entries are skipped when picking a
                          signal in check_signal() and skipped in draw_all();
                          only CHoCH entries are ever surfaced/traded/drawn.
        """
        super().__init__(
            name,
            long_support_conditions,
            short_support_conditions,
            confirmation_indicators,
        )
        self.pivot_length = pivot_length
        self.backstep = backstep
        self.retrace_fib = retrace_fib
        self.use_fibo_filter = use_fibo_filter
        self.use_bos = use_bos
        self.max_queue = max_queue

        self.chart: Chart

        self.cur_group_type: MarketSide = MarketSide.NEUTRAL
        self.cur_group_count: int = 0
        self.queue: list[ChochModel] = []

        self.last_reported_time: datetime | None = None

    def export_config(self):
        conf_dict = super().export_config()
        conf_dict.update(
            {
                "pivot_length": self.pivot_length,
                "backstep": self.backstep,
                "retrace_fib": self.retrace_fib,
                "use_fibo_filter": self.use_fibo_filter,
                "use_bos": self.use_bos,
                "max_queue": self.max_queue,
            }
        )
        return conf_dict

    @staticmethod
    def _rolling_extreme_excl(values: list[float], length: int, find_max: bool) -> list[float]:
        """
        result[i] = max/min(values[i-length : i]) i.e. the extreme of the
        `length` values strictly BEFORE i, excluding i itself.
        NaN where the window isn't fully available.
        """
        series = pd.Series(values, dtype=float)
        rolled = (
            series.rolling(window=length, min_periods=length).max()
            if find_max
            else series.rolling(window=length, min_periods=length).min()
        )
        return rolled.shift(1).tolist()

    def _find_pivots(self, candles: list[Candle]) -> list[dict]:
        """
        Mirrors Pine's `ta.pivothigh(length, length)` / `ta.pivotlow(length, length)`:
        a candidate bar `p` is a pivot high if its high is strictly greater
        than the `length` highs to its left and greater-or-equal to the
        `length` highs to its right (mirrored for pivot low). Because the
        right side needs `length` future bars to exist, the pivot only
        becomes known/confirmed at bar `p + length` - exactly like Pine only
        returning a non-na value once those bars have printed. Each event
        therefore carries both the pivot's own bar (`pivot_index`, used as
        the level/anchor location - Pine's `ph_bar := n - length`) and the
        bar at which it becomes visible (`confirm_index`, when Pine's `if ph`
        block actually runs).
        """
        length = self.pivot_length
        n = len(candles)
        if n <= 2 * length:
            return []

        highs = [c.high for c in candles]
        lows = [c.low for c in candles]

        left_high = self._rolling_extreme_excl(highs, length, find_max=True)
        right_high = self._rolling_extreme_excl(highs[::-1], length, find_max=True)[::-1]
        left_low = self._rolling_extreme_excl(lows, length, find_max=False)
        right_low = self._rolling_extreme_excl(lows[::-1], length, find_max=False)[::-1]

        events = []
        for p in range(length, n - length):
            confirm_index = p + length
            if highs[p] > left_high[p] and highs[p] >= right_high[p]:
                events.append(
                    {
                        "pivot_index": p,
                        "confirm_index": confirm_index,
                        "price": highs[p],
                        "type": "high",
                    }
                )
            if lows[p] < left_low[p] and lows[p] <= right_low[p]:
                events.append(
                    {
                        "pivot_index": p,
                        "confirm_index": confirm_index,
                        "price": lows[p],
                        "type": "low",
                    }
                )
        events.sort(key=lambda e: e["confirm_index"])
        return events

    @staticmethod
    def _pine_extreme(values: list[float], start: int, end: int, find_min: bool) -> tuple[float, int]:
        """
        Mirrors Pine's:
            float lo = low  (or high)
            for off = 1 to rng
                if low[off] < lo   (strict)
                    lo := low[off]
        i.e. scans from `end` backward down to `start`, only replacing on a
        STRICT improvement. On ties this keeps the bar closer to `end` (the
        most recently found one), unlike `min()/list.index()` which would
        keep the oldest/leftmost bar.
        """
        best = values[end]
        best_index = end
        for idx in range(end - 1, start - 1, -1):
            v = values[idx]
            if (find_min and v < best) or (not find_min and v > best):
                best = v
                best_index = idx
        return best, best_index

    def _push_model(self, model: ChochModel):
        self.queue.append(model)
        if len(self.queue) > self.max_queue:
            self.queue.pop(0)

    def _deactivate_all(self, side: MarketSide):
        for model in self.queue:
            if model.side is side:
                model.active = False

    def _update_extremes(self, candle: Candle):
        for model in self.queue:
            if not model.active:
                continue
            if candle.timestamp <= model.break_candle.timestamp:
                continue
            if model.side is MarketSide.BULLISH:
                model.extreme = max(model.extreme, candle.high)
            else:
                model.extreme = min(model.extreme, candle.low)

    def _find_group_start(self) -> int:
        size = len(self.queue)
        if size == 0:
            return 0
        group_start = size - 1
        for i in range(size - 2, -1, -1):
            if self.queue[i].side is self.cur_group_type and self.queue[i].active:
                group_start = i
            elif self.queue[i].side is not self.cur_group_type:
                break
        return group_start

    def _validate_group(self, candle: Candle):
        if not self.queue or self.cur_group_type is MarketSide.NEUTRAL:
            return

        group_start = self._find_group_start()
        for model in self.queue[group_start:]:
            if not (model.active and model.side is self.cur_group_type):
                continue
            if model.anchor is None:
                continue

            # extreme may still be at its initial -inf/inf sentinel if this
            # model is being validated on its own break bar
            if model.side is MarketSide.BULLISH:
                leg_bot = model.anchor
                leg_top = candle.high if model.extreme == float("-inf") else model.extreme
            else:
                leg_top = model.anchor
                leg_bot = candle.low if model.extreme == float("inf") else model.extreme

            if self.use_fibo_filter:
                if model.side is MarketSide.BULLISH:
                    retrace_level = leg_bot + (leg_top - leg_bot) * (1 - self.retrace_fib)
                    is_validated = candle.low <= retrace_level
                else:
                    retrace_level = leg_top - (leg_top - leg_bot) * (1 - self.retrace_fib)
                    is_validated = candle.high >= retrace_level
            else:
                retrace_level = model.break_level
                is_validated = True

            model.retrace_level = retrace_level

            if not is_validated:
                continue

            model.validated = True
            model.touch_candle = candle
            self._deactivate_all(self.cur_group_type)

            new_type = (
                MarketSide.BEARISH
                if model.side is MarketSide.BULLISH
                else MarketSide.BULLISH
            )
            found_prev = False
            for previous_model in reversed(self.queue):
                if previous_model.side is new_type and previous_model.active:
                    self.cur_group_type = new_type
                    found_prev = True
                    break
            if not found_prev:
                self.cur_group_type = MarketSide.NEUTRAL
                self.cur_group_count = 0

            return

    def _simulate(self, candles: list[Candle]) -> list[ChochModel]:
        events = self._find_pivots(candles)
        events_by_index: dict[int, list[dict]] = {}
        for event in events:
            events_by_index.setdefault(event["confirm_index"], []).append(event)

        self.queue = []
        self.cur_group_type = MarketSide.NEUTRAL
        self.cur_group_count = 0

        last_ph_price: float | None = None
        last_ph_index: int | None = None
        ph_crossed = False
        last_pl_price: float | None = None
        last_pl_index: int | None = None
        pl_crossed = False
        bias: MarketSide = MarketSide.NEUTRAL

        range_low: float | None = None
        range_low_index: int | None = None
        range_high: float | None = None
        range_high_index: int | None = None

        highs = [c.high for c in candles]
        lows = [c.low for c in candles]

        for i, candle in enumerate(candles):
            for event in events_by_index.get(i, []):
                if event["type"] == "high":
                    last_ph_price = event["price"]
                    last_ph_index = event["pivot_index"]
                    ph_crossed = False
                else:
                    last_pl_price = event["price"]
                    last_pl_index = event["pivot_index"]
                    pl_crossed = False

            bull_choch = (
                bias is not MarketSide.BULLISH
                and range_high is not None
                and candle.high > range_high
            )
            bear_choch = (
                bias is not MarketSide.BEARISH
                and range_low is not None
                and candle.low < range_low
            )
            bull_bos = (
                bias is MarketSide.BULLISH
                and last_ph_price is not None
                and not ph_crossed
                and candle.close > last_ph_price
            )
            bear_bos = (
                bias is MarketSide.BEARISH
                and last_pl_price is not None
                and not pl_crossed
                and candle.close < last_pl_price
            )

            bull_signal = bull_choch or bull_bos
            bear_signal = bear_choch or bear_bos

            if bull_choch:
                bull_sig_level, bull_sig_index = range_high, range_high_index
            else:
                bull_sig_level, bull_sig_index = last_ph_price, last_ph_index
            if bear_choch:
                bear_sig_level, bear_sig_index = range_low, range_low_index
            else:
                bear_sig_level, bear_sig_index = last_pl_price, last_pl_index

            if bull_signal:
                ph_crossed = True
                bias = MarketSide.BULLISH
                start = bull_sig_index if bull_sig_index is not None else i
                range_low, range_low_index = self._pine_extreme(
                    lows, start, i, find_min=True
                )
                if bull_choch:
                    range_high, range_high_index = None, None

            if bear_signal:
                pl_crossed = True
                bias = MarketSide.BEARISH
                start = bear_sig_index if bear_sig_index is not None else i
                range_high, range_high_index = self._pine_extreme(
                    highs, start, i, find_min=False
                )
                if bear_choch:
                    range_low, range_low_index = None, None

            if bias is MarketSide.NEUTRAL:
                if range_low is None or candle.low < range_low:
                    range_low, range_low_index = candle.low, i
                if range_high is None or candle.high > range_high:
                    range_high, range_high_index = candle.high, i

            if bull_signal:
                if self.cur_group_type is MarketSide.BEARISH:
                    self._deactivate_all(MarketSide.BEARISH)
                    self.cur_group_count = 0
                if self.cur_group_type is not MarketSide.BULLISH:
                    self.cur_group_count = 0
                self.cur_group_type = MarketSide.BULLISH
                self.cur_group_count += 1
                self._push_model(
                    ChochModel(
                        side=MarketSide.BULLISH,
                        break_candle=candle,
                        break_level=bull_sig_level,  # type: ignore[arg-type]
                        pivot_candle=candles[bull_sig_index] if bull_sig_index is not None else candle,
                        anchor=last_pl_price,
                        is_choch=bull_choch,
                    )
                )

            if bear_signal:
                if self.cur_group_type is MarketSide.BULLISH:
                    self._deactivate_all(MarketSide.BULLISH)
                    self.cur_group_count = 0
                if self.cur_group_type is not MarketSide.BEARISH:
                    self.cur_group_count = 0
                self.cur_group_type = MarketSide.BEARISH
                self.cur_group_count += 1
                self._push_model(
                    ChochModel(
                        side=MarketSide.BEARISH,
                        break_candle=candle,
                        break_level=bear_sig_level,  # type: ignore[arg-type]
                        pivot_candle=candles[bear_sig_index] if bear_sig_index is not None else candle,
                        anchor=last_ph_price,
                        is_choch=bear_choch,
                    )
                )

            self._update_extremes(candle)
            self._validate_group(candle)

        return self.queue

    def check_signal(
        self,
        chartdata: ChartData,
        check_long: bool = True,
        check_short: bool = True,
        *args,
        **kwargs,
    ) -> ChochSignal | None:
        self.chart = chartdata.chart
        self._simulate(chartdata.candles)

        last_candle = chartdata.candles[-1]
        newest_validated: ChochModel | None = None
        for model in self.queue:
            if not model.validated or model.touch_candle is None:
                continue
            if not model.is_choch and not self.use_bos:
                # BOS is still fully computed/queued/validated above (it can
                # still flip bias, set ranges, etc. for later CHoCH detection)
                # - use_bos only decides whether it's ever surfaced as a
                # tradable signal.
                continue
            if model.touch_candle.time == last_candle.time:
                newest_validated = model
                break

        if newest_validated is None:
            return None
        if (
            self.last_reported_time is not None
            and newest_validated.touch_candle.time <= self.last_reported_time  # type: ignore[union-attr]
        ):
            return None

        self.last_reported_time = newest_validated.touch_candle.time  # type: ignore[union-attr]
        signal = ChochSignal(
            self.chart, newest_validated.touch_candle, newest_validated.side, newest_validated  # type: ignore[arg-type]
        )

        if signal.side is MarketSide.BULLISH and not check_long:
            return None
        if signal.side is MarketSide.BEARISH and not check_short:
            return None

        confirmations = self.get_indicators_confirmation(chartdata)
        if signal.side is MarketSide.BULLISH and MarketSide.BEARISH in confirmations:
            logger.debug(f"indicators rejected the signal: {signal}")
            return None
        if signal.side is MarketSide.BEARISH and MarketSide.BULLISH in confirmations:
            logger.debug(f"indicators rejected the signal: {signal}")
            return None

        logger.info(f"Signal: {signal} | {signal.choch_model}")
        return signal

    def report(self, *args, **kwargs) -> str:
        return ""

    def _draw_model(self, plot: ChartPlot, model: ChochModel):
        base = "26a69a" if model.side is MarketSide.BULLISH else "ef5350"
        color = f"#{base}" if model.is_choch else f"#{base}70"
        width = 2 if model.is_choch else 1

        plot.draw_line(
            model.pivot_candle.time,
            model.break_level,
            model.break_candle.time,
            model.break_level,
            color=color,
            width=width,
        )

        pivot_source = (
            CandlesSource.High if model.side is MarketSide.BULLISH else CandlesSource.Low
        )
        plot.mark_candle(model.pivot_candle, source=pivot_source, color=color)

        if self.use_fibo_filter and model.retrace_level is not None and model.touch_candle is not None:
            plot.draw_horizontal_line(
                model.break_candle.time,
                model.touch_candle.time,
                model.retrace_level,
                color=color,
            )
            plot.mark_price(model.touch_candle.time, model.retrace_level, model.side)

    def draw(
        self,
        plot: ChartPlot,
        signal: ChochSignal,
        draw_indicators: bool = True,
        *args,
        **kwargs,
    ):
        super().draw(plot, signal, draw_indicators)
        self._draw_model(plot, signal.choch_model)
        plot.mark_signal(signal)

    def draw_all(self, plot: ChartPlot):
        for model in self.queue:
            if not model.validated:
                continue
            if not model.is_choch and not self.use_bos:
                continue
            self._draw_model(plot, model)

    def generate_dummy_signal(
        self,
        base_chartdata: ChartData,
        side: MarketSide = MarketSide.BULLISH,
    ) -> ChochSignal:
        pivot_candle = base_chartdata.candles[-5]
        break_candle = base_chartdata.candles[-2]
        touch_candle = base_chartdata.candles[-1]
        source = CandlesSource.High if side is MarketSide.BEARISH else CandlesSource.Low
        dummy_model = ChochModel(
            side=side,
            break_candle=break_candle,
            break_level=source(pivot_candle),
            pivot_candle=pivot_candle,
            anchor=source(base_chartdata.candles[-8]),
            is_choch=True,
        )
        dummy_model.validated = True
        dummy_model.touch_candle = touch_candle
        dummy_model.retrace_level = source(touch_candle)
        return ChochSignal(base_chartdata.chart, touch_candle, side, dummy_model)


class ChochQueueTradeConfig(TradeConfig):
    strategy: ChochQueueFilter  # type: ignore[override]

    async def find_signal(
        self, chartdata: ChartData, *args, **kwargs
    ) -> None | tuple[ChochSignal, Position]:
        signal = self.strategy.check_signal(
            chartdata, self.long_signal, self.short_signal
        )
        if signal is None:
            return None

        plot = None
        if self.send_signal:
            plot = ChartPlot(chartdata)
            self.strategy.draw(plot, signal, draw_indicators=True)

        position = await self.position_handler.generate_position(
            signal, sl_base_price=signal.choch_model.anchor, plot=plot
        )
        if not position:
            return None
        return signal, position