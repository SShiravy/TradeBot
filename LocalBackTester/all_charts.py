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


BTCUSDT_5m_2026_4_5 = CsvChart(
    "BTCUSDT",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\BTCUSDT-5m-2026-04-05.csv",
    csv_source=KlineSource.BINCANCE,
)


SOLUSDT_5m_2026_4_5 = CsvChart(
    "SOLUSDT",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\SOLUSDT-5m-2026-04-05.csv",
    csv_source=KlineSource.BINCANCE,
)


BTCUSDT_5m_test = CsvChart(
    "BTCUSDT",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\BTCUSDT-5m-test.csv",
    csv_source=KlineSource.BINCANCE,
)


SOLUSDT_5m_test = CsvChart(
    "SOLUSDT",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\SOLUSDT-5m-test.csv",
    csv_source=KlineSource.BINCANCE,
)

BTCUSDT_5m_test_2024 = CsvChart(
    "BTCUSDT",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\BTCUSDT-5m-2024test.csv",
    csv_source=KlineSource.BINCANCE,
)


BTCUSDT_5m_2024_month0203 = CsvChart(
    "BTCUSDT",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\BTCUSDT-5m-2024-month0203.csv",
    csv_source=KlineSource.BINCANCE,
)


FTMUSDT_5m_test_2024 = CsvChart(
    "FTMUSDT",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\FTMUSDT-5m-2024test.csv",
    csv_source=KlineSource.BINCANCE,
)

FTMUSDT_5m_2024_month0203 = CsvChart(
    "FTMUSDT",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\FTMUSDT-5m-2024-month0203.csv",
    csv_source=KlineSource.BINCANCE,
)


AVAXUSDT_5m_test_2024 = CsvChart(
    "AVAXUSDT",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\AVAXUSDT-5m-2024test.csv",
    csv_source=KlineSource.BINCANCE,
)

AVAXUSDT_5m_2024_month0203 = CsvChart(
    "AVAXUSDT",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\AVAXUSDT-5m-2024-month0203.csv",
    csv_source=KlineSource.BINCANCE,
)


NEARUSDT_5m_test_2024 = CsvChart(
    "NEARUSDT",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\NEARUSDT-5m-2024test.csv",
    csv_source=KlineSource.BINCANCE,
)

NEARUSDT_5m_2024_month0203 = CsvChart(
    "NEARUSDT",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\NEARUSDT-5m-2024-month0203.csv",
    csv_source=KlineSource.BINCANCE,
)


PENDLEUSDT_5m_test_2024 = CsvChart(
    "PENDLEUSDT",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\PENDLEUSDT-5m-2024test.csv",
    csv_source=KlineSource.BINCANCE,
)

PENDLEUSDT_5m_2024_month0203 = CsvChart(
    "PENDLEUSDT",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\PENDLEUSDT-5m-2024-month0203.csv",
    csv_source=KlineSource.BINCANCE,
)


RNDRUSDT_5m_test_2024 = CsvChart(
    "RNDRUSDT",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\RNDRUSDT-5m-2024test.csv",
    csv_source=KlineSource.BINCANCE,
)

RNDRUSDT_5m_2024_month0203 = CsvChart(
    "RNDRUSDT",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\RNDRUSDT-5m-2024-month0203.csv",
    csv_source=KlineSource.BINCANCE,
)


SOLUSDT_5m_test_2024 = CsvChart(
    "SOLUSDT",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\SOLUSDT-5m-2024test.csv",
    csv_source=KlineSource.BINCANCE,
)

SOLUSDT_5m_2024_month0203 = CsvChart(
    "SOLUSDT",
    TimeFrame.five_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\SOLUSDT-5m-2024-month0203.csv",
    csv_source=KlineSource.BINCANCE,
)

# FOREX


SOLUSD_1m_5000_test = CsvChart(
    "SOLUSD",
    TimeFrame.one_minute,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Opofincance\opo_SOLUSD_1m_5000_test.csv",
    csv_source=KlineSource.OPOFINANCE_META,
)


XAUUSD_1m_5000_test = CsvChart(
    "XAUUSD",
    TimeFrame.one_minute,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Opofincance\opo_XAUUSD_1m_5000_test.csv",
    csv_source=KlineSource.OPOFINANCE_META,
    ticks_path=r"D:\TraderBot\LocalBackTester\TickData\Opofinance\XAUUSD!_2025_11_03_to_2026_05_19.parquet",
)


XAUUSD_1m_99000 = CsvChart(
    "XAUUSD",
    TimeFrame.one_minute,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Opofincance\opo_XAUUSD_1m_99000.csv",
    csv_source=KlineSource.OPOFINANCE_META,
    ticks_path=r"D:\TraderBot\LocalBackTester\TickData\Opofinance\XAUUSD!_2025_11_03_to_2026_05_19.parquet",
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

SOLUSD_3m_99000 = CsvChart(
    "SOLUSD",
    TimeFrame.three_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Opofincance\opo_SOLUSD_3m_99000.csv",
    csv_source=KlineSource.OPOFINANCE_META,
)

XAUUSD_3m_99000 = CsvChart(
    "XAUUSD",
    TimeFrame.three_minutes,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Opofincance\opo_XAUUSD_3m_99000.csv",
    csv_source=KlineSource.OPOFINANCE_META,
    ticks_path = r"D:\TraderBot\LocalBackTester\TickData\Opofinance\XAUUSD!_2025_12_01_to_2026_06_27.parquet",
)


XAUUSD_1m_99000_28_6 = CsvChart(
    "XAUUSD",
    TimeFrame.one_minute,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Opofincance\opo_XAUUSD_1m_99000_28_6.csv",
    csv_source=KlineSource.OPOFINANCE_META,
    ticks_path=r"D:\TraderBot\LocalBackTester\TickData\Opofinance\XAUUSD!_2025_12_01_to_2026_06_27.parquet",
)

USDJPY_1m_99000_28_6 = CsvChart(
    "USDJPY",
    TimeFrame.one_minute,
    csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Opofincance\opo_USDJPY_1m_99000_28_6.csv",
    csv_source=KlineSource.OPOFINANCE_META,
)