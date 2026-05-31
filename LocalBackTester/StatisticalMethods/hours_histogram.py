from datetime import datetime, timezone
from LocalBackTester.StatisticalMethods.models import BasePnLHistogram
from TradingModule.models import Position


class HourlyPnLHistogram(BasePnLHistogram):
    def __init__(self, all_positions: list[Position], plot_name: str):
        super().__init__(all_positions, plot_name)
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
