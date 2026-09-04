from custom_logger import CustomLogger
import logging
import asyncio


CustomLogger(True, consol_log_level=logging.DEBUG)


async def start_diver_backtest():
    from DivergenceStrategy.backtest_configs import (
        forex_diver_one_m,
    )

    await forex_diver_one_m.backtest(1000, show_image=True)


async def start_diver_crypto_backtest_pack():
    from BacktestModule.crypto_diver_pack import start_diver_crypto_backtest_pack

    await start_diver_crypto_backtest_pack(send_report=True)


async def test_open_position():
    from TradingModule.trader_bot import TraderBot
    from TradingModule.reporter import TelegramReporter
    from ChartModule.models import MarketSide
    from DivergenceStrategy.backtest_configs import (
        forex_diver_one_m,
    )

    TelegramReporter().disable_reporting()
    the_config = forex_diver_one_m
    the_config.position_handler.short_trade = True
    the_config.position_handler.long_trade = True

    base_chartdata, second_chartdata = the_config.get_chartdata(100)
    diver_signal = the_config.strategy.generate_dummy_signal(
        base_chartdata, second_chartdata, MarketSide.BULLISH
    )
    logging.info(f"dummy diver signal: {diver_signal}")
    pos = await the_config.position_handler.generate_position(diver_signal)
    logging.info(f"position created from the dummy signal: {pos}")
    logging.info(
        f"opoen position: {the_config.agent.get_open_positions(chart=the_config.chart, comment_filter='')}"
    )
    await asyncio.gather(
        TraderBot(name="test opening pos", configs=[the_config]).manage()
    )


async def test_BitUnix_open_position():
    from TradingModule.trader_bot import TraderBot
    from config import settings
    from TradingModule.reporter import TelegramReporter
    from ChartModule.models import MarketSide
    from DivergenceStrategy.backtest_configs import (
        crypto_diver_five_m_sol,
        crypto_diver_five_m_near,
    )
    from BitUnix import BitUnixAgent

    agent = BitUnixAgent(settings.BITUNIX_API_KEY, settings.BITUNIX_API_SECRET_KEY)

    # from ChartModule.models import Chart, TimeFrame
    # from ChartModule.plot import ChartPlot
    # logging.debug(agent.bitunix_api.get_kline("BTCUSDT", "5m", limit=1))
    # chartdata = agent.get_chartdata(
    #     Chart("BTCUSDT", TimeFrame.five_minutes), n_bars=200
    # )
    # ChartPlot(chartdata, 200).show()  # type: ignore

    logging.debug(agent.bitunix_api.get_account())

    TelegramReporter().disable_reporting()
    the_config = crypto_diver_five_m_near
    the_config.position_handler.short_trade = True
    the_config.position_handler.long_trade = True

    base_chartdata, second_chartdata = the_config.get_chartdata(10)
    diver_signal = the_config.strategy.generate_dummy_signal(
        base_chartdata, second_chartdata, MarketSide.BULLISH
    )
    logging.info(f"dummy diver signal: {diver_signal}")
    pos = await the_config.position_handler.generate_position(diver_signal)
    if not pos:
        raise ValueError(f"{pos=}")
    await asyncio.gather(
        TraderBot(name="test opening pos", configs=[the_config]).manage()
    )


def test_handler_export_config():
    from DivergenceStrategy.backtest_configs import forex_diver_one_m

    logging.info(forex_diver_one_m.position_handler.export_config())


def store_mt5_data():
    from LocalBackTester.models import CsvChart
    from ChartModule.models import TimeFrame
    from LocalBackTester.methods import (
        store_forex_data,
        plot_csv_kline,
        # store_mt5_tick_data,
    )

    # store_mt5_tick_data()

    chart = CsvChart(
        "XAUUSD",
        timeframe=TimeFrame.one_minute,
        csv_path="opo_XAUUSD_1m_99000_28_6.csv",
    )
    store_forex_data(chart, 99000)
    plot_csv_kline(chart)
    pass


def test_rsi():
    from ChartModule.Indicators.rsi import RSI
    from ChartModule.models import Chart, TimeFrame
    from ChartModule.plot import ChartWithOscillatorPlot
    from Forex.agent import ForexAgent

    chart = Chart("XAUUSD!", TimeFrame.one_minute)
    chart_data = ForexAgent().get_chartdata(chart, 200)
    if chart_data is None:
        raise ValueError

    rsi = RSI()
    rsi.set(candles=chart_data.candles)
    plot = ChartWithOscillatorPlot(chart_data, rsi.data, 3000, label="RSI")
    rsi.plot(plot, plot.oscillator_ax)
    plot.show()


def test_choch_queue():
    from ChartModule.models import Chart, TimeFrame
    from ChartModule.plot import ChartPlot
    from ChochQueueStrategy.choch_queue import ChochQueueFilter
    from Forex.agent import ForexAgent

    chart = Chart("XAUUSD", TimeFrame.one_minute)
    chart_data = ForexAgent().get_chartdata(chart, 500)
    if chart_data is None:
        raise ValueError

    choch = ChochQueueFilter(pivot_length=2, max_queue=30, retrace_fib=0.8, use_fibo_filter=False, plot_pivots=True)
    choch.check_signal(chart_data)

    validated_models = [model for model in choch.queue if model.validated]
    logging.info(f"found {len(validated_models)} validated signals:")
    for model in validated_models:
        tag = "CHoCH" if model.is_choch else "BOS"
        logging.info(
            f"  [{tag}] {model.side} | break_level={model.break_level} "
            f"| break_time={model.break_candle.time} | touch_time={model.touch_candle.time if model.touch_candle else None}"
        )

    plot = ChartPlot(chart_data, len(chart_data.candles))
    plot.plot()
    choch.draw_all(plot)
    plot.show()


def test_ema_pivot_choch(n_ltf_candles: int = 120, n_htf_candles: int = 120, warm_up_candles: int = 10):
    from ChartModule.models import Chart, TimeFrame
    from ChartModule.plot import DoubleChartPlot
    from EmaPivotChochStrategy.ema_pivot_choch import EmaPivotChochFilter
    from Forex.agent import ForexAgent

    ltf_chart = Chart("XAUUSD", TimeFrame.one_minute)
    htf_chart = Chart("XAUUSD", TimeFrame.five_minutes)

    ltf_chartdata = ForexAgent().get_chartdata(ltf_chart, n_ltf_candles)
    htf_chartdata = ForexAgent().get_chartdata(htf_chart, n_htf_candles)
    if ltf_chartdata is None or htf_chartdata is None:
        raise ValueError

    logging.info(
        f"fetched LTF: {len(ltf_chartdata.candles)} candles, "
        f"{ltf_chartdata.candles[0].time} -> {ltf_chartdata.candles[-1].time}"
    )
    logging.info(
        f"fetched HTF: {len(htf_chartdata.candles)} candles, "
        f"{htf_chartdata.candles[0].time} -> {htf_chartdata.candles[-1].time}"
    )

    ema_pivot_choch = EmaPivotChochFilter(
        ema_periods=[20, 40, 60, 80],
        htf_pivot_length=1,
        htf_backstep=2,
        atr_period=14,
        atr_multiplier=1.0,
        max_bars_after_pivot=100,
        choch_pivot_length=2,
        choch_backstep=2,
        retrace_fib=0.5,
        use_fibo_filter=False,
        use_bos=False,
        use_choch=False
    )

    signals = []
    ltf_candles = ltf_chartdata.candles
    htf_candles = htf_chartdata.candles
    for i in range(warm_up_candles, len(ltf_candles)):
        window = ltf_chartdata.give_sub_chartdata(ltf_candles[: i + 1])
        last_time = window.candles[-1].time
        htf_window_candles = [c for c in htf_candles if c.time <= last_time]
        if len(htf_window_candles) < ema_pivot_choch.htf_pivot_length * 3:
            continue
        htf_window = htf_chartdata.give_sub_chartdata(htf_window_candles)
        signal = ema_pivot_choch.check_signal(window, htf_window)
        if signal is not None:
            signals.append(signal)

    logging.info(
        f"found {len(signals)} EmaPivotChoch signals over {len(ltf_candles)} LTF candles:"
    )
    for s in signals:
        logging.info(f"  {s}")

    logging.info(f"funnel diagnostics (cumulative over the whole walk): {ema_pivot_choch.debug_counters}")
    logging.info(f"diagnostics of the LAST check_signal() call: {ema_pivot_choch.debug_last_call}")

    plot = DoubleChartPlot(ltf_chartdata, htf_chartdata, plot_n_candles=n_ltf_candles)
    if signals:
        ema_pivot_choch.draw_all(plot, signals, draw_indicators=True)
    else:
        logging.info("no signals found in this window, showing raw EMAs instead")
        colors = ema_pivot_choch._ema_colors()
        for period, ema_values in ema_pivot_choch._emas.items():
            plot.second_plot.linear_plot(
                ema_values.keys(), ema_values.values(),
                color=colors[period],
            )

    logging.info(f"marking {len(ema_pivot_choch._touch_events)} EMA-pivot touches on the LTF chart")
    touch_debug = ema_pivot_choch.describe_touches()
    suspicious = [t for t in touch_debug if t["suspicious"]]
    out_of_range = [t for t in touch_debug if t["out_of_ltf_range"]]
    logging.info(
        f"touch alignment check: {len(suspicious)}/{len(touch_debug)} genuinely misaligned "
        f"(landed more than one HTF bar away from their pivot's own candle - should be 0), "
        f"{len(out_of_range)} pinned to LTF start because their pivot predates the fetched LTF window (expected)"
    )
    for t in touch_debug:
        flag = " <-- SUSPICIOUS" if t["suspicious"] else (" (out of LTF range)" if t["out_of_ltf_range"] else "")
        logging.info(
            f"  pivot={t['pivot_time']} (is_high={t['pivot_is_high']}) -> "
            f"ltf_marker={t['ltf_marker_time']}  delta={t['delta']}{flag}"
        )
    ema_pivot_choch.draw_touches(plot, ltf_chartdata=ltf_chartdata, htf_chartdata=htf_chartdata)

    plot.show()


def test_auto_trendlines():
    from ChartModule.models import Chart, TimeFrame
    from ChartModule.plot import ChartPlot
    from AutoTrendlineModule import AutoTrendlines
    from Forex.agent import ForexAgent

    chart = Chart("XAUUSD", TimeFrame.one_minute)
    chart_data = ForexAgent().get_chartdata(chart, 1000)
    if chart_data is None:
        raise ValueError

    auto_trendlines = AutoTrendlines(
        depth=15,
        backstep=2,
        atr_len=14,
        touch_mult=0.5,
        break_mult=0.4,
        min_touches=2,
        min_line_bars=15,
        max_span_bars=150,
        stale_bars=50,
        max_total_lines=500,
        max_active_per_dir=50,
        merge_projection_bars=50,
        display_only_aligned=False,
    )
    auto_trendlines.set(chart_data.candles)

    active_lines = [line for line in auto_trendlines.data if not line.broken]
    logging.info(
        f"total lines: {len(auto_trendlines.data)}, active: {len(active_lines)}"
    )
    for line in auto_trendlines.data:
        logging.info(line)

    plot = ChartPlot(chart_data, len(chart_data.candles))
    plot.plot()
    auto_trendlines.plot(plot)
    plot.show()


def test_sr_zones():
    from ChartModule.models import Chart, TimeFrame
    from ChartModule.plot import ChartPlot
    from SRZoneModule import SRZones
    from Forex.agent import ForexAgent

    chart = Chart("XAUUSD", TimeFrame.one_minute)
    chart_data = ForexAgent().get_chartdata(chart, 1000)
    if chart_data is None:
        raise ValueError

    sr_zones = SRZones(
        depth=20,
        backstep=2,
        max_candidates=150,
        atr_len=14,
        atr_median_lookback=21,
        radius_factor=1.0,
        min_radius_mult=0.25,
        max_radius_mult=3.0,
        merge_nearby=True,
        merge_interval_bars=300,
        width_mult=1.0,
        fallback_width_factor=0.35,
        max_zone_touches=5,
        max_zone_breaks=1,
        zone_break_bars=1,
        min_bars_between_touches=3,
        max_bars_between_touches=200,
        prune_after_bars=4500,
    )
    sr_zones.set(chart_data.candles)

    active_zones = [zone for zone in sr_zones.data if not zone.broken]
    logging.info(f"total zones: {len(sr_zones.data)}, active: {len(active_zones)}")
    for zone in sr_zones.data:
        logging.info(zone)

    plot = ChartPlot(chart_data, len(chart_data.candles))
    plot.plot()
    sr_zones.plot(
        plot,
        min_score_percentile=0,
        max_zones_display=None,
        proximity_boost=0.3,
        show_labels=True,
        show_live=True,
    )
    plot.show()


if __name__ == "__main__":
    import cProfile
    import pstats

    profiler = cProfile.Profile()
    profiler.enable()
    # asyncio.run(start_diver_crypto_backtest_pack())
    # asyncio.run(start_diver_backtest())
    # asyncio.run(start_fibochoch_backtest())
    # asyncio.run(start_fich_diver_backtest())

    # test_choch_queue()

    test_ema_pivot_choch()

    # test_auto_trendlines()

    # test_sr_zones()

    # new_backtest()

    # store_mt5_data()

    # asyncio.run(test_open_position())

    # test_handler_export_config()

    # asyncio.run(test_BitUnix_open_position())

    # test_rsi()

    # from datetime import datetime
    # print(datetime.fromtimestamp(1782313800))

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumtime")
    stats.print_stats(30)