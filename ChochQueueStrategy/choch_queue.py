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
import logging


logger = logging.getLogger("ChochQueue")


@dataclass(slots=True)
class ChochModel:
    """
    one CHoCH break under investigation (a single item of the pine-script queue arrays)

    side          : BULLISH -> c_type=1 | BEARISH -> c_type=-1
    break_candle  : candle where the pivot got broken (c_bar)
    break_level   : the pivot price that got broken (c_level)
    pivot_candle  : the pivot candle that got broken (c_pivot_bar)
    anchor        : fixed leg point, the opposite pivot price right before the break (c_anchor)
                    for BULLISH  = کف pivot قبلی (ثابت = کف لگ)
                    for BEARISH  = سقف pivot قبلی (ثابت = سقف لگ)
    extreme       : running max/min of the leg since the break bar (c_extreme)
                    for BULLISH  = running max high (آپدیت میشه = سقف لگ)
                    for BEARISH  = running min low  (آپدیت میشه = کف لگ)
    touch_candle  : the candle that confirmed/validated this CHoCH (retracement
                    touch when the fibo filter is on, same as break_candle when it's off)
    """

    side: MarketSide
    break_candle: Candle
    break_level: float
    pivot_candle: Candle
    anchor: float | None

    extreme: float = field(init=False)
    active: bool = field(default=True, init=False)
    retrace_level: float | None = field(default=None, init=False)
    validated: bool = field(default=False, init=False)
    touch_candle: Candle | None = field(default=None, init=False)

    def __post_init__(self):
        self.extreme = float("-inf") if self.side is MarketSide.BULLISH else float("inf")

    def __str__(self) -> str:
        return (
            f"{self.side}|{self.break_candle.time}"
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
        retrace_fib: float = 0.5,
        use_wick: bool = True,
        use_fibo_filter: bool = True,
        max_queue: int = 30,
        confirmation_indicators: list[IndicatorBaseModel] = [],
        long_support_conditions=SupportCandleConditions.RAW,
        short_support_conditions=SupportCandleConditions.RAW,
        name="ChochQueue",
    ) -> None:
        super().__init__(
            name,
            long_support_conditions,
            short_support_conditions,
            confirmation_indicators,
        )
        self.pivot_length = pivot_length
        self.retrace_fib = retrace_fib
        self.use_wick = use_wick
        self.use_fibo_filter = use_fibo_filter
        self.max_queue = max_queue

        self.chart: Chart

        self.cur_group_type: MarketSide = MarketSide.NEUTRAL
        self.queue: list[ChochModel] = []

        # only used to avoid re-firing the same signal on every call
        self.last_reported_time: datetime | None = None

    def export_config(self):
        conf_dict = super().export_config()
        conf_dict.update(
            {
                "pivot_length": self.pivot_length,
                "retrace_fib": self.retrace_fib,
                "use_wick": self.use_wick,
                "use_fibo_filter": self.use_fibo_filter,
                "max_queue": self.max_queue,
            }
        )
        return conf_dict

    # ─── PIVOT DETECTION ─────────────────────────────────

    def _find_pivots_and_missed(self, candles: list[Candle]) -> list[dict]:

        n = len(candles)
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]

        effective_length = self.pivot_length
        if n <= 2 * self.pivot_length:
            effective_length = 0

        pivot_highs_raw: list[tuple[int, float]] = []
        pivot_lows_raw: list[tuple[int, float]] = []

        if effective_length > 0:
            for i in range(effective_length, n - effective_length):
                if highs[i] == max(highs[i - effective_length : i + effective_length + 1]):
                    pivot_highs_raw.append((i, highs[i]))
                if lows[i] == min(lows[i - effective_length : i + effective_length + 1]):
                    pivot_lows_raw.append((i, lows[i]))

        all_pivots_sorted = sorted(
            [{"index": i, "price": p, "type": "high"} for i, p in pivot_highs_raw]
            + [{"index": i, "price": p, "type": "low"} for i, p in pivot_lows_raw],
            key=lambda x: x["index"],
        )

        missed_levels: list[dict] = []
        last_pivot = None
        for current in all_pivots_sorted:
            if last_pivot and last_pivot["type"] == current["type"]:
                start_idx = min(last_pivot["index"], current["index"])
                end_idx = max(last_pivot["index"], current["index"])
                if start_idx + 1 < end_idx:
                    if current["type"] == "high":
                        window = lows[start_idx + 1 : end_idx]
                        missed_price = min(window)
                        missed_index = start_idx + 1 + window.index(missed_price)
                        missed_levels.append(
                            {"index": missed_index, "price": missed_price, "type": "low"}
                        )
                    else:
                        window = highs[start_idx + 1 : end_idx]
                        missed_price = max(window)
                        missed_index = start_idx + 1 + window.index(missed_price)
                        missed_levels.append(
                            {"index": missed_index, "price": missed_price, "type": "high"}
                        )
            last_pivot = current

        if last_pivot and last_pivot["index"] < n - 1:
            start_idx = last_pivot["index"]
            if last_pivot["type"] == "high":
                window = lows[start_idx + 1 :]
                if window:
                    missed_price = min(window)
                    missed_index = start_idx + 1 + window.index(missed_price)
                    missed_levels.append(
                        {"index": missed_index, "price": missed_price, "type": "low"}
                    )
            else:
                window = highs[start_idx + 1 :]
                if window:
                    missed_price = max(window)
                    missed_index = start_idx + 1 + window.index(missed_price)
                    missed_levels.append(
                        {"index": missed_index, "price": missed_price, "type": "high"}
                    )

        return sorted(all_pivots_sorted + missed_levels, key=lambda x: x["index"])

    # ─── QUEUE MANAGEMENT ───────────────────────────────────────────────

    def _push_model(self, model: ChochModel):
        self.queue.append(model)
        if len(self.queue) > self.max_queue:
            self.queue.pop(0)

    def _deactivate_all(self, side: MarketSide):
        for model in self.queue:
            if model.side is side:
                model.active = False

    def _deactivate_from(self, start_index: int, side: MarketSide):
        for model in self.queue[start_index:]:
            if model.side is side:
                model.active = False

    # ─── EXTREME UPDATE & VALIDATION ────────────────────────────────────

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

        break_high = candle.high if self.use_wick else max(candle.open, candle.close)
        break_low = candle.low if self.use_wick else min(candle.open, candle.close)

        group_start = self._find_group_start()
        for model in self.queue[group_start:]:
            if not (model.active and model.side is self.cur_group_type):
                continue
            if model.anchor is None:
                continue

            if model.side is MarketSide.BULLISH:
                leg_bot, leg_top = model.anchor, model.extreme
            else:
                leg_top, leg_bot = model.anchor, model.extreme

            if self.use_fibo_filter:
                if model.side is MarketSide.BULLISH:
                    retrace_level = leg_bot + (leg_top - leg_bot) * (1 - self.retrace_fib)
                    is_validated = break_low <= retrace_level
                else:
                    retrace_level = leg_top - (leg_top - leg_bot) * (1 - self.retrace_fib)
                    is_validated = break_high >= retrace_level
            else:
                # fibonacci filter is off -> the CHoCH break itself confirms the signal
                retrace_level = model.break_level
                is_validated = True

            model.retrace_level = retrace_level

            if not is_validated:
                continue

            model.validated = True
            model.touch_candle = candle
            self._deactivate_from(group_start, self.cur_group_type)

            new_type = (
                MarketSide.BEARISH
                if model.side is MarketSide.BULLISH
                else MarketSide.BULLISH
            )
            self.cur_group_type = MarketSide.NEUTRAL
            for previous_model in reversed(self.queue):
                if previous_model.side is new_type and previous_model.active:
                    self.cur_group_type = new_type
                    break

            return  # only one validation per bar, mirrors pine's validated_this_bar

    # ─── MAIN SIMULATION ─────────────────────────────────────────────────

    def _simulate(self, candles: list[Candle]) -> list[ChochModel]:
        events = self._find_pivots_and_missed(candles)
        events_by_index: dict[int, list[dict]] = {}
        for event in events:
            events_by_index.setdefault(event["index"], []).append(event)

        self.queue = []
        self.cur_group_type = MarketSide.NEUTRAL
        last_ph_price: float | None = None
        last_ph_candle: Candle | None = None
        last_pl_price: float | None = None
        last_pl_candle: Candle | None = None
        os_state = 0  # 0 -> last pivot was a low | 1 -> last pivot was a high

        for i, candle in enumerate(candles):
            for event in events_by_index.get(i, []):
                if event["type"] == "high":
                    last_ph_price = event["price"]
                    last_ph_candle = candle
                    os_state = 1
                else:
                    last_pl_price = event["price"]
                    last_pl_candle = candle
                    os_state = 0

            break_high = candle.high if self.use_wick else max(candle.open, candle.close)
            break_low = candle.low if self.use_wick else min(candle.open, candle.close)

            choch_bull_raw = (
                os_state == 0 and last_ph_price is not None and break_high > last_ph_price
            )
            choch_bear_raw = (
                os_state == 1 and last_pl_price is not None and break_low < last_pl_price
            )

            if choch_bull_raw:
                if self.cur_group_type is MarketSide.BEARISH:
                    self._deactivate_all(MarketSide.BEARISH)
                self.cur_group_type = MarketSide.BULLISH
                self._push_model(
                    ChochModel(
                        side=MarketSide.BULLISH,
                        break_candle=candle,
                        break_level=last_ph_price,  # type: ignore[arg-type]
                        pivot_candle=last_ph_candle,  # type: ignore[arg-type]
                        anchor=last_pl_price,
                    )
                )
                last_ph_price = None
                os_state = 1

            if choch_bear_raw:
                if self.cur_group_type is MarketSide.BULLISH:
                    self._deactivate_all(MarketSide.BULLISH)
                self.cur_group_type = MarketSide.BEARISH
                self._push_model(
                    ChochModel(
                        side=MarketSide.BEARISH,
                        break_candle=candle,
                        break_level=last_pl_price,  # type: ignore[arg-type]
                        pivot_candle=last_pl_candle,  # type: ignore[arg-type]
                        anchor=last_ph_price,
                    )
                )
                last_pl_price = None
                os_state = 0

            self._update_extremes(candle)
            self._validate_group(candle)

        return self.queue

    # ─── MAIN SIGNAL FLOW ───────────────────────────────────────────────

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

        newest_validated: ChochModel | None = None
        for model in self.queue:
            if not model.validated or model.touch_candle is None:
                continue
            if newest_validated is None or model.touch_candle.time > newest_validated.touch_candle.time:  # type: ignore[union-attr]
                newest_validated = model

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

        logger.info(f"Signal:{signal}")
        return signal

    def report(self, *args, **kwargs) -> str:
        return ""

    # ─── DRAWING ────────────────────────────────────────────────────────

    def _draw_model(self, plot: ChartPlot, model: ChochModel):
        color = "#26a69a" if model.side is MarketSide.BULLISH else "#ef5350"

        # the CHoCH break line is always drawn, with or without the fibo filter
        plot.draw_line(
            model.pivot_candle.time,
            model.break_level,
            model.break_candle.time,
            model.break_level,
            color=color,
            width=2,
        )

        # the retracement line + touch arrow are only meaningful when the
        # fibo filter is on (otherwise the break itself is the signal)
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
            if model.validated:
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
