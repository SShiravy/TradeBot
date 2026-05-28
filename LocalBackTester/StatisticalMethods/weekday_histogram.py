from datetime import datetime
from LocalBackTester.StatisticalMethods.models import BasePnLHistogram


class WeekdayPnLHistogram(BasePnLHistogram):
    def __init__(self, pnl_list: list[float], timestamps: list[int], plot_name: str):
        super().__init__(pnl_list, timestamps, plot_name)
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
