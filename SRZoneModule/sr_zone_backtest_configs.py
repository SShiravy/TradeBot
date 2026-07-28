from ChartModule import Chart, TimeFrame
from SRZoneModule.sr_zone import SRZones
from Forex import ForexAgent
from BitUnix import BitUnixAgent
from config import settings

# Forex / Gold ------------------------------------------------------------


forex_sr_zones_one_m = SRZones(
    depth=12,
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
    max_bars_between_touches=300,
    prune_after_bars=4500,
)


def run_forex_sr_zones_example():
    chart = Chart("XAUUSD!", TimeFrame.one_minute)
    chartdata = ForexAgent().get_chartdata(chart, 1000)
    if chartdata is None:
        raise ValueError(f"{chartdata=}")

    forex_sr_zones_one_m.set(chartdata.candles)
    for zone in forex_sr_zones_one_m.data:
        print(zone)


# Crypto --------------------------------------------------------------


bitunix_agent = BitUnixAgent(settings.BITUNIX_API_KEY, settings.BITUNIX_API_SECRET_KEY)

crypto_sr_zones_five_m = SRZones(
    depth=10,
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
    max_bars_between_touches=250,
    prune_after_bars=4500,
)


def run_crypto_sr_zones_example():
    chart = Chart("SOLUSDT", TimeFrame.five_minutes)
    chartdata = bitunix_agent.get_chartdata(chart, 1000)
    if chartdata is None:
        raise ValueError(f"{chartdata=}")

    crypto_sr_zones_five_m.set(chartdata.candles)
    for zone in crypto_sr_zones_five_m.data:
        print(zone)
