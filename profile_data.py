import argparse
import os
import sys
from io import StringIO

import pandas as pd
import numpy as np


VALID_RESULTS      = {"white", "black", "draw"}
VALID_RATING_GROUPS = {"beginner", "novice", "intermediate", "advanced", "expert", "master"}
ELO_MIN, ELO_MAX   = 400, 3500


def section(title: str) -> str:
    bar = "=" * 60
    return f"\n{bar}\n  {title}\n{bar}\n"


def subsection(title: str) -> str:
    return f"\n--- {title} ---\n"


def pct(n: int, total: int) -> str:
    return f"{n:,} ({100 * n / total:.1f}%)" if total else "0 (N/A)"


def profile_basic(df: pd.DataFrame, name: str) -> str:
    out = section(f"Basic Profile — {name}")
    out += f"Rows    : {len(df):,}\n"
    out += f"Columns : {len(df.columns)}\n"
    out += f"Columns : {list(df.columns)}\n"

    n_dup = df.duplicated().sum()
    out += f"\nDuplicate rows : {pct(n_dup, len(df))}\n"

    return out


def profile_missing(df: pd.DataFrame) -> str:
    out = subsection("Missing Values")
    total = len(df)
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if missing.empty:
        out += "No missing values found.\n"
    else:
        for col, n in missing.items():
            out += f"  {col:<30} {pct(n, total)}\n"
    return out


def profile_numeric(df: pd.DataFrame) -> str:
    out = subsection("Numeric Column Statistics")
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if not num_cols:
        out += "No numeric columns.\n"
        return out
    stats = df[num_cols].describe().T
    out += stats.to_string() + "\n"
    return out


def profile_categorical(df: pd.DataFrame, cols: list[str]) -> str:
    out = subsection("Categorical Value Distributions")
    for col in cols:
        if col not in df.columns:
            continue
        counts = df[col].value_counts(dropna=False)
        out += f"\n  {col}:\n"
        for val, n in counts.items():
            out += f"    {str(val):<35} {pct(n, len(df))}\n"
    return out


def profile_elo(df: pd.DataFrame) -> str:
    out = subsection("Elo Rating Validity")
    for col in ["white_elo", "black_elo"]:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        out_of_range = ((series < ELO_MIN) | (series > ELO_MAX)).sum()
        out += f"  {col}: min={series.min()}, max={series.max()}, "
        out += f"mean={series.mean():.0f}, "
        out += f"out-of-range [{ELO_MIN}–{ELO_MAX}]: {pct(out_of_range, len(series))}\n"
    return out


def profile_results(df: pd.DataFrame) -> str:
    out = subsection("Result Validity")
    if "result" not in df.columns:
        return out + "  Column 'result' not found.\n"
    invalid = ~df["result"].isin(VALID_RESULTS)
    out += f"  Valid values   : {sorted(VALID_RESULTS)}\n"
    out += f"  Invalid values : {pct(invalid.sum(), len(df))}\n"
    if invalid.any():
        out += f"  Unique invalid : {df.loc[invalid, 'result'].unique().tolist()}\n"
    return out


def profile_eco(df: pd.DataFrame) -> str:
    out = subsection("ECO Opening Coverage")
    if "eco_code" not in df.columns:
        return out + "  Column 'eco_code' not found.\n"
    unknown  = (df["eco_code"] == "Unknown").sum()
    n_unique = df.loc[df["eco_code"] != "Unknown", "eco_code"].nunique()
    out += f"  Matched to ECO opening : {pct(len(df) - unknown, len(df))}\n"
    out += f"  Unknown                : {pct(unknown, len(df))}\n"
    out += f"  Unique ECO codes       : {n_unique}\n"
    out += f"  Unique opening names   : {df['opening_name'].nunique()}\n"
    return out


def profile_acpl(df: pd.DataFrame) -> str:
    out = subsection("Post-Opening ACPL (eval data)")
    if "post_opening_acpl" not in df.columns:
        return out + "  Column 'post_opening_acpl' not found.\n"
    series   = df["post_opening_acpl"].dropna()
    n_total  = len(df)
    n_has    = len(series)
    out += f"  Games with ACPL data   : {pct(n_has, n_total)}\n"
    if n_has == 0:
        out += "  No ACPL data available.\n"
        return out
    out += f"  Min ACPL               : {series.min():.2f} cp\n"
    out += f"  Max ACPL               : {series.max():.2f} cp\n"
    out += f"  Mean ACPL              : {series.mean():.2f} cp\n"
    out += f"  Median ACPL            : {series.median():.2f} cp\n"
    out += f"  Std ACPL               : {series.std():.2f} cp\n"

    outliers = (series > 500).sum()
    out += f"  Outliers (ACPL > 500)  : {pct(outliers, n_has)}\n"
    return out


def profile_eco_line_length(df: pd.DataFrame) -> str:
    out = subsection("ECO Line Length")
    if "eco_line_length" not in df.columns:
        return out + "  Column 'eco_line_length' not found.\n"
    series = df["eco_line_length"].dropna()
    out += f"  Min    : {series.min()}\n"
    out += f"  Max    : {series.max()}\n"
    out += f"  Mean   : {series.mean():.2f}\n"
    out += f"  Median : {series.median():.0f}\n"
    out += f"  Std    : {series.std():.2f}\n"

    out += "\n  Distribution:\n"
    counts = series.value_counts().sort_index()
    for length, n in counts.items():
        out += f"    {int(length):>3} half-moves : {pct(n, len(df))}\n"
    return out


def profile_rating_groups(df: pd.DataFrame) -> str:
    out = subsection("Rating Group Distribution")
    if "rating_group" not in df.columns:
        return out + "  Column 'rating_group' not found.\n"
    invalid_groups = ~df["rating_group"].isin(VALID_RATING_GROUPS)
    out += f"  Invalid rating groups  : {pct(invalid_groups.sum(), len(df))}\n\n"
    counts = df["rating_group"].value_counts()
    for group, n in counts.items():
        out += f"  {str(group):<15} : {pct(n, len(df))}\n"
    return out


def profile_file(path: str, label: str, is_integrated: bool) -> str:
    print(f"  Profiling: {path}")
    df  = pd.read_csv(path)
    out = ""
    out += profile_basic(df, label)
    out += profile_missing(df)
    out += profile_numeric(df)
    out += profile_results(df)
    out += profile_elo(df)
    out += profile_categorical(df, ["time_control"])

    if is_integrated:
        out += profile_eco(df)
        out += profile_eco_line_length(df)
        out += profile_rating_groups(df)
        out += profile_acpl(df)

    return out


def main():
    parser = argparse.ArgumentParser(
        description="Profile and assess data quality for the chess opening analysis datasets."
    )
    parser.add_argument("--cleaned",    type=str, required=True,
                        help="Path to the cleaned games CSV (output of clean_data.py)")
    parser.add_argument("--integrated", type=str, required=True,
                        help="Path to the integrated CSV (output of integrate_data.py)")
    parser.add_argument("--outdir",     type=str, default="results",
                        help="Directory to save the quality report (default: results/)")
    args = parser.parse_args()

    for path in [args.cleaned, args.integrated]:
        if not os.path.exists(path):
            print(f"Error: File not found: {path}")
            sys.exit(1)

    os.makedirs(args.outdir, exist_ok=True)
    report_path = os.path.join(args.outdir, "data_quality_report.txt")

    print("Running data quality profiling...")

    report  = "DATA QUALITY REPORT\n"
    report += f"Cleaned dataset    : {args.cleaned}\n"
    report += f"Integrated dataset : {args.integrated}\n"
    report += "\n"

    report += profile_file(args.cleaned,    "Cleaned Games CSV",    is_integrated=False)
    report += profile_file(args.integrated, "Integrated Games CSV", is_integrated=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
