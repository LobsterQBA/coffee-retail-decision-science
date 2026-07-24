from __future__ import annotations

import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
SQL_DIR = ROOT / "sql"
DB_PATH = DATA_DIR / "coffee_retail.db"


def load_csvs_to_sqlite() -> None:
    con = sqlite3.connect(DB_PATH)
    for table_name in ["stores", "calendar", "transactions"]:
        df = pd.read_csv(DATA_DIR / f"{table_name}.csv")
        df.to_sql(table_name, con, if_exists="replace", index=False)

    with open(SQL_DIR / "create_model_features.sql", encoding="utf-8") as f:
        con.executescript(f.read())
    con.close()


def design_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    model_df = df.copy()
    model_df["log_units"] = np.log(model_df["units_sold"].clip(lower=1))
    model_df["log_price"] = np.log(model_df["price"].clip(lower=0.1))
    base_cols = [
        "log_price",
        "temperature_f",
        "precipitation_in",
        "is_weekend",
        "is_holiday",
        "walkability_score",
    ]
    dummies = pd.get_dummies(model_df[["store_type", "region"]], drop_first=True, dtype=float)
    x = pd.concat([model_df[base_cols].astype(float), dummies], axis=1)
    x.insert(0, "intercept", 1.0)
    return x, model_df["log_units"]


def fit_ols(x: pd.DataFrame, y: pd.Series) -> pd.Series:
    beta, *_ = np.linalg.lstsq(x.to_numpy(dtype=float), y.to_numpy(dtype=float), rcond=None)
    return pd.Series(beta, index=x.columns)


def bootstrap_elasticity(df: pd.DataFrame, rng: np.random.Generator, n_bootstrap: int = 120) -> pd.DataFrame:
    rows = []
    for category, group in df.groupby("category"):
        estimates = []
        for _ in range(n_bootstrap):
            sample = group.sample(frac=1, replace=True, random_state=int(rng.integers(0, 1_000_000)))
            x, y = design_matrix(sample)
            estimates.append(fit_ols(x, y)["log_price"])

        full_x, full_y = design_matrix(group)
        beta = fit_ols(full_x, full_y)
        rows.append(
            {
                "category": category,
                "elasticity": beta["log_price"],
                "lower_95": np.percentile(estimates, 2.5),
                "upper_95": np.percentile(estimates, 97.5),
                "observations": len(group),
            }
        )
    return pd.DataFrame(rows).sort_values("elasticity")


def score_model(df: pd.DataFrame) -> pd.DataFrame:
    scored = []
    for category, group in df.groupby("category"):
        x, y = design_matrix(group)
        beta = fit_ols(x, y)
        predicted = np.exp(x @ beta)
        part = group.copy()
        part["predicted_units"] = predicted
        part["absolute_error"] = (part["units_sold"] - part["predicted_units"]).abs()
        scored.append(part)
    return pd.concat(scored, ignore_index=True)


def promotion_lift_check(df: pd.DataFrame) -> pd.DataFrame:
    campaign = df[
        (df["category"] == "cold_beverage")
        & (df["date"] >= "2025-06-01")
        & (df["date"] <= "2025-06-30")
    ].copy()
    treated_stores = {f"S{i:03d}" for i in range(1, 13)}
    campaign["period"] = np.where(campaign["date"] >= "2025-06-16", "after", "before")
    campaign["treated"] = campaign["store_id"].isin(treated_stores).astype(int)

    grouped = (
        campaign.groupby(["treated", "period"], as_index=False)
        .agg(avg_units=("units_sold", "mean"), avg_margin=("gross_margin", "mean"), rows=("units_sold", "size"))
    )

    pivot = grouped.pivot(index="treated", columns="period", values="avg_units")
    lift_units = (pivot.loc[1, "after"] - pivot.loc[1, "before"]) - (pivot.loc[0, "after"] - pivot.loc[0, "before"])
    return grouped.assign(diff_in_diff_units=np.where((grouped["treated"] == 1) & (grouped["period"] == "after"), lift_units, np.nan))


def recommend_promotions(features: pd.DataFrame, elasticity: pd.DataFrame) -> pd.DataFrame:
    recent = features[features["date"] >= "2025-11-01"].copy()
    category_inputs = (
        recent.groupby(["store_id", "region", "store_type", "category"], as_index=False)
        .agg(
            baseline_units=("baseline_units", "mean"),
            price=("base_price", "mean"),
            unit_cost=("unit_cost", "mean"),
            recent_margin=("gross_margin", "mean"),
            walkability_score=("walkability_score", "mean"),
        )
    )
    category_inputs = category_inputs.merge(elasticity[["category", "elasticity"]], on="category", how="left")
    category_inputs["candidate_discount"] = np.where(category_inputs["category"].isin(["cold_beverage", "whole_bean"]), 0.15, 0.10)
    category_inputs["expected_lift_pct"] = (1 - category_inputs["candidate_discount"]) ** category_inputs["elasticity"] - 1
    category_inputs["expected_incremental_units"] = category_inputs["baseline_units"] * category_inputs["expected_lift_pct"]
    discounted_price = category_inputs["price"] * (1 - category_inputs["candidate_discount"])
    category_inputs["expected_incremental_margin"] = (
        category_inputs["expected_incremental_units"] * (discounted_price - category_inputs["unit_cost"])
        - category_inputs["baseline_units"] * category_inputs["price"] * category_inputs["candidate_discount"] * 0.08
    )
    category_inputs["recommendation_score"] = category_inputs["expected_incremental_margin"] * (
        1 + (category_inputs["walkability_score"] - category_inputs["walkability_score"].mean()) / 250
    )
    return category_inputs.sort_values("recommendation_score", ascending=False).head(15)


def run_monitoring_sql(scored: pd.DataFrame) -> pd.DataFrame:
    con = sqlite3.connect(DB_PATH)
    scored.to_sql("model_scored", con, if_exists="replace", index=False)
    with open(SQL_DIR / "monitoring_checks.sql", encoding="utf-8") as f:
        monitoring = pd.read_sql_query(f.read(), con)
    con.close()
    return monitoring


def plot_elasticity(elasticity: pd.DataFrame) -> None:
    plt.figure(figsize=(9, 5.4))
    y_pos = np.arange(len(elasticity))
    err = np.vstack(
        [
            elasticity["elasticity"] - elasticity["lower_95"],
            elasticity["upper_95"] - elasticity["elasticity"],
        ]
    )
    plt.barh(y_pos, elasticity["elasticity"], xerr=err, color="#4E79A7", alpha=0.9)
    plt.axvline(0, color="#333333", linewidth=1)
    plt.yticks(y_pos, elasticity["category"])
    plt.xlabel("Estimated price elasticity")
    plt.title("Category-level demand elasticity")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "elasticity_by_category.png", dpi=180)
    plt.close()


def plot_recommendations(recommendations: pd.DataFrame) -> None:
    top = recommendations.head(10).copy()
    labels = top["store_id"] + " · " + top["category"]
    plt.figure(figsize=(10, 5.8))
    plt.barh(labels[::-1], top["recommendation_score"][::-1], color="#59A14F")
    plt.xlabel("Expected incremental margin score")
    plt.title("Top promotion recommendations for next planning cycle")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "promotion_recommendations.png", dpi=180)
    plt.close()


def plot_monitoring(monitoring: pd.DataFrame) -> None:
    weekly = monitoring.groupby("week_start", as_index=False).agg(mape=("mape", "mean"))
    plt.figure(figsize=(10, 4.8))
    plt.plot(pd.to_datetime(weekly["week_start"]), weekly["mape"], color="#F28E2B", linewidth=2)
    plt.axhline(0.12, color="#555555", linestyle="--", linewidth=1, label="12% review threshold")
    plt.ylabel("MAPE")
    plt.title("Weekly model monitoring")
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "model_monitoring.png", dpi=180)
    plt.close()


def write_summary(elasticity: pd.DataFrame, recommendations: pd.DataFrame, did: pd.DataFrame, monitoring: pd.DataFrame) -> None:
    most_elastic = elasticity.assign(abs_elasticity=elasticity["elasticity"].abs()).sort_values("abs_elasticity", ascending=False).iloc[0]
    least_elastic = elasticity.assign(abs_elasticity=elasticity["elasticity"].abs()).sort_values("abs_elasticity").iloc[0]
    top_rec = recommendations.iloc[0]
    did_lift = did["diff_in_diff_units"].dropna()
    avg_mape = monitoring["mape"].mean()

    summary = f"""# Executive summary

## Recommendation

Prioritize targeted promotions for high-elasticity categories in high-walkability stores, then monitor weekly forecast error and margin impact before scaling the playbook broadly.

## Key evidence

- `{most_elastic['category']}` is the most price-sensitive category in the synthetic panel, with estimated elasticity of `{most_elastic['elasticity']:.2f}`.
- `{least_elastic['category']}` is less price-sensitive, with estimated elasticity of `{least_elastic['elasticity']:.2f}`, suggesting discounts are less likely to pay back through volume alone.
- The top next-cycle recommendation is `{top_rec['store_id']}` / `{top_rec['category']}`, with an expected incremental margin score of `{top_rec['recommendation_score']:.1f}`.
- The difference-in-differences validation estimates promoted cold beverages generated `{did_lift.iloc[0]:.1f}` incremental units per store-category-day during the post period.
- Average weekly model MAPE is `{avg_mape:.1%}`. Weeks above the review threshold should trigger diagnostics before the output is used for operating decisions.

## Caveats

This project uses synthetic data, so the point is workflow quality rather than factual Starbucks performance. In production, I would replace the synthetic source with governed transaction, promotion, item, store, and weather tables, then validate elasticity stability by region, season, and channel.

## Next production step

Move the SQL feature layer into a shared analytics repo, schedule the pipeline, and expose model monitoring plus recommendation adoption in Tableau or Power BI.
"""
    (OUTPUT_DIR / "executive_summary.md").write_text(summary, encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    load_csvs_to_sqlite()

    con = sqlite3.connect(DB_PATH)
    features = pd.read_sql_query("SELECT * FROM model_features", con)
    con.close()

    rng = np.random.default_rng(20260724)
    elasticity = bootstrap_elasticity(features, rng)
    scored = score_model(features)
    recommendations = recommend_promotions(features, elasticity)
    did = promotion_lift_check(features)
    monitoring = run_monitoring_sql(scored)

    features.to_csv(OUTPUT_DIR / "model_features_sample.csv", index=False)
    elasticity.to_csv(OUTPUT_DIR / "elasticity_by_category.csv", index=False)
    recommendations.to_csv(OUTPUT_DIR / "promotion_recommendations.csv", index=False)
    did.to_csv(OUTPUT_DIR / "promo_diff_in_diff.csv", index=False)
    monitoring.to_csv(OUTPUT_DIR / "model_monitoring.csv", index=False)

    plot_elasticity(elasticity)
    plot_recommendations(recommendations)
    plot_monitoring(monitoring)
    write_summary(elasticity, recommendations, did, monitoring)

    print("Pipeline complete. See outputs/ for charts, tables, and executive_summary.md.")


if __name__ == "__main__":
    main()
