from ChartModule.models import Chart, ChartData, MarketSide
from ChartModule.Indicators import Indicator, SupportCandlesPattern
from ChartModule.Indicators.auto_trendline import AutoTrendlines
from ChartModule.plot import ChartPane
from Bots.CompositeStrategies.models import MTRSignal
from TraderBot.models import Strategy, StrategyPlotter
import logging


logger = logging.getLogger("MTR_Signal")


class MTRPlotter(StrategyPlotter):
    def __call__(
        self,
        pane: ChartPane,
        signal: MTRSignal,
        indicators: list[Indicator] = [],
        *args,
        show_archived: bool | None = None,
        **kwargs,
    ):
        for indicator in indicators:
            if not isinstance(indicator, AutoTrendlines) or indicator.data is None:
                continue
            indicator.plotter(
                pane,
                indicator.data,
                mtr_events=indicator.mtr_events,
                atr=indicator.atr.data,
                keep_archived=indicator.keep_archived,
                show_archived=show_archived,
            )
        super().__call__(pane, signal)


class MTRFilter(Strategy):
    """
    Fires whenever the trendline engine reports one or more simultaneous
    trendline breaks (an MTR event) on the candle that just closed.

    The old version carried a `DummyStrategy` placeholder because the
    trade config required one while the detection lived on the config
    itself. There is nothing dummy about it in the new layout: this is a
    plain Strategy, so a plain TraderBot runs it -- no bot subclass.
    """

    def __init__(
        self,
        mtr_indicator: AutoTrendlines,
        long_support_conditions=SupportCandlesPattern.RAW,
        short_support_conditions=SupportCandlesPattern.RAW,
        name="MTR",
    ) -> None:
        # the trendline engine is the strategy's own indicator, so it rides
        # in `indicators` and the default plotter call path can reach it
        super().__init__(
            name,
            MTRPlotter(),
            long_support_conditions,
            short_support_conditions,
            [mtr_indicator],
        )
        self.mtr_indicator = mtr_indicator
        self.chart: Chart | None = None
        self.last_checked_timestamp: int | None = None
        self.last_mtr_signal: MTRSignal | None = None

    def export_config(self):
        conf_dict = super().export_config()
        conf_dict.update({"mtr_indicator": self.mtr_indicator.export_configs()})
        return conf_dict

    def check_signal(
        self,
        chartdata: ChartData,
        check_long: bool = True,
        check_short: bool = True,
        *args,
        **kwargs,
    ) -> MTRSignal | None:
        self.chart = chartdata.chart
        if len(chartdata) == 0:
            return None

        last_candle = chartdata[-1]
        if self.last_checked_timestamp == last_candle.timestamp:
            return None

        self.mtr_indicator.set(chartdata)
        self.last_checked_timestamp = last_candle.timestamp

        events = self.mtr_indicator.mtr_events
        if not events:
            return None
        event = events[-1]
        if event.candle.timestamp != last_candle.timestamp:
            return None

        if event.side is MarketSide.BULLISH and not check_long:
            return None
        if event.side is MarketSide.BEARISH and not check_short:
            return None

        self.last_mtr_signal = MTRSignal(
            chartdata.chart, last_candle, event.side, self.name, event
        )
        logger.info(f"MTR Signal: {self.last_mtr_signal} ({event.text})")
        return self.last_mtr_signal
