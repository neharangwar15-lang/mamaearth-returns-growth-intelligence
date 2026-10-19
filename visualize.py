"""Generate the two required reproducible visualizations from cleaned_analysis.csv."""
from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
OUT = ROOT / "visualizations"
OUT.mkdir(exist_ok=True)

def main():
    df = pd.read_csv(ANALYSIS / "cleaned_analysis.csv", parse_dates=["order_date"])
    findings = json.loads((ROOT / "narrator" / "findings.json").read_text(encoding="utf-8"))

    rates = df.groupby("payment_method")["returned"].mean().mul(100).sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(rates.index, rates.values)
    ax.set_title("COD Returns at 44.4% — Nearly 3x CARD")
    ax.set_xlabel("Payment method")
    ax.set_ylabel("Return rate (%)")
    ax.set_ylim(0, max(rates.values) * 1.25)
    for bar, value in zip(bars, rates.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{value:.1f}%",
                ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(OUT / "return_rate_by_payment.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    monthly = findings["monthly_revenue_outlier_corrected"]
    months = list(monthly.keys())
    values = list(monthly.values())
    peak = findings["true_peak_month"]["month"]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(months, values, marker="o")
    ax.set_title(f"Outlier-Corrected Monthly Revenue — Peak: {peak}")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue (INR)")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(OUT / "monthly_revenue_trend.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("Generated:")
    print(OUT / "return_rate_by_payment.png")
    print(OUT / "monthly_revenue_trend.png")

if __name__ == "__main__":
    main()
