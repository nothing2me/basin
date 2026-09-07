"""Bounded, preview-only import of one local rainfall station."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
import hashlib
import io
import math
import re
from typing import Literal

MAX_BYTES = 10 * 1024 * 1024
MAX_ROWS = 250_000
TEMPLATE = b"date,precipitation\n2026-01-01,0\n2026-01-02,2.5\n2026-01-04,\n"


@dataclass(frozen=True)
class RainfallPreview:
    station: str
    location: str
    unit: str
    original_sha256: str
    observations: tuple[tuple[date, float | None], ...]

    @property
    def expected_days(self) -> int:
        return (self.observations[-1][0] - self.observations[0][0]).days + 1

    @property
    def valid_days(self) -> int:
        return sum(value is not None for _, value in self.observations)

    @property
    def missing_days(self) -> int:
        return self.expected_days - self.valid_days


def preview_rainfall(raw: bytes, station: str, location: str,
                     unit: Literal["mm", "inches"]) -> RainfallPreview:
    """Validate without changing sources, sessions, or scenario approvals."""
    if not station.strip() or not location.strip():
        raise ValueError("Enter a station name and location description.")
    if len(station) > 200 or len(location) > 500:
        raise ValueError("Use at most 200 characters for station and 500 for location.")
    if unit not in ("mm", "inches"):
        raise ValueError("Choose millimetres or inches explicitly.")
    if len(raw) > MAX_BYTES:
        raise ValueError("CSV exceeds the 10 MB limit.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("Save the CSV as UTF-8 text.") from error
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    records: dict[date, float | None] = {}
    try:
        if next(reader, None) != ["date", "precipitation"]:
            raise ValueError("Use exactly these columns: date,precipitation. Download the template.")
        for number, row in enumerate(reader, start=2):
            if number - 1 > MAX_ROWS:
                raise ValueError("CSV exceeds the 250,000 row limit.")
            if len(row) != 2:
                raise ValueError(f"Record {number}: expected two columns.")
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row[0]):
                raise ValueError(f"Record {number}: use YYYY-MM-DD dates.")
            try:
                day = date.fromisoformat(row[0])
            except ValueError as error:
                raise ValueError(f"Record {number}: invalid calendar date.") from error
            if day in records:
                raise ValueError(f"Record {number}: duplicate date {day}; resolve it before importing.")
            value = None
            if row[1].strip():
                try:
                    value = float(row[1]) * (25.4 if unit == "inches" else 1.0)
                except ValueError as error:
                    raise ValueError(f"Record {number}: precipitation must be a number or blank.") from error
                if not math.isfinite(value) or value < 0:
                    raise ValueError(f"Record {number}: rainfall must be finite and nonnegative.")
            records[day] = value
    except csv.Error as error:
        raise ValueError("Malformed CSV quoting or oversized field; use the template.") from error
    if not records or all(value is None for value in records.values()):
        raise ValueError("Include at least one valid rainfall observation.")
    result = RainfallPreview(station.strip(), location.strip(), unit,
                             hashlib.sha256(raw).hexdigest(), tuple(sorted(records.items())))
    if result.expected_days > MAX_ROWS:
        raise ValueError("Date span exceeds 250,000 calendar days.")
    return result
