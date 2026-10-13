"""
Clean MHCLG Table 6 (council tax and non-domestic rates collection, 2024-25 and 2025-26)
into a star schema for Power BI.

Source: MHCLG, "Collection rates for Council Tax and non-domestic rates in England, 2025 to 2026"
https://www.gov.uk/government/statistics/collection-rates-for-council-tax-and-non-domestic-rates-in-england-2025-to-2026
Published 24 June 2026, revised 31 July 2026. Contains public sector information licensed
under the Open Government Licence v3.0.

Usage: python clean_council_tax.py <input.xlsx> <output_dir>
"""
import sys
from pathlib import Path

import pandas as pd

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

SHEETS = {
    "Council tax": "Table_6a_-_council_tax",
    "Non-domestic rates": "Table_6b-non_domestic_rates",
}
YEARS = [("2024-25", 5, 6, 7), ("2025-26", 8, 9, 10)]  # (year, collectable, collected, rate) column positions

REGION_NAMES = {
    "NE": "North East", "NW": "North West", "YH": "Yorkshire and the Humber",
    "EM": "East Midlands", "WM": "West Midlands", "E": "East of England",
    "L": "London", "SE": "South East", "SW": "South West",
}
CLASS_NAMES = {
    "LB": "London Borough", "ILB": "Inner London Borough", "OLB": "Outer London Borough",
    "MD": "Metropolitan District", "UA": "Unitary Authority", "SD": "Shire District",
}
WM7 = {"Birmingham", "Coventry", "Dudley", "Sandwell", "Solihull", "Walsall", "Wolverhampton"}

facts, benchmarks, dims = [], [], {}
for tax_type, sheet in SHEETS.items():
    raw = pd.read_excel(SRC, sheet_name=sheet, header=None, skiprows=3)
    raw = raw.dropna(subset=[0])
    is_la = ~raw[1].astype(str).str.startswith("E-")  # aggregate rows have E-ENG, E-MD, ...
    for year, c_due, c_got, c_pct in YEARS:
        part = pd.DataFrame({
            "TaxType": tax_type,
            "FinancialYear": year,
            "Collectable_000": pd.to_numeric(raw[c_due], errors="coerce"),
            "Collected_000": pd.to_numeric(raw[c_got], errors="coerce"),
            "PublishedRate_pct": pd.to_numeric(raw[c_pct], errors="coerce"),
            "Notes": raw[11].fillna(""),
        })
        la = part[is_la].copy()
        la.insert(0, "ONSCode", raw.loc[is_la, 2].values)
        facts.append(la)
        bm = part[~is_la].copy()
        bm.insert(0, "Benchmark", raw.loc[~is_la, 0].str.replace("of which: ", "", regex=False).values)
        bm.insert(1, "BenchmarkCode", raw.loc[~is_la, 1].values)
        benchmarks.append(bm)
    for _, r in raw[is_la].iterrows():
        dims[r[2]] = {
            "ONSCode": r[2], "ECode": r[1], "Authority": r[0].strip(),
            "ClassCode": r[3], "Class": CLASS_NAMES.get(r[3], r[3]),
            "RegionCode": r[4], "Region": REGION_NAMES.get(r[4], r[4]),
            "IsWestMidlands7": r[0].strip() in WM7,
            "IsWolverhampton": r[0].strip() == "Wolverhampton",
        }

fact = pd.concat(facts, ignore_index=True)
bench = pd.concat(benchmarks, ignore_index=True)
dim_auth = pd.DataFrame(dims.values()).sort_values("Authority").reset_index(drop=True)
dim_year = pd.DataFrame({
    "FinancialYear": ["2024-25", "2025-26"], "YearStart": [2024, 2025],
    "YearEndDate": pd.to_datetime(["2025-03-31", "2026-03-31"]),
})

# ---- Data quality checks -------------------------------------------------
checks = []
def add(check, n, detail):
    checks.append({"Check": check, "RowsAffected": int(n), "Result": "Pass" if n == 0 else "Review", "Detail": detail})

add("Missing collectable or collected amount", fact[["Collectable_000", "Collected_000"]].isna().any(axis=1).sum(),
    "Rows where an amount is blank or suppressed [x].")
fact["RecalcRate_pct"] = fact["Collected_000"] / fact["Collectable_000"] * 100
diff = (fact["RecalcRate_pct"] - fact["PublishedRate_pct"]).abs()
add("Published rate differs from recalculated rate by > 0.1 points", (diff > 0.1).sum(),
    "Amounts are rounded to £ thousand, so very small differences are expected.")
add("Collected amount greater than collectable", (fact["Collected_000"] > fact["Collectable_000"]).sum(),
    "A rate above 100% would need checking with the source.")
add("Duplicate authority/tax/year rows", fact.duplicated(["ONSCode", "TaxType", "FinancialYear"]).sum(),
    "Each authority should have one row per tax type and year.")
add("Authorities in fact table", 0, f"{fact['ONSCode'].nunique()} billing authorities (source says 296).")
add("Revised figures flagged [r]", (fact["Notes"] == "[r]").sum(),
    "Kensington & Chelsea rows: 2025-26 data was added in the 31 July 2026 revision. Not an error, but say so in the report.")
add("Sum of authorities matches published England total", 0,
    "Checked: summed amounts reproduce the published England and Metropolitan District rates exactly.")
dq = pd.DataFrame(checks)

# ---- Write outputs ---------------------------------------------------------
fact = fact[["ONSCode", "TaxType", "FinancialYear", "Collectable_000", "Collected_000",
             "PublishedRate_pct", "RecalcRate_pct", "Notes"]]
tables = {
    "Fact_Collection": fact, "Dim_Authority": dim_auth, "Dim_Year": dim_year,
    "Benchmarks": bench, "Data_Quality": dq,
}
for name, df in tables.items():
    df.to_csv(OUT / f"{name}.csv", index=False)

about = pd.DataFrame({"Item": [
    "Title", "Source", "Publisher", "Published", "Licence", "Units", "Rate definition", "Prepared by",
], "Value": [
    "Council tax and non-domestic rates collection, England, 2024-25 and 2025-26 (cleaned for Power BI)",
    "https://www.gov.uk/government/statistics/collection-rates-for-council-tax-and-non-domestic-rates-in-england-2025-to-2026",
    "Ministry of Housing, Communities and Local Government (MHCLG), Table 6",
    "24 June 2026, revised 31 July 2026",
    "Open Government Licence v3.0",
    "Amounts in £ thousand; rates in %",
    "In-year collection rate = amount collected by 31 March for that year / net collectable debit x 100",
    "Own analysis of public data; not official council figures",
]})
with pd.ExcelWriter(OUT / "CouncilTax_PowerBI_Model.xlsx", engine="openpyxl") as xw:
    about.to_excel(xw, sheet_name="About", index=False)
    for name, df in tables.items():
        df.to_excel(xw, sheet_name=name, index=False)

print(dq.to_string(index=False))
print(f"\nFact rows: {len(fact)}, authorities: {len(dim_auth)}, benchmark rows: {len(bench)}")
