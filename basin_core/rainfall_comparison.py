"""Same-date rainfall comparison; no inferred spatial or climatic equivalence."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import math
from collections.abc import Mapping

from basin_core.uploads import RainfallPreview


@dataclass(frozen=True)
class RainfallComparison:
    rows: tuple[tuple[date, float | None, float | None], ...]
    paired_days: int
    upload_total_mm: float
    reference_total_mm: float

    @property
    def difference_mm(self) -> float:
        return self.upload_total_mm - self.reference_total_mm

    @property
    def relative_difference_pct(self) -> float | None:
        if self.reference_total_mm == 0:
            return None
        return 100 * self.difference_mm / self.reference_total_mm


def compare_rainfall(upload: RainfallPreview, reference: Mapping[date, float | None],
                     *, relationship: str, daily_basis_confirmed: bool) -> RainfallComparison:
    if relationship not in ("same_station", "regional_proxy"):
        raise ValueError("Declare a same-station comparison or acknowledge a regional proxy.")
    if not daily_basis_confirmed:
        raise ValueError("Confirm comparable daily observation periods before calculating.")
    local = dict(upload.observations)
    rows = []
    pairs = []
    for offset in range(upload.expected_days):
        day = upload.observations[0][0] + timedelta(days=offset)
        observed, benchmark = local.get(day), reference.get(day)
        if benchmark is not None and (not math.isfinite(benchmark) or benchmark < 0):
            raise ValueError("Reference contains invalid rainfall; review its quality before comparing.")
        rows.append((day, observed, benchmark))
        if observed is not None and benchmark is not None:
            pairs.append((observed, benchmark))
    if not pairs:
        raise ValueError("No dates have valid rainfall in both datasets. Choose an overlapping period.")
    return RainfallComparison(tuple(rows), len(pairs), math.fsum(x for x, _ in pairs),
                              math.fsum(y for _, y in pairs))
