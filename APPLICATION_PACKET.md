# Application packet: Starbucks Data Scientist, Data & Analytics

## Positioning

This role is not just asking for modeling. It is asking for a data scientist who can work inside a shared analytics environment, turn messy business data into governed model-ready tables, validate model outputs, and communicate recommendations that business partners can adopt.

My strongest angle for this role:

- Retail/marketplace demand forecasting from SevenRooms / DoorDash client work
- SQL, Spark, Databricks, Azure SQL, and repeatable pipeline experience from WPP
- Marketing mix modeling, ROI measurement, A/B testing, and campaign analytics from Xiaomi
- Strong bridge between machine learning implementation and stakeholder-facing decision support

## Proof-of-work project summary

I built a compact coffee-retail decision science workflow that mirrors the responsibilities in the job description. The newest version starts with a public-data pricing map:

- City-level Starbucks Caffè Latte delivery-menu observations across selected U.S. cities
- BEA metro-area Regional Price Parities joined as local price-level features
- Interactive map showing where observed quotes sit above or below a local-cost-implied benchmark
- Scatter plot and outlier table to communicate whether price variation appears aligned with local cost pressure

The project also includes a synthetic operating-data pipeline:

- SQL feature layer for daily store-category demand, revenue, margin, weather, holiday, promotion, and rolling baseline features
- Python modeling pipeline for category-level demand elasticity
- Difference-in-differences validation for a cold beverage promotion wave
- Promotion recommendation output ranked by expected incremental margin
- Model monitoring table and charts for weekly error, bias, and review thresholds

The project uses public data where possible and synthetic data for the operating tables, so it is safe to share publicly while still demonstrating the workflow I would bring to a retail analytics team.

## Short note for LinkedIn or email

Hi [Name],

I’m applying for the Data Scientist, Data & Analytics role on the Starbucks team in Seattle. I noticed the role emphasizes SQL/Python pipelines, model-ready datasets, elasticity / causal inference, and decision-ready reporting.

I built a small proof-of-work project around Starbucks pricing and coffee-retail decision science. It maps public Caffè Latte delivery-menu observations across U.S. cities, joins them to BEA metro-area price-level data, and flags cities that sit above or below a local-cost-implied benchmark. I also included a SQL/Python promotion workflow with elasticity modeling, difference-in-differences validation, recommendation scoring, and model monitoring outputs.

Repo: [GitHub link]

My background is a close fit: I’ve built Spark/Databricks ETL pipelines at WPP, worked on 7-day demand forecasting for restaurant clients at SevenRooms, and built marketing mix / ROI measurement models at Xiaomi. I’d love to connect if this maps to what your team needs.

Best,  
Leo

## Application form / cover letter paragraph

I’m excited about this role because it sits at the intersection of data engineering, applied modeling, and business decision support. In my recent work, I migrated large-scale data pipelines to Azure/Databricks, built demand forecasting models for restaurant operations, and developed marketing mix and campaign measurement workflows. To make my interest concrete, I built a small coffee-retail decision science project that demonstrates the workflow I would bring to Starbucks: public-data sourcing, city-level pricing diagnostics, SQL-based feature creation, Python elasticity modeling, causal validation for promotions, recommendation scoring, and model monitoring outputs. I enjoy turning complex data relationships into repeatable pipelines and clear recommendations that business partners can actually use.

## Resume bullets to emphasize for this role

- Built Spark-based ETL pipelines across Databricks and Azure SQL, processing 5–20M rows/day and reducing report-refresh time by 40%.
- Developed a 7-day multi-output demand forecasting model for restaurant clients, then served predictions through FastAPI, Streamlit, and a SQL backend for venue-level decision support.
- Built a marketing mix model to quantify channel contribution and ROI, then validated recommendations through online A/B tests.
- Designed stakeholder-facing NLP and RAG workflows that translated unstructured feedback and report archives into decision-ready outputs.

## If someone asks “why this project?”

I wanted to show the full analytical operating loop rather than a standalone model: define a business decision, source imperfect but useful public data, state limitations clearly, shape reliable features, estimate model behavior, validate it, turn it into recommendations, and monitor whether the output remains trustworthy.
