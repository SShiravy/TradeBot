from datetime import datetime
from LocalBackTester.StatisticalMethods.models import BasePnLHistogram


class WeekdayPnLHistogram(BasePnLHistogram):
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
