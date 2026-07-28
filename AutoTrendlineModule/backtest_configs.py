from ChartModule import Chart, TimeFrame
from AutoTrendlineModule.auto_trendline import AutoTrendlines
from Forex import ForexAgent
from BitUnix import BitUnixAgent
from config import settings

# Forex / Gold ------------------------------------------------------------


forex_auto_trendlines_one_m = AutoTrendlines(
    depth=12,
    atr_len=14,
    touch_mult=0.15,
    break_mult=0.40,
    min_touches=3,
    min_line_bars=15,
    max_span_bars=2000,
    max_stored_pivots=60,
    max_active_per_dir=4,
    max_total_lines=20,
    stale_bars=50,
    merge_projection_bars=50,
    display_only_aligned=True,
)


def run_forex_auto_trendlines_example():
    chart = Chart("XAUUSD!", TimeFrame.one_minute)
    chartdata = ForexAgent().get_chartdata(chart, 1000)
    if chartdata is None:
        raise ValueError(f"{chartdata=}")

    forex_auto_trendlines_one_m.set(chartdata.candles)
    for line in forex_auto_trendlines_one_m.data:
        print(line)


# Crypto --------------------------------------------------------------


bitunix_agent = BitUnixAgent(settings.BITUNIX_API_KEY, settings.BITUNIX_API_SECRET_KEY)

crypto_auto_trendlines_five_m = AutoTrendlines(
    depth=10,
    atr_len=14,
    touch_mult=0.15,
    break_mult=0.40,
    min_touches=3,
    min_line_bars=10,
    max_span_bars=1500,
    display_only_aligned=True,
)


def run_crypto_auto_trendlines_example():
    chart = Chart("SOLUSDT", TimeFrame.five_minutes)
    chartdata = bitunix_agent.get_chartdata(chart, 1000)
    if chartdata is None:
        raise ValueError(f"{chartdata=}")

    crypto_auto_trendlines_five_m.set(chartdata.candles)
    for line in crypto_auto_trendlines_five_m.data:
        print(line)
