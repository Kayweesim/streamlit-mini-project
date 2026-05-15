"""
PSA Port Operations — Power BI Data Generator
Run this script to produce 5 CSV files for your Power BI dashboard.
Usage: python generate_pbi_data.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

rng = np.random.default_rng(42)
OUTPUT_DIR = "psa_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Constants ──────────────────────────────────────────────────────────────────
TERMINALS = [
    "Tanjong Pagar", "Keppel", "Brani",
    "Pasir Panjang T1-2", "Pasir Panjang T3-4", "Tuas"
]
TERMINAL_BERTHS = {
    "Tanjong Pagar": 6, "Keppel": 8, "Brani": 4,
    "Pasir Panjang T1-2": 10, "Pasir Panjang T3-4": 10, "Tuas": 14
}
SHIPPING_LINES = [
    "Maersk", "MSC", "CMA CGM", "COSCO", "Evergreen",
    "Hapag-Lloyd", "ONE", "Yang Ming", "HMM", "PIL"
]
VESSEL_TYPES = ["Container", "Bulk Carrier", "Tanker", "RORO", "General Cargo"]
ROUTES = [
    "Singapore–China", "Singapore–Europe", "Singapore–US East",
    "Singapore–US West", "Singapore–India", "Singapore–SE Asia",
    "Singapore–Middle East", "Singapore–Japan", "Singapore–Korea"
]

# ── 1. Daily Throughput (2 years of daily TEU data) ────────────────────────────
print("Generating daily_throughput.csv ...")
dates = pd.date_range(start="2023-01-01", end="2024-12-31", freq="D")
n = len(dates)
base = 85_000
trend = np.linspace(0, 12_000, n)
seasonality = 7_000 * np.sin(2 * np.pi * np.arange(n) / 365 - 0.5)
noise = rng.normal(0, 2_800, n)
# Red Sea disruption boost mid-2024 (rows ~540–730)
disruption = np.where((np.arange(n) >= 540) & (np.arange(n) <= 730), 6_000, 0)
teu = (base + trend + seasonality + noise + disruption).clip(60_000, 130_000).astype(int)

throughput_df = pd.DataFrame({
    "Date": dates.strftime("%Y-%m-%d"),
    "TEU": teu,
    "Terminal": rng.choice(TERMINALS, n),
    "Month": dates.month,
    "Year": dates.year,
    "Quarter": dates.quarter,
    "DayOfWeek": dates.day_name(),
    "IsWeekend": dates.dayofweek >= 5,
})
throughput_df.to_csv(f"{OUTPUT_DIR}/daily_throughput.csv", index=False)
print(f"  → {len(throughput_df)} rows")

# ── 2. Vessel Arrivals (individual vessel-level records) ──────────────────────
print("Generating vessel_arrivals.csv ...")
vessel_rows = []
vessel_id = 1000

for single_date in pd.date_range(start="2023-01-01", end="2024-12-31", freq="D"):
    n_vessels = int(rng.integers(18, 36))
    for _ in range(n_vessels):
        terminal = rng.choice(TERMINALS)
        arrival_hour = rng.integers(0, 24)
        turnaround = round(float(rng.uniform(12, 38)), 1)
        departure_hour = (arrival_hour + int(turnaround)) % 24
        vessel_rows.append({
            "VesselID": f"V{vessel_id:05d}",
            "Date": single_date.strftime("%Y-%m-%d"),
            "Terminal": terminal,
            "ShippingLine": rng.choice(SHIPPING_LINES),
            "VesselType": rng.choice(
                VESSEL_TYPES,
                p=[0.52, 0.16, 0.22, 0.06, 0.04]
            ),
            "Route": rng.choice(ROUTES),
            "ArrivalHour": int(arrival_hour),
            "TurnaroundHrs": turnaround,
            "DepartureHour": int(departure_hour),
            "TEUCapacity": int(rng.choice([8_000, 12_000, 14_500, 20_000, 24_000])),
            "TEULoaded": int(rng.uniform(0.68, 0.97) * rng.choice([8_000, 12_000, 14_500, 20_000, 24_000])),
        })
        vessel_id += 1

vessels_df = pd.DataFrame(vessel_rows)
vessels_df["UtilisationRate"] = (vessels_df["TEULoaded"] / vessels_df["TEUCapacity"]).clip(0, 1).round(3)
vessels_df.to_csv(f"{OUTPUT_DIR}/vessel_arrivals.csv", index=False)
print(f"  → {len(vessels_df)} rows")

# ── 3. Berth Status (monthly utilisation per terminal) ────────────────────────
print("Generating berth_status.csv ...")
berth_rows = []
for period in pd.date_range(start="2023-01-01", end="2024-12-31", freq="MS"):
    for terminal in TERMINALS:
        base_util = {"Tanjong Pagar": 0.78, "Keppel": 0.82, "Brani": 0.75,
                     "Pasir Panjang T1-2": 0.88, "Pasir Panjang T3-4": 0.85, "Tuas": 0.70}[terminal]
        seasonal_bump = 0.04 * np.sin(2 * np.pi * period.month / 12)
        # 2024 Red Sea surge
        disruption_bump = 0.06 if (period.year == 2024 and period.month >= 7) else 0
        util = float(np.clip(base_util + seasonal_bump + disruption_bump + rng.normal(0, 0.02), 0.55, 0.99))
        berths = TERMINAL_BERTHS[terminal]
        berth_rows.append({
            "YearMonth": period.strftime("%Y-%m"),
            "Year": period.year,
            "Month": period.month,
            "Terminal": terminal,
            "TotalBerths": berths,  
            "OccupiedBerths": round(util * berths, 1),
            "UtilisationRate": round(util, 3),
            "AvgWaitingTimeHrs": round(float(rng.uniform(1.5, 8.0) * (1 + util)), 1),
            "MaintenanceBerths": int(rng.integers(0, 2)),
        })

berth_df = pd.DataFrame(berth_rows)
berth_df["AvailableBerths"] = berth_df["TotalBerths"] - berth_df["OccupiedBerths"].round() - berth_df["MaintenanceBerths"]
berth_df.to_csv(f"{OUTPUT_DIR}/berth_status.csv", index=False)
print(f"  → {len(berth_df)} rows")

# ── 4. Crane Performance (daily productivity per terminal) ────────────────────
print("Generating crane_performance.csv ...")
crane_rows = []
for single_date in pd.date_range(start="2023-01-01", end="2024-12-31", freq="D"):
    for terminal in TERMINALS:
        n_cranes = {"Tanjong Pagar": 18, "Keppel": 24, "Brani": 12,
                    "Pasir Panjang T1-2": 30, "Pasir Panjang T3-4": 30, "Tuas": 38}[terminal]
        active_cranes = int(rng.integers(max(1, n_cranes - 4), n_cranes + 1))
        moves_per_hour = round(float(rng.uniform(23, 36)), 1)
        downtime_pct = round(float(rng.uniform(0.02, 0.12)), 3)
        crane_rows.append({
            "Date": single_date.strftime("%Y-%m-%d"),
            "Terminal": terminal,
            "TotalCranes": n_cranes,
            "ActiveCranes": active_cranes,
            "MovesPerHour": moves_per_hour,
            "DowntimePct": downtime_pct,
            "TotalMovesDay": int(active_cranes * moves_per_hour * 20),  # ~20 productive hrs
            "Month": single_date.month,
            "Year": single_date.year,
        })

crane_df = pd.DataFrame(crane_rows)
crane_df.to_csv(f"{OUTPUT_DIR}/crane_performance.csv", index=False)
print(f"  → {len(crane_df)} rows")

# ── 5. Trade Route Summary (monthly, by route) ────────────────────────────────
print("Generating trade_routes.csv ...")
route_rows = []
route_base_teu = {
    "Singapore–China": 420_000, "Singapore–Europe": 280_000,
    "Singapore–US East": 180_000, "Singapore–US West": 160_000,
    "Singapore–India": 170_000, "Singapore–SE Asia": 310_000,
    "Singapore–Middle East": 140_000, "Singapore–Japan": 120_000,
    "Singapore–Korea": 110_000
}
for period in pd.date_range(start="2023-01-01", end="2024-12-31", freq="MS"):
    for route, base_teu in route_base_teu.items():
        growth = 1.04 if period.year == 2024 else 1.0
        seasonal = 1 + 0.08 * np.sin(2 * np.pi * period.month / 12)
        # US route dip in 2024 H2 due to tariff uncertainty
        tariff_impact = 0.92 if ("US" in route and period.year == 2024 and period.month >= 8) else 1.0
        teu_vol = int(base_teu * growth * seasonal * tariff_impact + rng.normal(0, base_teu * 0.03))
        route_rows.append({
            "YearMonth": period.strftime("%Y-%m"),
            "Year": period.year,
            "Month": period.month,
            "Route": route,
            "TEU": max(teu_vol, 0),
            "AvgFreightRateUSD": round(float(rng.uniform(800, 3200)), 0),
            "ShipCount": int(rng.integers(40, 180)),
            "OnTimeDeliveryPct": round(float(rng.uniform(0.78, 0.97)), 3),
        })

routes_df = pd.DataFrame(route_rows)
routes_df.to_csv(f"{OUTPUT_DIR}/trade_routes.csv", index=False)
print(f"  → {len(routes_df)} rows")

# ── Summary ────────────────────────────────────────────────────────────────────
print("\n✅ All files written to ./psa_data/")
print("Files:")
for f in sorted(os.listdir(OUTPUT_DIR)):
    size = os.path.getsize(f"{OUTPUT_DIR}/{f}") // 1024
    print(f"  {f:35s} {size:>4} KB")
print("\nLoad all 5 CSVs into Power BI using Get Data → Text/CSV")
