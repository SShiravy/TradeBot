from datetime import datetime
from LocalBackTester.StatisticalMethods.models import BasePnLHistogram
from TradingModule.models import Position


class WeekdayPnLHistogram(BasePnLHistogram):
    def __init__(self, all_positions: list[Position], plot_name: str):
        super().__init__(all_positions, plot_name)
        self.name = "Weekday PNL"

    def get_category(
        self,
        timestamp: int,
    ) -> str:
        dt = datetime.fromtimestamp(timestamp)

        return dt.strftime("%A")

    def category_order(self) -> list[str]:
        return [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
