// =====================================================================
// Power Query (M) - clean the ORIGINAL MHCLG file inside Power BI
// Optional: use this to show Power Query skills. The simple way is to
// load CouncilTax_PowerBI_Model.xlsx instead.
//
// How to use:
//   1. Open the MHCLG file in Excel. Save As > "Excel Workbook (*.xlsx)".
//      (Do NOT use "Strict Open XML" - Power BI may not read it.)
//   2. Power BI: Home > Transform data > New Source > Blank Query.
//   3. View > Advanced Editor. Paste this code. Change FilePath.
//   4. Rename the query "CouncilTax_Clean".
// Note: written for the 2025-26 Table 6a layout. Not tested in Power BI
// Desktop - check each step in the Applied Steps pane.
// =====================================================================
let
    FilePath  = "C:\Data\Table_6_2025-26.xlsx",   // <-- change this
    TaxSheet  = "Table_6a_-_council_tax",          // or "Table_6b-non_domestic_rates"

    Source    = Excel.Workbook(File.Contents(FilePath), null, true),
    Sheet     = Source{[Item = TaxSheet, Kind = "Sheet"]}[Data],

    // Rows 1-3 are title, description and long headers
    SkipTop   = Table.Skip(Sheet, 3),

    NewNames  = {"Authority", "ECode", "ONSCode", "ClassCode", "RegionCode",
                 "Collectable_2024-25", "Collected_2024-25", "Rate_2024-25",
                 "Collectable_2025-26", "Collected_2025-26", "Rate_2025-26", "Notes"},
    Renamed   = Table.RenameColumns(
                    SkipTop,
                    List.Zip({List.FirstN(Table.ColumnNames(SkipTop), 12), NewNames})),
    KeepCols  = Table.SelectColumns(Renamed, NewNames),

    // Remove England / class total rows (their E-Code starts with "E-")
    OnlyLAs   = Table.SelectRows(
                    KeepCols,
                    each [Authority] <> null and not Text.StartsWith(Text.From([ECode]), "E-")),
    Trimmed   = Table.TransformColumns(OnlyLAs, {{"Authority", Text.Trim, type text}}),

    // Wide (one column per year) -> long (one row per year)
    Unpivoted = Table.UnpivotOtherColumns(
                    Trimmed,
                    {"Authority", "ECode", "ONSCode", "ClassCode", "RegionCode", "Notes"},
                    "Attribute", "Value"),
    Split     = Table.SplitColumn(
                    Unpivoted, "Attribute",
                    Splitter.SplitTextByDelimiter("_", QuoteStyle.None),
                    {"Measure", "FinancialYear"}),
    Pivoted   = Table.Pivot(Split, {"Collectable", "Collected", "Rate"}, "Measure", "Value"),

    Typed     = Table.TransformColumnTypes(
                    Pivoted,
                    {{"Collectable", type number}, {"Collected", type number},
                     {"Rate", type number}, {"FinancialYear", type text}}),

    // Data quality check: recalculate the rate and compare
    AddRecalc = Table.AddColumn(Typed, "RecalcRate",
                    each [Collected] / [Collectable] * 100, type number),
    AddCheck  = Table.AddColumn(AddRecalc, "RateCheck",
                    each if Number.Abs([RecalcRate] - [Rate]) <= 0.1 then "OK" else "Review",
                    type text),
    AddTax    = Table.AddColumn(AddCheck, "TaxType",
                    each if TaxSheet = "Table_6a_-_council_tax" then "Council tax" else "Non-domestic rates",
                    type text)
in
    AddTax
