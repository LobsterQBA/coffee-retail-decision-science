# Coffee Retail Decision Science

Proof-of-work project for a Data Scientist, Data & Analytics role focused on analytically ready datasets, repeatable modeling pipelines, model monitoring, visualization, and decision support.

This project uses synthetic coffee-retail data. It is inspired by common retail analytics problems, not by proprietary Starbucks data.

## Business question

How should a coffee retailer choose weekly promotions and staffing priorities across stores when demand depends on price, seasonality, weather, local store context, and product category?

## Why this is relevant to the role

The Starbucks role asks for someone who can:

- extract, shape, and validate data with SQL
- build repeatable Python/R pipelines for model training and outputs
- communicate methodology and business implications clearly
- monitor model performance through dashboards or reporting
- apply elasticity, causal inference, and optimization for decision support

This repo demonstrates that workflow end to end:

1. Generate synthetic store, calendar, promotion, and sales data.
2. Use SQL to create an analytically ready daily store-category panel.
3. Estimate demand elasticity with a log-log model and uncertainty bands.
4. Run a simple promotion lift validation using difference-in-differences.
5. Recommend promotions with an optimization-style scoring heuristic.
6. Produce decision-ready charts and model monitoring outputs.

## Project structure

```text
.
├── data/                         # Generated synthetic data and local SQLite database
├── outputs/                      # Generated charts and model artifacts
├── sql/
│   ├── create_model_features.sql # SQL transformation into modeling table
│   └── monitoring_checks.sql     # SQL checks for model output monitoring
├── src/coffee_decision_science/
│   ├── generate_synthetic_data.py
│   └── pipeline.py
├── requirements.txt
└── README.md
```

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.coffee_decision_science.generate_synthetic_data
python -m src.coffee_decision_science.pipeline
```

If you already have `pandas`, `numpy`, and `matplotlib` installed, you can run the two Python commands directly.

## Outputs

After running the pipeline, the `outputs/` folder contains:

- `elasticity_by_category.csv` — estimated category-level price elasticity with approximate uncertainty bounds
- `promotion_recommendations.csv` — next-week promotion recommendations ranked by expected incremental margin
- `model_monitoring.csv` — weekly prediction-error monitoring table
- `elasticity_by_category.png` — business-readable elasticity chart
- `promotion_recommendations.png` — top recommended promotions
- `model_monitoring.png` — monitoring view for model performance
- `executive_summary.md` — short decision memo suitable for sharing

## Frontend dashboard

The repo includes a static `index.html` dashboard designed for Vercel or GitHub Pages. It presents the project as a recruiter- and hiring-manager-readable proof of work:

- KPI cards for records, elasticity, promotion lift, and monitoring error
- charts for elasticity, promotion recommendations, and model monitoring
- links to the executive memo, methodology, SQL, and pipeline code

To preview locally:

```bash
python3 -m http.server 4173
```

Then open `http://localhost:4173`.

## Methodology

### SQL feature layer

The modeling table is built in SQL at the daily store-category level. It joins transaction, store, and calendar data, then creates:

- demand, revenue, and gross margin outcomes
- price and discount features
- holiday, weekend, weather, and seasonality controls
- rolling trailing demand baselines

### Demand model

The model estimates:

```text
log(units_sold) ~ log(price) + promo_depth + weather + holiday + weekend + store type + category
```

The `log(price)` coefficient is interpreted as price elasticity. Category-specific elasticity is estimated by fitting the same controlled model separately by category. Uncertainty bands are generated with bootstrap resampling.

### Causal validation

The project includes a lightweight difference-in-differences validation:

```text
(treated after - treated before) - (control after - control before)
```

This checks whether promoted store-category pairs saw incremental demand above their own baseline and the concurrent control group.

### Decision support

Promotion candidates are scored using:

```text
expected incremental units × expected margin per unit - discount cost
```

The recommendation intentionally balances volume lift with margin tradeoffs, rather than maximizing units sold alone.

## What I would productionize next

- Replace synthetic data with governed internal tables.
- Move the SQL feature layer into dbt or a shared analytics repo.
- Add Airflow/Databricks scheduling and data-quality checks.
- Use Bayesian hierarchical elasticity to borrow strength across sparse store-category cells.
- Add a Tableau/Power BI dashboard for elasticity, recommendations, and model monitoring.
- Track drift in elasticity, forecast error, promo mix, and recommendation adoption.

## Applicant note

I built this as a compact demonstration of the kind of data science workflow I would bring to a retail analytics team: start from a decision, make the data reproducible, validate the model, and translate outputs into actions that operators and business partners can use.
