from ChartModule.models import TimeFrame
from LocalBackTester.models import CsvChart, KlineSource

# CRYPTO

BTCUSDT_1h_2024_9 = CsvChart(
    "BTCUSDT",
    TimeFrame.one_hour,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\BTCUSDT-1h-2024-09.csv",
    csv_source=KlineSource.BINCANCE,
)


SOLUSDT_1h_2024_9 = CsvChart(
    "SOLUSDT",
    TimeFrame.one_hour,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\SOLUSDT-1h-2024-09.csv",
    csv_source=KlineSource.BINCANCE,
)

# FOREX

XAUUSD_1m_99000 = CsvChart(
    "XAUUSD",
    TimeFrame.one_minute,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Opofincance\opo_XAUUSD_1m_99000.csv",
    csv_source=KlineSource.OPOFINANCE_META,
)

SOLUSD_1m_99000 = CsvChart(
    "SOLUSD",
    TimeFrame.one_minute,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Opofincance\opo_SOLUSD_1m_99000.csv",
    csv_source=KlineSource.OPOFINANCE_META,
)

BTCUSD_1m_99000 = CsvChart(
    "BTCUSD",
    TimeFrame.one_minute,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Opofincance\opo_BTCUSD_1m_99000.csv",
    csv_source=KlineSource.OPOFINANCE_META,
)


XAUUSD_5m_50000 = CsvChart(
    "XAUUSD",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Opofincance\opo_XAUUSD_5m_50000.csv",
    csv_source=KlineSource.OPOFINANCE_META,
)

SOLUSD_5m_50000 = CsvChart(
    "SOLUSD",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Opofincance\opo_SOLUSD_5m_50000.csv",
    csv_source=KlineSource.OPOFINANCE_META,
)

BTCUSD_5m_50000 = CsvChart(
    "BTCUSD",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Opofincance\opo_BTCUSD_5m_50000.csv",
    csv_source=KlineSource.OPOFINANCE_META,
)
