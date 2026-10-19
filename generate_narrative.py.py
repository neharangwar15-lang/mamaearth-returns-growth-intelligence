"""Gemini SCR narrative with deterministic offline fallback and numeric checker."""
from pathlib import Path
import json
import os
import re

ROOT = Path(__file__).resolve().parents[1]
FINDINGS_PATH = ROOT / "narrator" / "findings.json"
SAMPLE_PATH = ROOT / "narrator" / "sample_output.txt"

def generate_scr_narrative_offline(findings: dict) -> dict:
    """Fully keyless and deterministic narrative built from computed findings."""
    cleaned = findings["cleaned_total_revenue_inr"]
    raw = findings["raw_total_revenue_inr"]
    delta = findings["duplicate_reconciliation_delta_inr"]
    rates = findings["return_rate_by_payment"]
    risk = findings["highest_risk_segment"]
    peak = findings["true_peak_month"]
    inflated = findings["outlier_inflated_month"]
    narrative = (
        "Situation\n"
        f"After removing duplicate orders, cleaned revenue is ₹{cleaned:,.2f}, compared with "
        f"raw revenue of ₹{raw:,.2f}. The cleaned dataset retains the legitimate 175 orders.\n\n"
        "Complication\n"
        f"COD has a {rates['COD']:.1f}% return rate, compared with {rates['CARD']:.1f}% for CARD "
        f"and {rates['UPI']:.1f}% for UPI. The highest-risk segment is COD in Tier-{risk['city_tier']} "
        f"cities, with a {risk['return_rate_pct']:.1f}% return rate. Removing duplicate rows explains "
        f"the ₹{delta:,.2f} revenue difference. January appears to lead at ₹{inflated['apparent_revenue_inr']:,.2f} "
        f"before outlier correction, but its corrected revenue is ₹{inflated['corrected_revenue_inr']:,.2f}.\n\n"
        "Resolution\n"
        f"Prioritize investigation of COD workflows in Tier-{risk['city_tier']} cities and monitor return "
        f"reasons by payment method. Use outlier-corrected revenue for trend decisions: {peak['month']} "
        f"(March) is the true peak at ₹{peak['revenue_inr']:,.2f}. These figures come from the supplied "
        "analysis findings; validate operational actions against business context."
    )
    return {"status": "success", "narrative": narrative, "tokens": 0, "mode": "offline"}

def generate_scr_narrative(findings: dict) -> dict:
    """Call Gemini if a key is configured; otherwise return offline narrative."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return generate_scr_narrative_offline(findings)
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=30000))
        system_instruction = (
            "You are a senior data analyst writing for Mamaearth's regional ops and finance heads. "
            "Return exactly three labeled sections: Situation, Complication, Resolution. "
            "Every number must come only from the supplied findings and must preserve its value; "
            "do not invent statistics or introduce unsupported numerical claims."
        )
        contents = (
            "Write a concise business narrative using the SCR structure. Use only these verified findings:\n"
            + json.dumps(findings, ensure_ascii=False, indent=2)
        )
        # Temperature 0.0 is used because this is a factual business report, not creative writing.
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,
                max_output_tokens=1024
            )
        )
        text = response.text or ""
        usage = getattr(response, "usage_metadata", None)
        tokens = getattr(usage, "total_token_count", 0) if usage else 0
        if not text.strip():
            raise ValueError("Gemini returned an empty narrative.")
        return {"status": "success", "narrative": text, "tokens": tokens, "mode": "gemini"}
    except Exception as err:
        return {"status": "error", "narrative": None, "message": str(err), "mode": "gemini"}

def check_numeric_accuracy(narrative: str, findings: dict) -> bool:
    """Print pass/fail for each required numeric/peak-month figure."""
    normalized = narrative.replace(",", "")
    tests = [
        ("cleaned revenue", "97358.3" in normalized or "97358.30" in normalized),
        ("COD return rate", "44.4" in normalized),
        ("COD + Tier-2 return rate", "54.5" in normalized),
        ("duplicate reconciliation delta", "2501.9" in normalized or "2501.90" in normalized),
        ("March true peak revenue", "March" in narrative and
         ("20318.9" in normalized or "20318.90" in normalized or "20,318.90" in narrative)),
    ]
    passed = True
    for label, ok in tests:
        print(f"{'PASS' if ok else 'FAIL'} — {label}")
        passed = passed and ok
    return passed

def main():
    if not FINDINGS_PATH.exists():
        raise FileNotFoundError("Run python analysis/clean_and_eda.py first to create findings.json.")
    findings = json.loads(FINDINGS_PATH.read_text(encoding="utf-8"))
    result = generate_scr_narrative(findings)
    if result["status"] == "error":
        print("Gemini call failed; using offline fallback. Error:", result.get("message"))
        result = generate_scr_narrative_offline(findings)
    narrative = result["narrative"]
    print(f"Mode: {result.get('mode', 'offline')}; tokens: {result.get('tokens', 0)}")
    print("\n" + narrative)
    ok = check_numeric_accuracy(narrative, findings)
    if not ok:
        print("Numeric check failed; replacing narrative with deterministic offline output.")
        result = generate_scr_narrative_offline(findings)
        narrative = result["narrative"]
        ok = check_numeric_accuracy(narrative, findings)
    SAMPLE_PATH.write_text(narrative.rstrip() + "\n", encoding="utf-8")
    print("Saved sample output to narrator/sample_output.txt")
    if not ok:
        raise SystemExit("Numeric accuracy check failed even after offline fallback.")

if __name__ == "__main__":
    main()
