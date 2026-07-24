from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


def make_stores(rng: np.random.Generator, n_stores: int = 36) -> pd.DataFrame:
    regions = ["Seattle", "Bellevue", "Tacoma", "Redmond"]
    store_types = ["urban_core", "drive_thru", "suburban", "campus"]

    rows = []
    for store_id in range(1, n_stores + 1):
        region = rng.choice(regions, p=[0.42, 0.22, 0.20, 0.16])
        store_type = rng.choice(store_types, p=[0.34, 0.28, 0.26, 0.12])
        rows.append(
            {
                "store_id": f"S{store_id:03d}",
                "region": region,
                "store_type": store_type,
                "walkability_score": round(float(rng.normal(70, 12)), 1),
                "avg_ticket": round(float(rng.normal(9.25, 1.4)), 2),
            }
        )
    return pd.DataFrame(rows)


def make_calendar() -> pd.DataFrame:
    dates = pd.date_range("2025-01-01", "2025-12-31", freq="D")
    holidays = {
        "2025-01-01",
        "2025-02-17",
        "2025-05-26",
        "2025-07-04",
        "2025-09-01",
        "2025-11-27",
        "2025-12-25",
    }
    calendar = pd.DataFrame({"date": dates})
    calendar["day_of_week"] = calendar["date"].dt.day_name()
    calendar["is_weekend"] = calendar["date"].dt.dayofweek.isin([5, 6]).astype(int)
    calendar["is_holiday"] = calendar["date"].dt.strftime("%Y-%m-%d").isin(holidays).astype(int)
    calendar["week_start"] = calendar["date"] - pd.to_timedelta(calendar["date"].dt.dayofweek, unit="D")
    calendar["month"] = calendar["date"].dt.month
    return calendar


def seasonal_temperature(rng: np.random.Generator, date: pd.Timestamp) -> float:
    day_of_year = date.dayofyear
    seasonal = 55 + 18 * np.sin(2 * np.pi * (day_of_year - 105) / 365)
    return round(float(seasonal + rng.normal(0, 6)), 1)


def make_transactions(
    rng: np.random.Generator,
    stores: pd.DataFrame,
    calendar: pd.DataFrame,
) -> pd.DataFrame:
    categories = {
        "espresso": {"base_price": 5.75, "unit_cost": 1.65, "base_units": 75, "elasticity": -1.15},
        "cold_beverage": {"base_price": 6.25, "unit_cost": 1.85, "base_units": 68, "elasticity": -1.45},
        "tea": {"base_price": 4.95, "unit_cost": 1.25, "base_units": 34, "elasticity": -1.05},
        "food": {"base_price": 7.25, "unit_cost": 3.45, "base_units": 42, "elasticity": -0.85},
        "whole_bean": {"base_price": 14.95, "unit_cost": 6.25, "base_units": 13, "elasticity": -1.70},
    }

    store_type_multiplier = {
        "urban_core": 1.18,
        "drive_thru": 1.10,
        "suburban": 0.92,
        "campus": 0.78,
    }
    category_temp_effect = {
        "espresso": -0.004,
        "cold_beverage": 0.018,
        "tea": -0.006,
        "food": 0.001,
        "whole_bean": -0.002,
    }

    rows = []
    for _, store in stores.iterrows():
        store_noise = rng.normal(1.0, 0.08)
        for _, cal in calendar.iterrows():
            temp = seasonal_temperature(rng, cal["date"])
            precipitation = max(0, rng.gamma(1.2, 0.07) - 0.04)
            for category, cfg in categories.items():
                promo_roll = rng.random()
                promo_depth = 0.0
                store_number = int(store["store_id"].replace("S", ""))
                is_cold_drink_campaign = (
                    category == "cold_beverage"
                    and store_number <= 12
                    and pd.Timestamp("2025-06-16") <= cal["date"] <= pd.Timestamp("2025-06-30")
                )
                if is_cold_drink_campaign:
                    promo_depth = 0.20
                elif category in {"cold_beverage", "food"} and cal["month"] in [5, 6, 7, 8] and promo_roll < 0.15:
                    promo_depth = float(rng.choice([0.10, 0.15, 0.20]))
                elif promo_roll < 0.07:
                    promo_depth = float(rng.choice([0.10, 0.15]))

                price = cfg["base_price"] * (1 - promo_depth)
                weekend_lift = 1.12 if cal["is_weekend"] else 1.0
                holiday_lift = 0.82 if cal["is_holiday"] else 1.0
                weather_lift = 1 + category_temp_effect[category] * (temp - 55) - 0.08 * precipitation
                price_lift = (price / cfg["base_price"]) ** cfg["elasticity"]
                promo_visibility_lift = 1 + (0.10 if promo_depth > 0 else 0)
                expected_units = (
                    cfg["base_units"]
                    * store_type_multiplier[store["store_type"]]
                    * store_noise
                    * weekend_lift
                    * holiday_lift
                    * weather_lift
                    * price_lift
                    * promo_visibility_lift
                )
                units_sold = max(1, int(rng.poisson(max(1, expected_units))))
                rows.append(
                    {
                        "date": cal["date"].strftime("%Y-%m-%d"),
                        "store_id": store["store_id"],
                        "category": category,
                        "units_sold": units_sold,
                        "price": round(price, 2),
                        "base_price": cfg["base_price"],
                        "unit_cost": cfg["unit_cost"],
                        "discount_pct": promo_depth,
                        "temperature_f": temp,
                        "precipitation_in": round(float(precipitation), 3),
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20260724)
    stores = make_stores(rng)
    calendar = make_calendar()
    transactions = make_transactions(rng, stores, calendar)

    stores.to_csv(DATA_DIR / "stores.csv", index=False)
    calendar.assign(date=calendar["date"].dt.strftime("%Y-%m-%d"), week_start=calendar["week_start"].dt.strftime("%Y-%m-%d")).to_csv(
        DATA_DIR / "calendar.csv", index=False
    )
    transactions.to_csv(DATA_DIR / "transactions.csv", index=False)

    print(f"Wrote {len(stores):,} stores, {len(calendar):,} calendar rows, and {len(transactions):,} transaction rows.")


if __name__ == "__main__":
    main()
