from BackTest.StatisticalMethods.models import BasePnLHistogram
from datetime import datetime, timezone


class HourlyPnLHistogram(BasePnLHistogram):
    def __init__(self):
        super().__init__()
        self.name = "Hourly PNL"

    def get_category(
        self,
        timestamp: int,
    ) -> str:
        dt = datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc,
        )

        return str(dt.hour)

    def category_order(self) -> list[str]:
        return [str(i) for i in range(24)]


class WeekdayPnLHistogram(BasePnLHistogram):
    def __init__(self):
        super().__init__()
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


class SessionPnLHistogram(BasePnLHistogram):
    def __init__(self):
        super().__init__()
        self.name = "Session PNL"

    def get_category(
        self,
        timestamp: int,
    ) -> str:
        dt = datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc,
        )

        hour = dt.hour

        match hour:
            case h if 0 <= h < 6:
                return r"Sydney\Tokyo"

            case h if 6 <= h < 8:
                return "Tokyo"

            case h if 8 <= h < 9:
                return r"Tokyo\London"

            case h if 9 <= h < 13:
                return "London"

            case h if 13 <= h < 17:
                return r"London\NewYork"

            case h if 17 <= h < 21:
                return "NewYork"

            case h if 21 <= h < 22:
                return r"Sydney\NewYork"

            case h if 22 <= h < 0:
                return "Sydney"

            case _:
                return "Unknown"

    def category_order(self) -> list[str]:
        return [
            r"Sydney\Tokyo",
            "Tokyo",
            r"Tokyo\London",
            "London",
            r"London\NewYork",
            "NewYork",
            r"Sydney\NewYork",
            "Sydney",
        ]
