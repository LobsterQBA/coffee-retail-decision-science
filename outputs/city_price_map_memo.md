# City price map memo

## What changed

This version replaces the synthetic-only demo with a city-level public-data workflow:

- Starbucks Caffè Latte delivery-menu observations across 27 U.S. cities
- BEA/FRED-style Regional Price Parity features at the MSA level
- A map comparing observed delivery-menu prices with local price levels
- A simple price-vs-RPP model to identify cities priced above or below what local cost levels would predict

## Readout

- Average observed Caffè Latte delivery-menu price: `$5.63`
- Highest observed city: `Honolulu, HI` at `$6.35+`
- Lowest observed city: `Jefferson City, MO` at `$5.45+`
- Correlation between latte price and all-items RPP: `0.46` with R² `0.22`
- Correlation between latte price and housing RPP: `0.29` with R² `0.08`

## Interpretation

The result is directionally useful rather than definitive. Prices do move somewhat with local price levels, but the fit is not perfect. That is the interesting business signal: a city may look expensive because the whole metro is expensive, or because the observed Starbucks delivery-menu quote sits above what local cost level alone would predict.

## Caveat

The Starbucks observations are delivery-menu quotes from public Grubhub snippets, not official in-store Starbucks prices. Starbucks notes that delivery-app prices may be higher than posted store prices. For a production-quality study, the next step would be collecting multiple stores per city through a governed, repeatable price collection process.
