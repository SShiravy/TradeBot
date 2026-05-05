
from ChartModule.models import TimeFrame
from LocalBackTester.models import CsvChart, KlineSource


BTCUSDT_1h_2024_9 = CsvChart("BTCUSDT",TimeFrame.one_hour, 
                             csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\BTCUSDT-1h-2024-09.csv",
                             csv_source=KlineSource.BINCANCE)


SOLUSDT_1h_2024_9 = CsvChart("SOLUSDT",TimeFrame.one_hour,
                             csv_path=r"D:\TraderBot\LocalBackTester\KlinesCSV\Binance\SOLUSDT-1h-2024-09.csv",
                             csv_source=KlineSource.BINCANCE)


