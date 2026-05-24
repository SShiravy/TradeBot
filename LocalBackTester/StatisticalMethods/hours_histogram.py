from datetime import datetime, timezone
from LocalBackTester.StatisticalMethods.models import BasePnLHistogram


class HourlyPnLHistogram(BasePnLHistogram):
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
