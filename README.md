# Council Tax Collection Benchmarking – West Midlands

A Power BI project that compares the council tax and business rates (non-domestic rates) collection of **Wolverhampton** with the other West Midlands metropolitan councils and with England.

**Tools:** Power BI Desktop, Power Query, DAX, Python (pandas)
**Data:** MHCLG, *Collection rates for Council Tax and non-domestic rates in England, 2025 to 2026*, Table 6. Published 24 June 2026, revised 31 July 2026. [Source page](https://www.gov.uk/government/statistics/collection-rates-for-council-tax-and-non-domestic-rates-in-england-2025-to-2026). Open Government Licence v3.0.

> This is my own analysis of public data. It is not an official council or government report.

---

## 1. Files

| File | What it is |
|---|---|
| `CouncilTax_PowerBI_Model.xlsx` | Clean data, ready for Power BI. One sheet for each table, plus an About sheet. |
| `Fact_Collection.csv` | Fact table: 296 councils × 2 tax types × 2 years = 1,184 rows. |
| `Dim_Authority.csv` | One row for each council: codes, class, region, West Midlands flag. |
| `Dim_Year.csv` | Financial years 2024-25 and 2025-26. |
| `Benchmarks.csv` | Published totals for England and each council class (for checking). |
| `Data_Quality.csv` | Results of the data quality checks. |
| `DAX_Measures.dax` | All DAX measures for the report. |
| `PowerQuery_CleanSource.m` | Optional: Power Query code that cleans the original MHCLG file. |
| `clean_council_tax.py` | Python script that made the clean files from the MHCLG file. |

---

## 2. Data model (star schema)

```
Dim_Authority (296 rows)          Dim_Year (2 rows)
   ONSCode  1 ──┐               ┌── 1  FinancialYear
                │               │
                *               *
           Fact_Collection (1,184 rows)
           ONSCode, TaxType, FinancialYear,
           Collectable_000, Collected_000,
           PublishedRate_pct, RecalcRate_pct, Notes
```

- Amounts are in **£ thousand**.
- `Benchmarks` and `Data_Quality` are separate tables. Do not connect them.

---

## 3. Build steps in Power BI Desktop

### Step 1 – Load the data
1. Open Power BI Desktop. Select **Get data > Excel workbook**.
2. Select `CouncilTax_PowerBI_Model.xlsx`.
3. Tick **Fact_Collection, Dim_Authority, Dim_Year, Data_Quality**. Select **Load**.

### Step 2 – Make the relationships
1. Go to **Model view**.
2. Drag `Dim_Authority[ONSCode]` to `Fact_Collection[ONSCode]`. Check: one-to-many, single direction.
3. Drag `Dim_Year[FinancialYear]` to `Fact_Collection[FinancialYear]`.
4. Hide the key columns in the fact table (right-click > Hide in report view).

### Step 3 – Add the measures
1. Select **Home > Enter data**. Name the table `_Measures`. Select **Load**.
2. Open `DAX_Measures.dax`. Copy each measure into `_Measures` with **New measure**.
3. Format `Collection Rate` and the other `Rate ...` measures as **Percentage, 1 decimal**.
4. Delete the blank column in `_Measures`. The table icon then shows as a measures table.

### Step 4 – Build the report pages

**Page 1 – Overview**
- Slicers: `TaxType` (single select, default "Council tax"), `FinancialYear` (default 2025-26), `Authority` (default Wolverhampton).
- Cards: `Collection Rate`, `Rate England`, `Rate Same Class`, `Gap vs England (pts)`, `Rank Label`, `Uncollected (£k)`.
- Card `RAG Status`, with the font colour from `RAG Colour` (Conditional formatting > Field value).
- Text box or card: `Plain English Summary`.
- Title: `Dynamic Title`.

**Page 2 – West Midlands benchmark**
- Filter the page: `Dim_Authority[IsWestMidlands7] = True`.
- Clustered bar chart: Authority on the axis, `Collection Rate` as the value. Sort high to low. Bar colour from `Bar Colour`.
- Add a constant line at the England rate (Analytics pane), or a line visual with `Rate England`.
- Table: Authority, `Collection Rate`, `YoY Change (pts)`, `Rank in West Midlands 7`, `Rank in England`, `RAG Status`.

**Page 3 – Trend and compare**
- Clustered column chart: FinancialYear on the axis; `Collection Rate`, `Rate Same Class`, `Rate England` as values.
- Same chart for non-domestic rates (use the TaxType slicer).

**Page 4 – Data quality**
- Table visual of `Data_Quality`.
- Cards: `Rows Flagged Revised`, `Max Rate Difference (pts)`.
- Text box: source, publication date, licence, units, and the limitations in section 6.

### Step 5 – Make it self-service
- Sync the slicers across pages (View > Sync slicers).
- Add tooltips that show `Collected (£k)` and `Collectable (£k)`.
- Add a "Reset" bookmark button.

### Step 6 – Publish
- Save as `CouncilTax_Benchmarking.pbix`.
- Put the `.pbix`, these files and 3–4 screenshots on GitHub.
- Optional: **Publish to web** (public data only).

---

## 4. Data quality checks

| Check | Result |
|---|---|
| Missing amounts | 0 rows – Pass |
| Published rate vs recalculated rate (> 0.1 points) | 0 rows – Pass |
| Collected > collectable | 0 rows – Pass |
| Duplicate council/tax/year rows | 0 rows – Pass |
| Number of councils | 296 (matches the source) |
| Sum of councils vs published England total | Matches exactly |
| Revised rows `[r]` | 4 rows (Kensington & Chelsea) – data added in the 31 July 2026 revision |

---

## 5. Key findings (council tax, in-year collection rate)

| | 2024-25 | 2025-26 | Change |
|---|---|---|---|
| **Wolverhampton** | 92.6% | 92.2% | −0.3 pts |
| West Midlands 7 (pooled) | 93.1% | 92.5% | −0.7 pts |
| Metropolitan Districts | 93.6% | 93.3% | −0.3 pts |
| England | 95.9% | 95.6% | −0.3 pts |

- In 2025-26, Wolverhampton collected **92.2%** of council tax due in the year. This was **3.4 points below England** and 1.1 points below the average for metropolitan districts.
- About **£12.9 million** was not collected by 31 March 2026.
- Wolverhampton ranked **281 of 296** councils in England, **32 of 36** metropolitan districts, and **6 of 7** in the West Midlands group.
- For **business rates**, the result is different: Wolverhampton collected **97.0%** in 2025-26, which is **above England (96.7%)**, and it improved by 0.7 points.

---

## 6. Limitations (read before you draw conclusions)

1. **In-year rate is not the final rate.** Councils continue to collect arrears after 31 March. A low in-year rate does not mean the money is lost.
2. **Only two years.** Two points are not a trend. Add older Table 6 files to see a 5-year pattern.
3. **Correlation, not cause.** Lower collection rates often appear in areas with higher deprivation. This analysis does not show *why* a council's rate is lower. Local council tax support schemes, discounts and population differences also change the rate.
4. **Pooled vs simple average.** Group rates in this report are pooled (total collected ÷ total collectable). Large councils such as Birmingham have more weight. The simple average of the 7 councils' rates is higher (93.3% in 2025-26).
5. **RAG thresholds are my own rule** (Green ≥ England; Amber within 2 points; Red more than 2 points below). They are not official targets.
6. Figures are as reported by councils to MHCLG and can be revised.

---

## 7. Next steps
- Add 3 more years from older MHCLG releases.
- Add Index of Multiple Deprivation (IMD) scores to test the deprivation relationship.
- Add homelessness and fly-tipping indicators for a wider performance dashboard.
- Load the files into a Microsoft Fabric lakehouse and connect the report to it.
