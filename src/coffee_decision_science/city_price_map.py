from __future__ import annotations

import json
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
MARPP_ZIP = DATA_DIR / "MARPP.zip"
MARPP_URL = "https://apps.bea.gov/regional/zip/MARPP.zip"


def ensure_bea_rpp_zip() -> None:
    if MARPP_ZIP.exists():
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading BEA Regional Price Parities data from {MARPP_URL}")
    urllib.request.urlretrieve(MARPP_URL, MARPP_ZIP)


def load_bea_rpp() -> pd.DataFrame:
    ensure_bea_rpp_zip()
    with zipfile.ZipFile(MARPP_ZIP) as archive:
        with archive.open("MARPP_MSA_2008_2024.csv") as f:
            raw = pd.read_csv(f)

    raw["cbsa_code"] = raw["GeoFIPS"].astype(str).str.replace('"', "", regex=False).str.strip().str.zfill(5)
    raw["metric"] = raw["Description"].astype(str).str.strip()
    latest_year = "2024"
    rpp = raw.pivot_table(index=["cbsa_code", "GeoName"], columns="metric", values=latest_year, aggfunc="first").reset_index()
    rpp = rpp.rename(
        columns={
            "RPPs: All items": "rpp_all_items",
            "RPPs: Services: Housing": "rpp_housing",
            "RPPs: Goods": "rpp_goods",
            "RPPs: Services: Other": "rpp_other_services",
            "RPPs: Services: Utilities": "rpp_utilities",
        }
    )
    return rpp


def fit_linear(x: pd.Series, y: pd.Series) -> dict[str, float]:
    keep = x.notna() & y.notna()
    x = x[keep].astype(float)
    y = y[keep].astype(float)
    slope, intercept = np.polyfit(x, y, 1)
    pred = slope * x + intercept
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot else 0
    corr = float(np.corrcoef(x, y)[0, 1]) if len(x) > 1 else 0
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r2": float(r2),
        "corr": corr,
        "n": int(len(x)),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = pd.read_csv(DATA_DIR / "starbucks_city_price_observations.csv", dtype={"cbsa_code": str})
    prices["cbsa_code"] = prices["cbsa_code"].str.zfill(5)
    rpp = load_bea_rpp()

    df = prices.merge(rpp, on="cbsa_code", how="left")
    df["latte_index_vs_sample_avg"] = df["latte_price"] / df["latte_price"].mean() * 100
    df["rpp_gap"] = df["latte_index_vs_sample_avg"] - df["rpp_all_items"]

    model = fit_linear(df["rpp_all_items"], df["latte_price"])
    df["predicted_latte_from_rpp"] = model["slope"] * df["rpp_all_items"] + model["intercept"]
    df["residual_vs_rpp_model"] = df["latte_price"] - df["predicted_latte_from_rpp"]

    housing_model = fit_linear(df["rpp_housing"], df["latte_price"])

    df = df.sort_values("latte_price", ascending=False)
    df.to_csv(OUTPUT_DIR / "city_price_index.csv", index=False)

    summary = {
        "city_count": int(len(df)),
        "avg_latte_price": round(float(df["latte_price"].mean()), 2),
        "min_latte": {
            "city": df.sort_values("latte_price").iloc[0]["city"],
            "state": df.sort_values("latte_price").iloc[0]["state"],
            "price": float(df.sort_values("latte_price").iloc[0]["latte_price"]),
        },
        "max_latte": {
            "city": df.iloc[0]["city"],
            "state": df.iloc[0]["state"],
            "price": float(df.iloc[0]["latte_price"]),
        },
        "rpp_model": model,
        "housing_model": housing_model,
        "largest_positive_residual": df.sort_values("residual_vs_rpp_model", ascending=False).head(5)[
            ["city", "state", "latte_price", "rpp_all_items", "residual_vs_rpp_model"]
        ].to_dict("records"),
        "largest_negative_residual": df.sort_values("residual_vs_rpp_model").head(5)[
            ["city", "state", "latte_price", "rpp_all_items", "residual_vs_rpp_model"]
        ].to_dict("records"),
    }

    payload = {
        "summary": summary,
        "cities": json.loads(df.to_json(orient="records")),
        "sources": [
            {
                "name": "Starbucks delivery caveat",
                "url": "https://www.starbucks.com/stores-and-ordering/",
                "note": "Starbucks states delivery-app prices may be higher than store/marked prices.",
            },
            {
                "name": "BEA Regional Price Parities",
                "url": "https://www.bea.gov/data/prices-inflation/regional-price-parities-state-and-metro-area",
                "note": "RPP measures regional price-level differences vs. the national level.",
            },
            {
                "name": "BEA MARPP downloadable data",
                "url": MARPP_URL,
                "note": "Downloaded MSA-level RPP CSV used for 2024 all-items and housing indexes.",
            },
            {
                "name": "Grubhub Starbucks delivery menu snippets",
                "url": "https://www.grubhub.com/",
                "note": "City-level Caffè Latte observations are manually curated from public search snippets linking to Grubhub restaurant pages.",
            },
            {
                "name": "TradingPedia Starbucks affordability benchmark",
                "url": "https://www.tradingpedia.com/forex-brokers/sipping-through-the-salary-gap-starbucks-coffee-costs-across-the-united-states/",
                "note": "Used as an external sanity check on U.S. Starbucks price dispersion and source limitations.",
            },
        ],
    }
    (OUTPUT_DIR / "city_price_index.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "city_price_index.js").write_text(
        "window.CITY_PRICE_INDEX = " + json.dumps(payload, indent=2) + ";\n",
        encoding="utf-8",
    )

    memo = f"""# City price map memo

## What changed

This version replaces the synthetic-only demo with a city-level public-data workflow:

- Starbucks Caffè Latte delivery-menu observations across {summary['city_count']} U.S. cities
- BEA/FRED-style Regional Price Parity features at the MSA level
- A map comparing observed delivery-menu prices with local price levels
- A simple price-vs-RPP model to identify cities priced above or below what local cost levels would predict

## Readout

- Average observed Caffè Latte delivery-menu price: `${summary['avg_latte_price']}`
- Highest observed city: `{summary['max_latte']['city']}, {summary['max_latte']['state']}` at `${summary['max_latte']['price']:.2f}+`
- Lowest observed city: `{summary['min_latte']['city']}, {summary['min_latte']['state']}` at `${summary['min_latte']['price']:.2f}+`
- Correlation between latte price and all-items RPP: `{model['corr']:.2f}` with R² `{model['r2']:.2f}`
- Correlation between latte price and housing RPP: `{housing_model['corr']:.2f}` with R² `{housing_model['r2']:.2f}`

## Interpretation

The result is directionally useful rather than definitive. Prices do move somewhat with local price levels, but the fit is not perfect. That is the interesting business signal: a city may look expensive because the whole metro is expensive, or because the observed Starbucks delivery-menu quote sits above what local cost level alone would predict.

## Caveat

The Starbucks observations are delivery-menu quotes from public Grubhub snippets, not official in-store Starbucks prices. Starbucks notes that delivery-app prices may be higher than posted store prices. For a production-quality study, the next step would be collecting multiple stores per city through a governed, repeatable price collection process.
"""
    (OUTPUT_DIR / "city_price_map_memo.md").write_text(memo, encoding="utf-8")
    print(f"Wrote {OUTPUT_DIR / 'city_price_index.csv'}")
    print(f"Wrote {OUTPUT_DIR / 'city_price_index.json'}")
    print(f"RPP model corr={model['corr']:.3f}, r2={model['r2']:.3f}")


if __name__ == "__main__":
    main()
