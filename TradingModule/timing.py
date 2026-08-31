from __future__ import annotations
import time
from datetime import datetime, timezone
from typing import Optional, Union

TimeInput = Union[int, float, str, datetime]


class TimeHandler:
    """In backtest mode, set_time() freezes/advances time for every caller"""
    _override: Optional[int] = None
    _tz = timezone.utc

    @classmethod
    def now(cls) -> int:
        """Current time as integer unix timestamp (seconds)
        Overridden (backtest) if set, else real."""
        return cls._override if cls._override is not None else int(time.time())

    @classmethod
    def set_time(cls, when: TimeInput) -> None:
        cls._override = cls.to_timestamp(when)

    @classmethod
    def advance(cls, seconds: int) -> int:
        """Move the frozen time forward by `seconds`"""
        if cls._override is None:
            raise RuntimeError("Not in backtest mode — call set_time() first.")
        cls._override += int(seconds)
        return cls._override

    @classmethod
    def reset(cls) -> None:
        """Return to real-time mode"""
        cls._override = None

    @classmethod
    def is_backtest(cls) -> bool:
        return cls._override is not None

    @classmethod
    def to_timestamp(cls, value: TimeInput) -> int:
        """Normalize datetime/str/int/float -> integer unix seconds"""
        if isinstance(value, datetime):
            dt = value if value.tzinfo else value.replace(tzinfo=cls._tz)
            return int(dt.timestamp())
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            return int(cls.parse(value).timestamp())
        raise TypeError(f"Unsupported time type: {type(value)}")

    @classmethod
    def to_datetime(cls, value: TimeInput) -> datetime:
        """Convert any supported input to a tz-aware datetime (for formatting only)"""
        return datetime.fromtimestamp(cls.to_timestamp(value), tz=cls._tz)

    @staticmethod
    def parse(value: str, fmt: Optional[str] = None) -> datetime:
        """Parse a string; uses ISO format unless an explicit fmt is given."""
        return datetime.strptime(value, fmt) if fmt else datetime.fromisoformat(value)

    @classmethod
    def is_valid(cls, value: TimeInput) -> bool:
        try:
            cls.to_timestamp(value)
            return True
        except (ValueError, TypeError):
            return False

    @classmethod
    def format(cls, value: Optional[TimeInput] = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format `value` (default: current time) as a string."""
        ts = cls.now() if value is None else cls.to_timestamp(value)
        return cls.to_datetime(ts).strftime(fmt)

    @classmethod
    def elapsed_since(cls, value: TimeInput) -> int:
        """Seconds between `value` and current (possibly overridden) time."""
        return cls.now() - cls.to_timestamp(value)

    @classmethod
    def is_between(cls, start: TimeInput, end: TimeInput, value: Optional[TimeInput] = None) -> bool:
        """Whether `value` (default: now) falls within [start, end], inclusive."""
        v = cls.now() if value is None else cls.to_timestamp(value)
        return cls.to_timestamp(start) <= v <= cls.to_timestamp(end)


    def __init__(self, when: TimeInput):
        self._temp_time = self.to_timestamp(when)
        self._previous: Optional[int] = None

    def __enter__(self):
        self._previous = TimeHandler._override
        TimeHandler._override = self._temp_time
        return TimeHandler

    def __exit__(self, exc_type, exc_val, exc_tb):
        TimeHandler._override = self._previous

