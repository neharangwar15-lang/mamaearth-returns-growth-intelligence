"""Clean raw Mamaearth CSVs, run EDA, and generate verified findings.json."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
NARRATOR = ROOT / "narrator"
NARRATOR.mkdir(exist_ok=True)

def money(value):
    return round(float(value), 2)

def main():
    customers = pd.read_csv(DATA / "customers.csv")
    products = pd.read_csv(DATA / "products.csv")
    orders = pd.read_csv(DATA / "orders.csv")

    print("TASK 1 — LOAD AND INSPECT")
    print("customers shape:", customers.shape)
    print("products shape:", products.shape)
    print("orders raw shape:", orders.shape)
    assert orders.shape == (180, 9)

    print("\nTASK 2 — STANDARDIZE PAYMENT METHOD")
    print("Raw payment values:", sorted(orders["payment_method"].dropna().unique().tolist()))
    print("Raw unique count:", orders["payment_method"].nunique())
    orders["payment_method"] = orders["payment_method"].astype("string").str.strip().str.upper()
    print("Clean payment counts:\n", orders["payment_method"].value_counts().sort_index())
    assert orders["payment_method"].nunique() == 3

    print("\nTASK 3 — REMOVE DUPLICATES USING NATURAL KEY")
    natural_key = ["customer_id", "product_id", "order_date", "quantity",
                   "discount_pct", "payment_method", "rating", "returned"]
    duplicate_mask = orders.duplicated(subset=natural_key, keep="first")
    dropped = orders.loc[duplicate_mask].copy()
    print("Duplicate order IDs:", dropped["order_id"].tolist())
    orders_clean = orders.loc[~duplicate_mask].copy()
    print("Dropped rows:", int(duplicate_mask.sum()))
    print("Clean shape:", orders_clean.shape)
    assert dropped["order_id"].tolist() == ["O0176", "O0177", "O0178", "O0179", "O0180"]
    assert orders_clean.shape == (175, 9)

    print("\nTASK 4 — IMPUTE MISSING VALUES")
    missing_discount = int(orders_clean["discount_pct"].isna().sum())
    missing_rating = int(orders_clean["rating"].isna().sum())
    rating_median = float(orders_clean["rating"].median())
    print("Missing discount rows:", missing_discount)
    print("Missing rating rows:", missing_rating)
    print("Rating median before imputation:", rating_median)
    orders_clean["discount_pct"] = orders_clean["discount_pct"].fillna(0)
    orders_clean["rating"] = orders_clean["rating"].fillna(rating_median)
    print("Remaining nulls:\n", orders_clean[["discount_pct", "rating"]].isnull().sum().to_dict())
    assert missing_discount == 12 and missing_rating == 15 and rating_median == 3.0
    assert not orders_clean[["discount_pct", "rating"]].isnull().any().any()

    print("\nTASK 5 — MERGE AND RECONCILE")
    # Independent value calculation for removed duplicates: raw blank discount is treated as 0%.
    dropped_value = dropped.merge(products[["product_id", "price"]], on="product_id", how="left")
    dropped_value["order_value"] = dropped_value["quantity"] * dropped_value["price"] * (
        1 - dropped_value["discount_pct"].fillna(0) / 100.0
    )
    merged = (orders_clean.merge(products, on="product_id", how="left", validate="many_to_one")
              .merge(customers, on="customer_id", how="left", validate="many_to_one"))
    merged["order_date"] = pd.to_datetime(merged["order_date"], errors="raise")
    merged["order_value"] = merged["quantity"] * merged["price"] * (
        1 - merged["discount_pct"] / 100.0
    )
    cleaned_revenue = money(merged["order_value"].sum())
    duplicate_delta = money(dropped_value["order_value"].sum())
    raw_revenue = money(cleaned_revenue + duplicate_delta)
    print("Cleaned rows:", len(merged))
    print(f"Cleaned revenue: ₹{cleaned_revenue:,.2f}")
    print(f"Removed duplicate rows' combined value: ₹{duplicate_delta:,.2f}")
    print(f"Reconciled raw revenue: ₹{raw_revenue:,.2f}")
    print(
        f"Reconciliation: raw revenue ₹{raw_revenue:,.2f} minus cleaned revenue "
        f"₹{cleaned_revenue:,.2f} equals ₹{duplicate_delta:,.2f}. This exact delta "
        "comes from the five double-submitted rows removed in Task 3. Filling missing "
        "discounts with 0 and imputing ratings do not change order-value totals."
    )
    assert cleaned_revenue == 97358.30, f"Unexpected cleaned revenue {cleaned_revenue}"
    assert duplicate_delta == 2501.90, f"Unexpected duplicate delta {duplicate_delta}"
    assert raw_revenue == 99860.20

    print("\nTASK 6 — IQR OUTLIERS ON QUANTITY")
    q1 = float(merged["quantity"].quantile(0.25))
    q3 = float(merged["quantity"].quantile(0.75))
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    merged["is_outlier"] = ~merged["quantity"].between(lower, upper, inclusive="both")
    outliers = merged.loc[merged["is_outlier"], ["order_id", "quantity"]].sort_values("order_id")
    print({"Q1": q1, "Q3": q3, "IQR": iqr, "lower": lower, "upper": upper})
    print("Outlier rows (flagged, not dropped):\n", outliers.to_string(index=False))
    assert (q1, q3, iqr, lower, upper) == (1.0, 2.0, 1.0, -0.5, 3.5)
    assert outliers["order_id"].tolist() == ["O0011", "O0098"]

    print("\nTASK 7 — COD RETURN-RATE HYPOTHESIS")
    print("Hypothesis: COD orders have a higher return rate than CARD and UPI orders.")
    by_payment = merged.groupby("payment_method")["returned"].agg(["count", "mean"])
    by_payment["return_rate_pct"] = (by_payment["mean"] * 100).round(1)
    print(by_payment[["count", "return_rate_pct"]].to_string())
    rates = by_payment["return_rate_pct"].to_dict()
    assert rates == {"CARD": 14.7, "COD": 44.4, "UPI": 18.9}
    print("Verdict: Confirmed — COD has the highest return rate.")

    print("\nTASK 8 — PAYMENT METHOD × CITY TIER")
    segment = merged.groupby(["payment_method", "city_tier"])["returned"].agg(["count", "mean"])
    segment["return_rate_pct"] = (segment["mean"] * 100).round(1)
    print(segment[["count", "return_rate_pct"]].to_string())
    high_risk = segment["return_rate_pct"].idxmax()
    high_rate = float(segment.loc[high_risk, "return_rate_pct"])
    print(f"Highest-risk segment: {high_risk[0]} + Tier-{high_risk[1]} at {high_rate:.1f}%")
    assert high_risk == ("COD", 2) and high_rate == 54.5

    print("\nTASK 9 — CORRELATION ANALYSIS")
    corr_cols = ["rating", "returned", "discount_pct", "quantity"]
    corr = merged[corr_cols].corr(numeric_only=True)
    print(corr.round(4).to_string())
    def band(r):
        a = abs(float(r))
        if a < 0.2:
            return "negligible"
        if a < 0.4:
            return "weak"
        if a < 0.7:
            return "moderate"
        return "strong"
    for i, a in enumerate(corr_cols):
        for b in corr_cols[i+1:]:
            print(f"{a} vs {b}: r={corr.loc[a,b]:.4f} — {band(corr.loc[a,b])}")
            assert band(corr.loc[a,b]) == "negligible"
    print(f"Hypothesis 'higher discounts reduce returns': Busted (r={corr.loc['discount_pct','returned']:.4f}).")

    print("\nTASK 10 — MONTHLY REVENUE WITH AND WITHOUT OUTLIERS")
    merged["year_month"] = merged["order_date"].dt.to_period("M").astype(str)
    monthly_all = merged.groupby("year_month")["order_value"].sum().round(2)
    monthly_corrected = merged.loc[~merged["is_outlier"]].groupby("year_month")["order_value"].sum().round(2)
    monthly_all = monthly_all.reindex(sorted(monthly_all.index))
    monthly_corrected = monthly_corrected.reindex(sorted(monthly_all.index))
    print("Including flagged outliers:\n", monthly_all.to_string())
    print("Excluding flagged outliers:\n", monthly_corrected.to_string())
    peak_month = str(monthly_corrected.idxmax())
    peak_value = money(monthly_corrected.max())
    print(
        "Interpretation: January's apparent lead is an artifact of the two bulk orders "
        "O0011 (2026-01-28) and O0098 (2026-01-10). Once those flagged orders are excluded, "
        f"March is the genuine peak month at ₹{peak_value:,.2f}."
    )
    expected_corrected = {
        "2026-01": 11637.10, "2026-02": 13195.50, "2026-03": 20318.90,
        "2026-04": 9495.30, "2026-05": 13151.10, "2026-06": 11615.40
    }
    assert {k: money(v) for k,v in monthly_corrected.items()} == expected_corrected
    assert peak_month == "2026-03" and peak_value == 20318.90

    print("\nTASK 11 — EXPORT VERIFIED FINDINGS")
    findings = {
        "cleaned_total_revenue_inr": cleaned_revenue,
        "raw_total_revenue_inr": raw_revenue,
        "duplicate_reconciliation_delta_inr": duplicate_delta,
        "return_rate_by_payment": {k: float(rates[k]) for k in ["COD", "CARD", "UPI"]},
        "highest_risk_segment": {
            "payment_method": high_risk[0], "city_tier": int(high_risk[1]),
            "return_rate_pct": high_rate
        },
        "true_peak_month": {"month": peak_month, "revenue_inr": peak_value},
        "outlier_inflated_month": {
            "month": str(monthly_all.idxmax()),
            "apparent_revenue_inr": money(monthly_all.max()),
            "corrected_revenue_inr": money(monthly_corrected.loc[monthly_all.idxmax()])
        },
        "monthly_revenue_including_outliers": {k: money(v) for k,v in monthly_all.items()},
        "monthly_revenue_outlier_corrected": {k: money(v) for k,v in monthly_corrected.items()}
    }
    (NARRATOR / "findings.json").write_text(json.dumps(findings, indent=2) + "\n", encoding="utf-8")
    # Save computed analysis data for visualize.py, ensuring it uses this exact pipeline's output.
    out_csv = ROOT / "analysis" / "cleaned_analysis.csv"
    merged.to_csv(out_csv, index=False)
    print("Wrote narrator/findings.json and analysis/cleaned_analysis.csv")
    print(json.dumps(findings, indent=2))

if __name__ == "__main__":
    main()
