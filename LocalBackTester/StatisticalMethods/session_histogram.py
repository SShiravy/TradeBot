from datetime import datetime, timezone
from LocalBackTester.StatisticalMethods.models import BasePnLHistogram


class SessionPnLHistogram(BasePnLHistogram):
    def get_category(
        self,
        timestamp: int,
    ) -> str:
        dt = datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc,
        )

        hour = dt.hour

        if 0 <= hour < 7:
            return "Asian"

        elif 7 <= hour < 10:
            return "London Open"

        elif 12 <= hour < 16:
            return r"London\NY Overlap"

        elif 13 <= hour < 22:
            return "New York"

        return "Dead Market"

    def category_order(self) -> list[str]:
        return [
            "Asian",
            "London Open",
            r"London\NY Overlap",
            "New York",
            "Dead Market",
        ]
