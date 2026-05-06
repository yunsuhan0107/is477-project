import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
from scipy import stats


RATING_GROUP_ORDER = ["beginner", "novice", "intermediate", "advanced", "expert", "master"]

WHITE_WIN = "white"
BLACK_WIN = "black"
DRAW      = "draw"


def load_data(path: str) -> pd.DataFrame:
    print(f"Loading integrated dataset from: {path}")
    df = pd.read_csv(path)
    print(f"  {len(df):,} games loaded.")
    before = len(df)
    df = df[df["eco_code"] != "Unknown"].copy()
    print(f"  {len(df):,} games retained after dropping Unknown openings "
          f"({before - len(df):,} removed).")
    return df


def encode_result(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["white_win"] = (df["result"] == WHITE_WIN).astype(int)
    df["draw"]      = (df["result"] == DRAW).astype(int)
    df["black_win"] = (df["result"] == BLACK_WIN).astype(int)
    return df


def overall_winrates(df: pd.DataFrame, min_games: int) -> pd.DataFrame:
    agg = (
        df.groupby(["eco_code", "opening_name"])
        .agg(
            games      = ("result",    "count"),
            white_wins = ("white_win", "sum"),
            draws      = ("draw",      "sum"),
            black_wins = ("black_win", "sum"),
        )
        .reset_index()
    )
    agg = agg[agg["games"] >= min_games].copy()
    agg["white_win_rate"] = agg["white_wins"] / agg["games"]
    agg["draw_rate"]      = agg["draws"]      / agg["games"]
    agg["black_win_rate"] = agg["black_wins"] / agg["games"]
    return agg.sort_values("white_win_rate", ascending=False)


def winrates_by_group(df: pd.DataFrame, min_games: int) -> pd.DataFrame:
    agg = (
        df.groupby(["eco_code", "opening_name", "rating_group"])
        .agg(
            games      = ("result",    "count"),
            white_wins = ("white_win", "sum"),
        )
        .reset_index()
    )
    agg = agg[agg["games"] >= min_games].copy()
    agg["white_win_rate"] = agg["white_wins"] / agg["games"]
    return agg


def opening_variance(by_group: pd.DataFrame) -> pd.DataFrame:
    pivot = by_group.pivot_table(
        index=["eco_code", "opening_name"],
        columns="rating_group",
        values="white_win_rate",
    )
    group_cols = [g for g in RATING_GROUP_ORDER if g in pivot.columns]
    pivot      = pivot.reindex(columns=group_cols)
    pivot["variance"] = pivot[group_cols].var(axis=1,  skipna=True)
    pivot["std_dev"]  = pivot[group_cols].std(axis=1,  skipna=True)
    pivot["range"]    = pivot[group_cols].max(axis=1) - pivot[group_cols].min(axis=1)
    pivot["n_groups"] = pivot[group_cols].notna().sum(axis=1)
    pivot = pivot[pivot["n_groups"] >= 2]
    return pivot.sort_values("variance", ascending=False).reset_index()


def top_openings_per_group(by_group: pd.DataFrame, top_n: int = 8) -> dict:
    return {
        group: by_group[by_group["rating_group"] == group].nlargest(top_n, "white_win_rate")
        for group in RATING_GROUP_ORDER
    }


def master_vs_beginner(df: pd.DataFrame, top_n: int = 15, min_games: int = 5) -> pd.DataFrame:
    """..."""
    LOW_GROUPS  = ["beginner", "novice"]
    HIGH_GROUPS = ["master",   "expert"]

    low = (
        df[df["rating_group"].isin(LOW_GROUPS)]
        .groupby(["eco_code", "opening_name"])
        .agg(games=("result", "count"), white_wins=("white_win", "sum"))
        .reset_index()
    )
    low = low[low["games"] >= min_games]
    low["beginner_win_rate"] = low["white_wins"] / low["games"]

    high = (
        df[df["rating_group"].isin(HIGH_GROUPS)]
        .groupby(["eco_code", "opening_name"])
        .agg(games=("result", "count"), white_wins=("white_win", "sum"))
        .reset_index()
    )
    high = high[high["games"] >= min_games]
    high["master_win_rate"] = high["white_wins"] / high["games"]

    merged = low.merge(
        high[["eco_code", "opening_name", "master_win_rate"]],
        on=["eco_code", "opening_name"],
        how="inner",
    )
    merged["gap"]     = merged["master_win_rate"] - merged["beginner_win_rate"]
    merged["abs_gap"] = merged["gap"].abs()
    return merged.nlargest(top_n, "abs_gap").reset_index(drop=True)


def acpl_by_line_length(df: pd.DataFrame) -> pd.DataFrame:
    needed = ["eco_line_length", "post_opening_acpl"]
    if not all(c in df.columns for c in needed):
        return pd.DataFrame()

    sub = df[needed].dropna()
    if sub.empty:
        return pd.DataFrame()

    agg = (
        sub.groupby("eco_line_length")["post_opening_acpl"]
        .agg(games="count", mean_acpl="mean", std_acpl="std")
        .reset_index()
    )
    return agg[agg["games"] >= 10].copy()


def short_name(name: str, max_len: int = 28) -> str:
    return name if len(name) <= max_len else name[:max_len - 1] + "…"


def plot_top_openings_by_group(top_dict: dict, outpath: str) -> None:
    groups = [g for g in RATING_GROUP_ORDER if g in top_dict and not top_dict[g].empty]
    n_cols = 2
    n_rows = (len(groups) + 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, n_rows * 4.5))
    axes   = axes.flatten()
    colors = plt.cm.tab10.colors

    for i, group in enumerate(groups):
        ax  = axes[i]
        sub = top_dict[group].copy()
        sub["label"] = sub["opening_name"].apply(short_name)
        bars = ax.barh(sub["label"][::-1], sub["white_win_rate"][::-1] * 100,
                       color=colors[i % len(colors)], edgecolor="white", linewidth=0.5)
        ax.set_title(f"{group.capitalize()} players", fontsize=13, fontweight="bold", pad=8)
        ax.set_xlabel("White win rate (%)", fontsize=10)
        ax.xaxis.set_major_formatter(mtick.PercentFormatter())
        ax.set_xlim(0, 80)
        ax.axvline(50, color="grey", linewidth=0.8, linestyle="--", alpha=0.6)
        for bar, (_, row) in zip(bars[::-1], sub.iterrows()):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                    f"n={row['games']}", va="center", fontsize=7.5, color="dimgrey")
        ax.spines[["top", "right"]].set_visible(False)

    for j in range(len(groups), len(axes)):
        axes[j].set_visible(False)

    fig.suptitle("Top Chess Openings by White Win Rate per Rating Group",
                 fontsize=16, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(outpath, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {outpath}")


def plot_variance_chart(variance_df: pd.DataFrame, outpath: str, top_n: int = 15) -> None:
    sub = variance_df.head(top_n).copy()
    sub["label"] = sub["opening_name"].apply(short_name)

    fig, ax = plt.subplots(figsize=(11, 7))
    bars = ax.barh(sub["label"][::-1], sub["std_dev"][::-1] * 100,
                   color="#e07b39", edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Std. dev. of white win rate across rating groups (pp)", fontsize=11)
    ax.set_title(f"Top {top_n} Openings With Highest Win-Rate Variance Across Rating Groups",
                 fontsize=13, fontweight="bold", pad=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter())
    for bar, (_, row) in zip(bars[::-1], sub.iterrows()):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
                f"{row['std_dev']*100:.1f}pp", va="center", fontsize=8.5)
    plt.tight_layout()
    plt.savefig(outpath, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {outpath}")


def plot_heatmap(by_group: pd.DataFrame, overall: pd.DataFrame,
                 outpath: str, top_n: int = 20) -> None:
    top_openings = overall.nlargest(top_n, "games")["eco_code"].tolist()
    sub = by_group[by_group["eco_code"].isin(top_openings)].copy()

    pivot = sub.pivot_table(index="opening_name", columns="rating_group",
                            values="white_win_rate", aggfunc="mean")
    pivot = pivot.reindex(columns=[g for g in RATING_GROUP_ORDER if g in pivot.columns])
    pivot.index = [short_name(n, 32) for n in pivot.index]

    fig, ax = plt.subplots(figsize=(12, max(6, len(pivot) * 0.55)))
    im = ax.imshow(pivot.values * 100, aspect="auto", cmap="RdYlGn", vmin=30, vmax=70)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([c.capitalize() for c in pivot.columns], fontsize=10)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=9)

    for r in range(len(pivot.index)):
        for c in range(len(pivot.columns)):
            val = pivot.values[r, c]
            if not np.isnan(val):
                ax.text(c, r, f"{val*100:.0f}%", ha="center", va="center",
                        fontsize=8, color="black" if 35 < val * 100 < 65 else "white")

    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_label("White win rate (%)", fontsize=10)
    ax.set_title(f"White Win Rate Heatmap — Top {top_n} Most-Played Openings by Rating Group",
                 fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(outpath, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {outpath}")


def plot_overall_distribution(overall: pd.DataFrame, outpath: str, top_n: int = 20) -> None:
    sub = overall.nlargest(top_n, "games").copy()
    sub["label"] = sub["opening_name"].apply(lambda n: short_name(n, 30))
    sub = sub.sort_values("white_win_rate")

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.barh(sub["label"], sub["white_win_rate"] * 100, color="#4a90d9", label="White wins")
    ax.barh(sub["label"], sub["draw_rate"] * 100,
            left=sub["white_win_rate"] * 100, color="#b0b0b0", label="Draw")
    ax.barh(sub["label"], sub["black_win_rate"] * 100,
            left=(sub["white_win_rate"] + sub["draw_rate"]) * 100,
            color="#e05c5c", label="Black wins")
    ax.axvline(50, color="black", linewidth=0.8, linestyle="--", alpha=0.5)
    ax.set_xlabel("Share of outcomes (%)", fontsize=11)
    ax.set_title(f"Outcome Distribution for Top {top_n} Most-Played Openings (All Rating Groups)",
                 fontsize=13, fontweight="bold", pad=10)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter())
    ax.legend(loc="lower right", fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    plt.savefig(outpath, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {outpath}")


def plot_master_vs_beginner(comparison_df: pd.DataFrame, outpath: str) -> None:
    if comparison_df.empty:
        print(f"  Skipped (no data): {outpath}")
        return

    df = comparison_df.copy().sort_values("gap")
    df["label"] = df["opening_name"].apply(short_name)

    y      = np.arange(len(df))
    height = 0.35

    fig, ax = plt.subplots(figsize=(13, max(6, len(df) * 0.6)))
    ax.barh(y + height / 2, df["master_win_rate"]   * 100,
            height, color="#2166ac", label="Master / Expert",   alpha=0.9)
    ax.barh(y - height / 2, df["beginner_win_rate"] * 100,
            height, color="#d73027", label="Beginner / Novice", alpha=0.9)

    for i, (_, row) in enumerate(df.iterrows()):
        gap_pct = row["gap"] * 100
        sign    = "+" if gap_pct >= 0 else ""
        ax.text(
            max(row["master_win_rate"], row["beginner_win_rate"]) * 100 + 0.8,
            i, f"gap: {sign}{gap_pct:.1f}pp",
            va="center", fontsize=8, color="dimgrey",
        )

    ax.set_yticks(y)
    ax.set_yticklabels(df["label"], fontsize=9)
    ax.axvline(50, color="grey", linewidth=0.8, linestyle="--", alpha=0.6)
    ax.set_xlabel("White win rate (%)", fontsize=11)
    ax.set_title(
        "White Win Rate: Master/Expert vs Beginner/Novice per Opening\n"
        "(positive gap = opening favours stronger players in practice)",
        fontsize=13, fontweight="bold", pad=12,
    )
    ax.xaxis.set_major_formatter(mtick.PercentFormatter())
    ax.legend(fontsize=10, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    plt.savefig(outpath, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {outpath}")


def plot_line_length_vs_acpl(acpl_df: pd.DataFrame, outpath: str) -> None:
    if acpl_df.empty:
        print(f"  Skipped (no ACPL data available): {outpath}")
        return

    x = acpl_df["eco_line_length"].values
    y = acpl_df["mean_acpl"].values
    n = acpl_df["games"].values

    slope, intercept, r_value, p_value, _ = stats.linregress(x, y)
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = slope * x_line + intercept

    fig, ax = plt.subplots(figsize=(10, 6))
    scatter = ax.scatter(x, y, s=np.sqrt(n) * 3, alpha=0.7,
                         c=y, cmap="RdYlGn_r", edgecolors="white", linewidth=0.5)
    ax.plot(x_line, y_line, color="#333333", linewidth=1.5, linestyle="--",
            label=f"Linear fit  r = {r_value:.3f},  p = {p_value:.3f}")

    cbar = fig.colorbar(scatter, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_label("Mean ACPL (centipawns)", fontsize=9)

    ax.set_xlabel("ECO theoretical line length (half-moves)", fontsize=11)
    ax.set_ylabel("Mean post-opening ACPL (centipawns)", fontsize=11)
    ax.set_title(
        "Opening Line Length vs Post-Opening Average Centipawn Loss\n"
        "(point size ∝ number of games; lower ACPL = more accurate play)",
        fontsize=13, fontweight="bold", pad=12,
    )
    ax.legend(fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)

    direction = ("longer openings → worse midgame accuracy" if slope > 0
                 else "longer openings → better midgame accuracy")
    sig = "significant" if p_value < 0.05 else "not significant"
    ax.annotate(
        f"{direction}\n(r={r_value:.3f}, {sig})",
        xy=(0.03, 0.93), xycoords="axes fraction", fontsize=9, color="dimgrey",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7),
    )
    plt.tight_layout()
    plt.savefig(outpath, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {outpath}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyse chess opening win rates from the integrated Lichess dataset."
    )
    parser.add_argument("--input",     type=str, required=True,
                        help="Path to the integrated CSV produced by integrate_data.py")
    parser.add_argument("--outdir",    type=str, default="results",
                        help="Directory to write CSV summaries and chart images")
    parser.add_argument("--min-games", type=int, default=30,
                        help="Minimum games per opening to include in analysis (default: 30)")
    parser.add_argument("--top-n",     type=int, default=8,
                        help="Top openings per rating group in bar chart (default: 8)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    os.makedirs(args.outdir, exist_ok=True)

    df = load_data(args.input)
    df = encode_result(df)
    present_groups = [g for g in RATING_GROUP_ORDER if g in df["rating_group"].unique()]
    df["rating_group"] = pd.Categorical(df["rating_group"],
                                        categories=present_groups, ordered=True)

    print("\n--- Computing overall win rates ---")
    overall = overall_winrates(df, args.min_games)
    print(f"  {len(overall):,} openings meet the min-games threshold ({args.min_games}).")

    print("\n--- Computing win rates by rating group ---")
    by_group = winrates_by_group(df, args.min_games)

    print("\n--- Computing cross-group variance (Q2) ---")
    variance = opening_variance(by_group)

    print("\n--- Identifying top openings per group (Q4, Q5) ---")
    top_dict = top_openings_per_group(by_group, top_n=args.top_n)

    print("\n--- Computing master vs beginner comparison (Q1) ---")
    comparison = master_vs_beginner(df, top_n=15)
    if not comparison.empty:
        print(comparison[["opening_name", "master_win_rate",
                           "beginner_win_rate", "gap"]].to_string(
            index=False, float_format=lambda x: f"{x:.1%}"))

    print("\n--- Computing line length vs ACPL (Q3) ---")
    acpl_agg = acpl_by_line_length(df)
    if acpl_agg.empty:
        print("  No post-opening ACPL data found — Q3 chart will be skipped.")
        print("  (Ensure you are using a 2017+ Lichess dataset with eval annotations.)")
    else:
        print(f"  {len(acpl_agg)} line-length buckets with ≥10 games.")

    print("\n--- Saving CSV summaries ---")
    paths = {
        "overall":    os.path.join(args.outdir, "opening_winrates_overall.csv"),
        "by_group":   os.path.join(args.outdir, "opening_winrates_by_group.csv"),
        "variance":   os.path.join(args.outdir, "opening_variance.csv"),
        "acpl":       os.path.join(args.outdir, "opening_acpl_by_length.csv"),
        "comparison": os.path.join(args.outdir, "master_vs_beginner.csv"),
    }
    overall.to_csv(paths["overall"],       index=False)
    by_group.to_csv(paths["by_group"],     index=False)
    variance.to_csv(paths["variance"],     index=False)
    acpl_agg.to_csv(paths["acpl"],         index=False)
    comparison.to_csv(paths["comparison"], index=False)
    for p in paths.values():
        print(f"  Saved: {p}")

    print("\n=== Top 10 Openings by White Win Rate (all groups) ===")
    cols = ["eco_code", "opening_name", "games",
            "white_win_rate", "draw_rate", "black_win_rate"]
    print(overall[cols].head(10).to_string(
        index=False, float_format=lambda x: f"{x:.1%}"))

    print("\n=== Top 10 High-Variance Openings (theory vs practice gap) ===")
    if not variance.empty:
        vcols = ["eco_code", "opening_name", "std_dev", "n_groups"]
        print(variance[vcols].head(10).to_string(
            index=False, float_format=lambda x: f"{x:.3f}"))

    print("\n--- Generating charts ---")
    plot_top_openings_by_group(
        top_dict,   os.path.join(args.outdir, "top_openings_by_group.png"))
    if not variance.empty:
        plot_variance_chart(
            variance, os.path.join(args.outdir, "winrate_variance_chart.png"))
    plot_heatmap(
        by_group, overall, os.path.join(args.outdir, "winrate_heatmap.png"))
    plot_overall_distribution(
        overall,  os.path.join(args.outdir, "outcome_distribution.png"))
    plot_master_vs_beginner(
        comparison, os.path.join(args.outdir, "master_vs_beginner.png"))
    plot_line_length_vs_acpl(
        acpl_agg, os.path.join(args.outdir, "line_length_vs_acpl.png"))

    print(f"\nDone. All results written to: {args.outdir}/")


if __name__ == "__main__":
    main()
