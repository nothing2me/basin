"""Generate realistic daily on-farm rainfall dataset for Garza Farm, San Patricio / Nueces County, TX.

Covers 2021 through 2024 (1,461 days).
Reflects South Texas Coastal Bend precipitation dynamics:
- Early spring planting pulses (March-April)
- Intense summer flash drought and dry spells (May-August)
- Fall tropical moisture pulses (September-October)
- Severe multi-year drought sequence leading to regional reservoir depletion (38% storage in Choke Canyon + Lake Corpus Christi).
"""
import datetime
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from basin_core.uploads import preview_rainfall

def generate_garza_farm_rainfall() -> pd.DataFrame:
    monthly_targets = {
        # 2021: Moderate start, historic wet May deluges, then dry summer, late tropical pulses
        (2021, 1): 1.10, (2021, 2): 1.35, (2021, 3): 1.80, (2021, 4): 2.10,
        (2021, 5): 6.65, (2021, 6): 1.45, (2021, 7): 0.60, (2021, 8): 0.85,
        (2021, 9): 4.80, (2021, 10): 3.20, (2021, 11): 1.15, (2021, 12): 1.25,
        # 2022: Drought deepens; dry spring planting, blistering summer flash drought (Jul 0.0 in)
        (2022, 1): 0.75, (2022, 2): 0.60, (2022, 3): 1.10, (2022, 4): 1.40,
        (2022, 5): 1.20, (2022, 6): 0.25, (2022, 7): 0.00, (2022, 8): 0.65,
        (2022, 9): 3.85, (2022, 10): 2.10, (2022, 11): 1.35, (2022, 12): 1.10,
        # 2023: Historic Texas heat dome, extreme prolonged summer drought (Jun 0.15, Jul 0.0, Aug 0.05 in)
        (2023, 1): 0.95, (2023, 2): 1.20, (2023, 3): 1.30, (2023, 4): 1.65,
        (2023, 5): 1.85, (2023, 6): 0.15, (2023, 7): 0.00, (2023, 8): 0.05,
        (2023, 9): 2.90, (2023, 10): 3.65, (2023, 11): 1.40, (2023, 12): 0.85,
        # 2024: Continuing drought broken by Tropical Storm Alberto in late June (June 19-21), dry Jul-Aug, fall pulses
        (2024, 1): 1.25, (2024, 2): 1.10, (2024, 3): 1.55, (2024, 4): 1.95,
        (2024, 5): 1.40, (2024, 6): 4.20, (2024, 7): 0.45, (2024, 8): 0.70,
        (2024, 9): 4.60, (2024, 10): 3.10, (2024, 11): 1.20, (2024, 12): 1.05,
    }

    np.random.seed(1983)  # Mateo Garza farm gauge seed
    start_date = datetime.date(2021, 1, 1)
    end_date = datetime.date(2024, 12, 31)
    dates = [start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    daily_rain = {}
    for (y, m), target in monthly_targets.items():
        m_dates = [d for d in dates if d.year == y and d.month == m]
        days_in_m = len(m_dates)
        if target <= 0.01:
            for d in m_dates:
                daily_rain[d] = 0.0
            continue

        if target > 4.0:
            n_events = np.random.randint(4, 7)
        elif target > 2.0:
            n_events = np.random.randint(3, 5)
        elif target > 0.8:
            n_events = np.random.randint(2, 4)
        else:
            n_events = np.random.randint(1, 3)

        event_days = list(np.random.choice(m_dates, size=min(n_events, days_in_m), replace=False))

        # Anchor specific authentic South Texas weather events:
        if y == 2024 and m == 6:
            event_days = [datetime.date(2024, 6, 19), datetime.date(2024, 6, 20), datetime.date(2024, 6, 21), datetime.date(2024, 6, 4)]
        elif y == 2021 and m == 5:
            event_days = [datetime.date(2021, 5, 11), datetime.date(2021, 5, 18), datetime.date(2021, 5, 19), datetime.date(2021, 5, 28), datetime.date(2021, 5, 3)]

        weights = np.random.dirichlet(np.ones(len(event_days)))
        event_amounts = weights * target

        for d in m_dates:
            daily_rain[d] = 0.0
        for ed, amt in zip(event_days, event_amounts):
            daily_rain[ed] = round(float(amt), 2)

    records = [{'date': d.isoformat(), 'precipitation': daily_rain[d]} for d in dates]
    return pd.DataFrame(records)

if __name__ == "__main__":
    df = generate_garza_farm_rainfall()
    out_path = Path("data/garza_farm_rainfall.csv")
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} daily records to {out_path.resolve()}")
    
    # Validation with preview_rainfall
    raw_bytes = out_path.read_bytes()
    preview = preview_rainfall(raw_bytes, "Garza Farm Rain Gauge", "San Patricio County, TX", "inches")
    print("BASIN Ingestion Validation:")
    print(f"- Expected Days: {preview.expected_days}")
    print(f"- Valid Days: {preview.valid_days}")
    print(f"- Missing Days: {preview.missing_days}")
    print(f"- Coverage: {preview.coverage_label}")
    print(f"- Original SHA256: {preview.original_sha256}")
    
    df['year'] = pd.to_datetime(df['date']).dt.year
    print("\nAnnual Rainfall Totals (inches):")
    print(df.groupby('year')['precipitation'].sum().round(2))
    
    df['month'] = pd.to_datetime(df['date']).dt.month
    print("\nSummer Flash Drought (Jun-Aug) Totals (inches):")
    print(df[df['month'].isin([6, 7, 8])].groupby('year')['precipitation'].sum().round(2))
