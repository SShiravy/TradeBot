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

    choch = ChochQueueFilter(pivot_length=2, retrace_fib=0.8, use_fibo_filter=True)
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
        depth=25,
        backstep=2,
        atr_len=14,
        touch_mult=0.5,
        break_mult=0.4,
        min_touches=2,
        min_line_bars=15,
        max_span_bars=150,
        stale_bars=50,
        max_total_lines=300,
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
        zone_break_bars=2,
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

    test_auto_trendlines()

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
