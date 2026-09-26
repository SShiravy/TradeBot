"""Plain-text building blocks shared by every analysis `__str__`."""

from Settings.timing import TimeHandler
from typing import Sequence, Self
import math


WIDTH = 60


def money(value: float) -> str:
    return f"{value:+,.2f} $"


def signed(value: float, decimals: int = 2) -> str:
    return "-" if math.isnan(value) else f"{value:+,.{decimals}f}"


def number(value: float, decimals: int = 2) -> str:
    if math.isnan(value):
        return "-"
    if math.isinf(value):
        return "inf"
    return f"{value:,.{decimals}f}"


def percent(value: float, decimals: int = 1) -> str:
    return "-" if math.isnan(value) else f"{value:.{decimals}f}%"


def moment(timestamp: int) -> str:
    return TimeHandler.format(timestamp, "%Y-%m-%d %H:%M")


def duration(seconds: float) -> str:
    days, rest = divmod(int(seconds), 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    if days:
        return f"{days}d {hours:02d}h {minutes:02d}m"
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m"


class TextReport:
    """Fixed-width report in the same layout as `PnLReport.__str__`."""

    def __init__(self, title: str, subtitle: str = "") -> None:
        heading = f"{title} | {subtitle}" if subtitle else title
        self._lines = [heading, "=" * WIDTH]

    def section(self, name: str) -> Self:
        self._lines += ["", name, "-" * WIDTH]
        return self

    def field(self, label: str, value: object) -> Self:
        self._lines.append(f"{label:<17}: {value}")
        return self

    def line(self, text: str) -> Self:
        self._lines.append(text)
        return self

    def table(self, headers: Sequence[str], rows: Sequence[Sequence[object]]) -> Self:
        """First column left-aligned, the rest right-aligned."""
        cells = [[str(cell) for cell in row] for row in rows]
        widths = [
            max([len(header)] + [len(row[i]) for row in cells])
            for i, header in enumerate(headers)
        ]

        def join(values: Sequence[str]) -> str:
            first, *rest = zip(values, widths)
            parts = [first[0].ljust(first[1])] + [v.rjust(w) for v, w in rest]
            return "  ".join(parts).rstrip()

        self._lines.append(join(headers))
        self._lines.append(join(["-" * w for w in widths]))
        self._lines += [join(row) for row in cells]
        return self

    def __str__(self) -> str:
        return "\n".join(self._lines)
