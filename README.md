# Mamaearth Returns & Growth Intelligence Pipeline

## Project overview
This project analyses Mamaearth customer, product, and order data to understand revenue, returns, payment-method risk, and monthly sales trends. It combines SQL reporting, Python data cleaning and exploratory analysis, charts, and a generated business narrative.

## Business workflow
1. **SQL (MySQL Workbench):** creates the database tables, loads the supplied data, and runs business reports.
2. **Python (pandas):** standardizes payment-method labels, removes duplicate order records, handles missing values, checks unusual order quantities, reconciles revenue, and calculates return and revenue metrics.
3. **Visualizations (Matplotlib):** creates a payment-method return-rate chart and an outlier-corrected monthly revenue trend.
4. **Narrator:** turns the calculated findings into a Situation–Complication–Resolution (SCR) summary. It supports offline mode, so an API key is not required.

## Key findings
- The source data contains 45 customers, 16 products, and 180 order rows.
- Five duplicate order rows were identified; the cleaned dataset contains 175 orders.
- Raw revenue was ₹99,860.20 and cleaned revenue was ₹97,358.30, a difference of ₹2,501.90.
- COD had a 44.4% return rate, compared with 18.9% for UPI and 14.7% for CARD.
- COD orders in Tier-2 cities had a 54.5% return rate, making this a priority segment for further investigation.
- After flagging the two unusually large quantity orders for trend analysis, March 2026 was the highest-revenue month at ₹20,318.90.

These findings indicate associations in this dataset; they do not by themselves prove why orders were returned.

## Project files
- `sql/`: MySQL schema, seed data, and business-report queries.
- `data/`: original customer, product, and order CSV files.
- `analysis/`: cleaning/EDA script, visualization script, and generated cleaned dataset.
- `visualizations/`: generated PNG charts.
- `narrator/`: calculated findings, narrative generator, and sample narrative output.

## How to run
Python 3.10+ is recommended. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

### 1. SQL
In MySQL Workbench, run `sql/schema.sql`, then `sql/seed_data.sql`, then `sql/reports.sql`. The schema script drops and recreates the project tables, so do not rerun it against a database whose data you need to preserve.

### 2. Python analysis and charts
From the repository root, run:

```bash
python analysis/clean_and_eda.py
python analysis/visualize.py
```

### 3. Narrative
Run the offline-capable narrative generator:

```bash
python narrator/generate_narrative.py
```

The narrative uses the computed `narrator/findings.json` file. Gemini mode is optional and requires a `GEMINI_API_KEY` environment variable; never commit an API key.

## Reproducibility notes
The original CSVs are retained unchanged. The cleaning script creates `analysis/cleaned_analysis.csv` and `narrator/findings.json`; the visualization and narrative scripts use those outputs. Outlier orders are flagged for trend analysis rather than deleted from the cleaned order data.
