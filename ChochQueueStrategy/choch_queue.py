from ChartModule.models import (
    Chart,
    Signal,
    ChartData,
    MarketSide,
    Candle,
    CandlesSource,
)
from ChartModule.Indicators import IndicatorBaseModel, SupportCandleConditions
from ChartModule.Indicators.swing_pivots import SwingPivots, PivotPoint
from ChartModule.plot import ChartPlot
from TradingModule.trader_bot import TradeConfig
from TradingModule.models import Position, Strategy
from datetime import datetime
from dataclasses import dataclass, field
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
        plot_pivots: bool = False,
        min_choch_candles: int = 3,
        choch_mode: int = 2,
        name="ChochQueue",
    ) -> None:
        """
        choch_mode: which CHoCH detection engine to use.
                 1 -> the ORIGINAL logic: a CHoCH is just a touch of the
                      range_high/range_low level that was set up by the
                      last opposite-side signal (BOS or CHoCH) - i.e. the
                      swing high/low that led to the last move on the
                      other side. This is computed as part of the same
                      bias/range engine BOS already uses below, and was
                      the only CHoCH logic before this class had a
                      separate, independent CHoCH engine.
                 2 -> (default) the independent, candle-color-cluster-based
                      engine described below (min_choch_candles,
                      structural validity, unbounded fallback chain, etc.)
                      - completely decoupled from BOS/pivots.

        backstep: enforces alternation between pivot highs/lows. Raw pivot
        candidates from _find_pivots() (Pine-style pivothigh/pivotlow,
        meaningful even at pivot_length=1 since its window excludes the
        current bar) are reduced via _reduce_to_zigzag() before being used
        by the simulation:
          - among consecutive candidates of the SAME type, only the most
            extreme one survives (a higher high replaces a lower prior
            high, a lower low replaces a higher prior low) - this is what
            "extends" a leg instead of creating a same-type pivot with
            nothing opposite in between.
          - a candidate of the OPPOSITE type is only confirmed as the next
            zigzag point if it is at least `backstep` bars (by
            pivot_index) away from the last confirmed point; closer
            reversals are treated as noise and dropped.
        This is NOT an exact port of DevLucem's ZigLib (whose Depth+Backstep
        formula degenerates at depth=1 - see chat history) but gives the
        same practical guarantee (no same-type pivots back-to-back) while
        staying meaningful at pivot_length=1. NOTE: this bias/pivot engine
        now ONLY drives BOS detection - see _find_flip_candle_chochs for
        the independent CHoCH detection.

        use_bos: BOS breaks are ALWAYS computed and pushed into the internal
                 queue/state exactly like the Pine script - they still flip
                 bias, set range_low/range_high, etc., since later CHoCH
                 detection depends on that state evolving correctly.
                 True  -> validated BOS entries are also surfaced as tradable
                          signals and drawn (matches the Pine script).
                 False -> validated BOS entries are skipped when picking a
                          signal in check_signal() and skipped in draw_all();
                          only CHoCH entries are ever surfaced/traded/drawn.
                 (CHoCH itself no longer has an is_choch flag coming out of
                 this engine - see _find_flip_candle_chochs.)

        plot_pivots: purely visual - when True, draw_all() also marks every
                 raw pivot high/low found by _find_pivots() (regardless of
                 whether it ever became a CHoCH/BOS model). Useful for
                 sanity-checking pivot_length visually. Has no effect on
                 detection/filtering logic.

        min_choch_candles: minimum number of candles required between a
                 CHoCH's reference flip candle and the candle that touches
                 it (see _find_flip_candle_chochs). A touch happening only
                 1-2 candles after the flip candle is rejected as noise -
                 the flip candle's opposite-color run needs some room to
                 breathe before a touch counts as a real reversal.
        """
        super().__init__(
            name,
            long_support_conditions,
            short_support_conditions,
            confirmation_indicators,
        )
        self.pivot_length = pivot_length
        self.backstep = backstep
        self.pivots = SwingPivots(depth=pivot_length, backstep=backstep)
        self.retrace_fib = retrace_fib
        self.use_fibo_filter = use_fibo_filter
        self.use_bos = use_bos
        self.max_queue = max_queue
        self.plot_pivots = plot_pivots
        self.min_choch_candles = min_choch_candles
        if choch_mode not in (1, 2):
            raise ValueError(f"choch_mode must be 1 or 2, got {choch_mode!r}")
        self.choch_mode = choch_mode
        self._pivot_events: list[dict] = []

        self.chart: Chart

        self.cur_group_type: MarketSide = MarketSide.NEUTRAL
        self.cur_group_count: int = 0
        self.queue: list[ChochModel] = []
        self.choch_events: list[ChochModel] = []

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
                "plot_pivots": self.plot_pivots,
                "min_choch_candles": self.min_choch_candles,
                "choch_mode": self.choch_mode,
            }
        )
        return conf_dict


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

    def _find_flip_candle_chochs(self, candles: list[Candle]) -> list[ChochModel]:
        """
        Independent CHoCH detection - completely decoupled from BOS and
        from `self.pivots`/SwingPivots. Only BOS uses the pivot engine;
        this method never reads `self.pivots` at all.

          - a "flip-up" candle is a bullish (green) candle immediately
            preceded by a bearish (red) one. Its LOW becomes the reference
            level for the next bearish CHoCH.
          - a "flip-down" candle is the mirror: a red candle immediately
            preceded by a green one. Its HIGH becomes the reference level
            for the next bullish CHoCH.
          - a bearish CHoCH fires the instant any LATER candle's low
            touches or goes below the flip-up candle's low (a wick touch
            is enough - close does not need to break it). Mirrored for
            bullish CHoCH against flip-down candles.
          - only the MOST RECENT not-yet-fired flip candle of each type is
            "current"; a newer flip candle of the same type supersedes an
            older, not-yet-touched one.
          - consecutive CHoCHs of the same side are never allowed: a
            bullish CHoCH can only fire if the previous CHoCH (of either
            side) was bearish, and vice versa. The very first CHoCH ever
            can be either side.
          - a touch is only accepted if at least `min_choch_candles`
            candles separate the flip candle from the touch candle (a
            reversal that happens too fast - 1 or 2 candles later - is
            treated as noise, not a real CHoCH). Either way - accepted or
            rejected as too fast - the FIRST candle that touches a
            reference level consumes it; it is never left pending for a
            later candle to "confirm" the exact same level again.
          - STRUCTURAL VALIDITY: a cluster is only a legitimate CHoCH
            reference if its level is lower (bearish) / higher (bullish)
            than the level of its own immediately-following cluster (NOT
            necessarily the latest/current one).
          - fallback chain: if the current cluster is touched but rejected
            for being too fast, the same touching candle is checked
            against earlier clusters, walking backward one at a time.
            Structurally invalid candidates (against their own immediate
            successor - NOT necessarily "current") are skipped entirely
            without a touch check. Each structurally valid candidate found
            is touch/distance-checked; if it fires, the walk stops
            (success). If it's touched-but-too-fast (or simply not
            touched), the walk KEEPS GOING to the next older valid
            candidate - it does not give up after a single attempt. The
            walk only ends when something fires or the cluster history is
            exhausted.
          - universal cleanup: on EVERY candle, ANY still-unconsumed
            cluster (not just "current" or the one fallback candidate)
            whose level is also touched gets consumed right then. Without
            this, a level broken quietly while some newer cluster is
            "current" would stay falsely "fresh" and could resurface much
            later as a stale fallback once an unrelated future candle
            finally touches "current" too - producing a CHoCH that looks
            absurdly delayed relative to when the level was actually
            broken.

        The model's `anchor` is set to the extreme (highest high for a
        bearish CHoCH, lowest low for a bullish one) reached between the
        flip candle and the touch candle - i.e. the swing point that would
        invalidate the move - so it can still be used as an SL base price
        exactly like before.
        """

        def candle_color(c: Candle) -> str:
            if c.close > c.open:
                return "green"
            if c.close < c.open:
                return "red"
            return "doji"

        n = len(candles)
        colors = [candle_color(c) for c in candles]
        models: list[ChochModel] = []

        # Full, append-only history per side: [{"price", "index", "consumed"}, ...]
        # in chronological order. Never pruned (older entries may still be
        # needed as the "next cluster" reference for validity checks).
        bear_clusters: list[dict] = []
        bull_clusters: list[dict] = []
        last_side: MarketSide | None = None

        def make_model(side: MarketSide, ref_price: float, ref_index: int, touch_index: int) -> ChochModel:
            if side is MarketSide.BEARISH:
                anchor = max(c.high for c in candles[ref_index : touch_index + 1])
            else:
                anchor = min(c.low for c in candles[ref_index : touch_index + 1])
            model = ChochModel(
                side=side,
                break_candle=candles[touch_index],
                break_level=ref_price,
                pivot_candle=candles[ref_index],
                anchor=anchor,
                is_choch=True,
            )
            model.validated = True
            model.touch_candle = candles[touch_index]
            return model

        def try_fallback_chain(clusters: list[dict], want_lower: bool, side: MarketSide, i: int, touches) -> bool:
            """
            Walks backward from clusters[-2] (the one just before
            "current", already handled by the caller). Structurally
            invalid candidates are skipped over entirely (never touch-
            checked, never consumed - they may still be needed as a
            "next cluster" reference for even older candidates). For
            each structurally VALID, not-yet-consumed candidate found:
              - if this candle touches it, the candidate is consumed
                right away (regardless of outcome below);
              - if it also satisfies `min_choch_candles`, the CHoCH
                fires here and the walk stops (success);
              - otherwise (touched-but-too-fast, or not touched at all),
                the walk CONTINUES to the next (older) valid candidate -
                it does not give up after just one attempt.
            Returns True if something fired.
            """
            for k in range(len(clusters) - 2, -1, -1):
                candidate = clusters[k]
                if candidate["consumed"]:
                    continue
                next_price = clusters[k + 1]["price"]
                valid = (candidate["price"] < next_price) if want_lower else (candidate["price"] > next_price)
                if not valid:
                    continue
                if candidate["index"] < i and touches(candidate["price"]):
                    candidate["consumed"] = True
                    if i - candidate["index"] >= self.min_choch_candles:
                        models.append(make_model(side, candidate["price"], candidate["index"], i))
                        for p in clusters:
                            p["consumed"] = True
                        return True
                    # touched but too fast -> consumed, keep walking back
                # not touched (or touched-but-rejected handled above) -> keep walking back
            return False

        for i in range(1, n):
            if colors[i] == "green" and colors[i - 1] == "red":
                bear_clusters.append({"price": candles[i].low, "index": i, "consumed": False})
            if colors[i] == "red" and colors[i - 1] == "green":
                bull_clusters.append({"price": candles[i].high, "index": i, "consumed": False})

            # --- bearish CHoCH ---
            if bear_clusters:
                current = bear_clusters[-1]
                if not current["consumed"] and current["index"] < i and candles[i].low <= current["price"]:
                    current["consumed"] = True
                    if last_side is MarketSide.BEARISH:
                        pass  # alternation blocks it outright - no fallback either
                    elif i - current["index"] >= self.min_choch_candles:
                        models.append(make_model(MarketSide.BEARISH, current["price"], current["index"], i))
                        last_side = MarketSide.BEARISH
                        for p in bear_clusters:
                            p["consumed"] = True
                    else:
                        fired = try_fallback_chain(
                            bear_clusters, True, MarketSide.BEARISH, i, lambda price: candles[i].low <= price
                        )
                        if fired:
                            last_side = MarketSide.BEARISH

                # Universal cleanup - see docstring.
                for p in bear_clusters:
                    if not p["consumed"] and p["index"] < i and candles[i].low <= p["price"]:
                        p["consumed"] = True

            # --- bullish CHoCH ---
            if bull_clusters:
                current = bull_clusters[-1]
                if not current["consumed"] and current["index"] < i and candles[i].high >= current["price"]:
                    current["consumed"] = True
                    if last_side is MarketSide.BULLISH:
                        pass
                    elif i - current["index"] >= self.min_choch_candles:
                        models.append(make_model(MarketSide.BULLISH, current["price"], current["index"], i))
                        last_side = MarketSide.BULLISH
                        for p in bull_clusters:
                            p["consumed"] = True
                    else:
                        fired = try_fallback_chain(
                            bull_clusters, False, MarketSide.BULLISH, i, lambda price: candles[i].high >= price
                        )
                        if fired:
                            last_side = MarketSide.BULLISH

                # Universal cleanup - see docstring.
                for p in bull_clusters:
                    if not p["consumed"] and p["index"] < i and candles[i].high >= p["price"]:
                        p["consumed"] = True

        return models

    def _simulate(self, candles: list[Candle]) -> list[ChochModel]:
        self.pivots.set(candles)
        if self.choch_mode == 2:
            self.choch_events = self._find_flip_candle_chochs(candles)
        else:
            self.choch_events = []  # mode 1 fills this in below, from self.queue

        events = [
            {
                "pivot_index": p.index,
                "confirm_index": p.confirmed_index,
                "price": p.price,
                "type": "high" if p.is_high else "low",
            }
            for p in self.pivots.data
        ]
        self._pivot_events = [
            {
                "candle": candles[event["pivot_index"]],
                "price": event["price"],
                "type": event["type"],
            }
            for event in events
        ]
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

        if self.choch_mode == 1:
            self.choch_events = [model for model in self.queue if model.is_choch]

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
        # CHoCH (independent, flip-candle based) takes priority over BOS
        # (old pivot/range engine) when both would fire on the same candle.
        candidates: list[ChochModel] = list(self.choch_events)
        if self.use_bos:
            candidates += [model for model in self.queue if not model.is_choch]

        newest_validated: ChochModel | None = None
        for model in candidates:
            if not model.validated or model.touch_candle is None:
                continue
            if model.touch_candle.time != last_candle.time:
                continue
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

    def _draw_pivots(self, plot: ChartPlot):
        highs = [
            (event["candle"].time, event["price"])
            for event in self._pivot_events
            if event["type"] == "high"
        ]
        lows = [
            (event["candle"].time, event["price"])
            for event in self._pivot_events
            if event["type"] == "low"
        ]
        plot.mark_points(highs, legend="PivotHigh", color="#ff9800")
        plot.mark_points(lows, legend="PivotLow", color="#2196f3")

    def draw_all(self, plot: ChartPlot):
        if self.plot_pivots:
            self._draw_pivots(plot)
        for model in self.choch_events:
            self._draw_model(plot, model)
        if self.use_bos:
            for model in self.queue:
                if model.validated and not model.is_choch:
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