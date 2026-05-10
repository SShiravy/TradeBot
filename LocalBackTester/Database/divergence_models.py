from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime


class DiverSignals(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    signal_timestamp: int

    baseline_start_timestamp: int
    baseline_end_timestamp: int
    secondline_start_timestamp: int
    secondline_end_timestamp: int
    
    side: str
    source: int = Field(foreign_key="backtestrun.id", index=True)


class DiverBacktests(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    config_hash: str = Field(index=True, unique=True)

    symbol: str
    second_symbol: Optional[str] = None
    timeframe: str

    first_candle_timestamp: int
    last_candle_timestamp: int


    created_at: datetime = Field(default_factory=datetime.utcnow)

    config_json: str