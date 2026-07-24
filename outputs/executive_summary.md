# Executive summary

## Recommendation

Prioritize targeted promotions for high-elasticity categories in high-walkability stores, then monitor weekly forecast error and margin impact before scaling the playbook broadly.

## Key evidence

- `whole_bean` is the most price-sensitive category in the synthetic panel, with estimated elasticity of `-2.53`.
- `food` is less price-sensitive, with estimated elasticity of `-1.40`, suggesting discounts are less likely to pay back through volume alone.
- The top next-cycle recommendation is `S012` / `cold_beverage`, with an expected incremental margin score of `93.9`.
- The difference-in-differences validation estimates promoted cold beverages generated `41.5` incremental units per store-category-day during the post period.
- Average weekly model MAPE is `15.1%`. Weeks above the review threshold should trigger diagnostics before the output is used for operating decisions.

## Caveats

This project uses synthetic data, so the point is workflow quality rather than factual Starbucks performance. In production, I would replace the synthetic source with governed transaction, promotion, item, store, and weather tables, then validate elasticity stability by region, season, and channel.

## Next production step

Move the SQL feature layer into a shared analytics repo, schedule the pipeline, and expose model monitoring plus recommendation adoption in Tableau or Power BI.
