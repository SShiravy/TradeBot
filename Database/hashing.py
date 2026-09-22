import hashlib
import json
from enum import Enum
from typing import Any


def normalize(value: Any) -> Any:
    """
    Recursively turn a config value into json serializable primitives.

    Enums are reduced to their value so the produced hash stays stable
    between runs (Chart.export_config keeps chart_type as an Enum).
    """
    if isinstance(value, Enum):
        return normalize(value.value)
    if isinstance(value, dict):
        return {str(key): normalize(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted((normalize(item) for item in value), key=repr)
    if isinstance(value, (list, tuple)):
        return [normalize(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def serialize_config(config: dict) -> str:
    """Dump a config dict deterministically, ready to be stored as a column."""
    return json.dumps(normalize(config), sort_keys=True, separators=(",", ":"))


def generate_hash(payload: dict) -> str:
    """sha256 of the deterministic json dump of payload."""
    return hashlib.sha256(serialize_config(payload).encode()).hexdigest()
