import argparse
import os
import sys

import pandas as pd
import requests
from tqdm import tqdm

ECO_URLS = [
    "https://raw.githubusercontent.com/lichess-org/chess-openings/master/a.tsv",
    "https://raw.githubusercontent.com/lichess-org/chess-openings/master/b.tsv",
    "https://raw.githubusercontent.com/lichess-org/chess-openings/master/c.tsv",
    "https://raw.githubusercontent.com/lichess-org/chess-openings/master/d.tsv",
    "https://raw.githubusercontent.com/lichess-org/chess-openings/master/e.tsv",
]

ECO_CACHE_PATH = "data/eco/eco_openings.csv"

RATING_BINS = [0, 1000, 1300, 1600, 1900, 2200, 3500]
RATING_LABELS = ["beginner", "novice", "intermediate", "advanced", "expert", "master"]


def download_eco_database(cache_path: str) -> pd.DataFrame:
    if os.path.exists(cache_path):
        print(f"Loading cached ECO database from: {cache_path}")
        return pd.read_csv(cache_path)

    print("Downloading ECO database from GitHub...")
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    frames = []
    for url in ECO_URLS:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        from io import StringIO
        df = pd.read_csv(StringIO(response.text), sep="\t")
        frames.append(df)
        print(f"  Downloaded: {url.split('/')[-1]} ({len(df)} openings)")

    eco_df = pd.concat(frames, ignore_index=True)

    eco_df = eco_df.rename(columns={"pgn": "moves", "eco": "eco_code"})

    eco_df["moves_clean"] = eco_df["moves"].apply(normalise_moves)

    eco_df.to_csv(cache_path, index=False)
    print(f"ECO database cached to: {cache_path} ({len(eco_df)} total openings)")
    return eco_df


def normalise_moves(pgn_moves: str) -> str:
    import re
    cleaned = re.sub(r"\d+\.+\s*", "", str(pgn_moves))
    cleaned = " ".join(cleaned.split())
    return cleaned


def build_eco_lookup(eco_df: pd.DataFrame) -> dict:
    lookup = {}
    for _, row in eco_df.iterrows():
        moves_clean = row["moves_clean"]
        lookup[moves_clean] = (row["eco_code"], row["name"])
    return lookup


def match_opening(opening_moves: str, lookup: dict, max_depth: int = 10) -> tuple:
    tokens = opening_moves.strip().split()

    for length in range(min(len(tokens), max_depth), 0, -1):
        prefix = " ".join(tokens[:length])
        if prefix in lookup:
            return lookup[prefix]

    return ("Unknown", "Unknown")


def assign_rating_group(elo: int) -> str:
    for i, threshold in enumerate(RATING_BINS[1:]):
        if elo < threshold:
            return RATING_LABELS[i]
    return RATING_LABELS[-1]


def integrate(games_path: str, output_path: str) -> None:
    print(f"Loading cleaned games from: {games_path}")
    games_df = pd.read_csv(games_path)
    print(f"  {len(games_df):,} games loaded.")

    eco_df = download_eco_database(ECO_CACHE_PATH)
    lookup = build_eco_lookup(eco_df)
    print(f"  {len(lookup):,} unique opening positions in lookup table.")

    print("Matching games to ECO openings...")
    eco_codes = []
    opening_names = []

    for moves in tqdm(games_df["opening_moves"], desc="Matching openings", unit=" games"):
        eco_code, opening_name = match_opening(str(moves), lookup)
        eco_codes.append(eco_code)
        opening_names.append(opening_name)

    games_df["eco_code"] = eco_codes
    games_df["opening_name"] = opening_names

    games_df["avg_elo"] = ((games_df["white_elo"] + games_df["black_elo"]) / 2).astype(int)
    games_df["rating_group"] = games_df["avg_elo"].apply(assign_rating_group)

    matched = (games_df["eco_code"] != "Unknown").sum()
    print(f"\n--- Matching Summary ---")
    print(f"Games matched to an opening: {matched:,} / {len(games_df):,} "
          f"({100 * matched / len(games_df):.1f}%)")
    print(f"\nRating group distribution:")
    print(games_df["rating_group"].value_counts().to_string())

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    games_df.to_csv(output_path, index=False)
    print(f"\nIntegrated dataset saved to: {output_path}")
    print(f"Columns: {list(games_df.columns)}")


def main():
    parser = argparse.ArgumentParser(
        description="Integrate cleaned Lichess games with ECO opening database."
    )
    parser.add_argument(
        "--games", type=str, required=True,
        help="Path to the cleaned games CSV (output of clean_data.py)",
    )
    parser.add_argument(
        "--output", type=str, required=True,
        help="Path for the integrated output CSV",
    )
    args = parser.parse_args()

    if not os.path.exists(args.games):
        print(f"Error: Games file not found: {args.games}")
        sys.exit(1)

    integrate(games_path=args.games, output_path=args.output)


if __name__ == "__main__":
    main()
