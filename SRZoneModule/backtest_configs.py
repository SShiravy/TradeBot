from ChartModule import Chart, TimeFrame
from SRZoneModule.sr_zone import SRZones
from ExchangeAgents.MT5 import MT5Agent
from ExchangeAgents.BitUnix import BitUnixAgent
from config import settings

# Forex / Gold ------------------------------------------------------------


forex_sr_zones_one_m = SRZones(
    depth=12,
    backstep=2,
    atr_len=14,
    zone_radius_mult=1.0,
    fallback_width_mult=0.35,
    min_bars_between_touches=3,
    max_bars_between_touches=300,
    max_touches=5,
    break_bars=2,
    stale_bars=300,
)


def run_forex_sr_zones_example():
    chart = Chart("XAUUSD!", TimeFrame.one_minute)
    chartdata = MT5Agent().get_chartdata(chart, 1000)
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
    atr_len=14,
    zone_radius_mult=1.0,
    fallback_width_mult=0.35,
    min_bars_between_touches=3,
    max_bars_between_touches=250,
    max_touches=5,
    break_bars=2,
    stale_bars=250,
)


def run_crypto_sr_zones_example():
    chart = Chart("SOLUSDT", TimeFrame.five_minutes)
    chartdata = bitunix_agent.get_chartdata(chart, 1000)
    if chartdata is None:
        raise ValueError(f"{chartdata=}")

    crypto_sr_zones_five_m.set(chartdata.candles)
    for zone in crypto_sr_zones_five_m.data:
        print(zone)
