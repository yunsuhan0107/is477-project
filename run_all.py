import argparse
import subprocess
import sys
import os
import time


DEFAULT_YEAR      = 2017
DEFAULT_MONTH     = 1
DEFAULT_MAX_GAMES = 10000
DEFAULT_MIN_GAMES = 30


def run_step(step_name: str, cmd: list[str]) -> None:
    print(f"\n{'='*60}")
    print(f"  STEP: {step_name}")
    print(f"  CMD:  {' '.join(cmd)}")
    print(f"{'='*60}")
    t0 = time.time()
    result = subprocess.run(cmd, check=False)
    elapsed = time.time() - t0
    if result.returncode != 0:
        print(f"\n[ERROR] Step '{step_name}' failed with exit code {result.returncode}.")
        print("Pipeline aborted.")
        sys.exit(result.returncode)
    print(f"\n[OK] {step_name} completed in {elapsed:.1f}s")


def file_exists(path: str) -> bool:
    return os.path.exists(path)


def main():
    parser = argparse.ArgumentParser(
        description="Run the full chess opening analysis pipeline end-to-end."
    )
    parser.add_argument("--year",         type=int, default=DEFAULT_YEAR)
    parser.add_argument("--month",        type=int, default=DEFAULT_MONTH)
    parser.add_argument("--max-games",    type=int, default=DEFAULT_MAX_GAMES,
                        help="Max games to extract from PGN (default: 10000)")
    parser.add_argument("--min-games",    type=int, default=DEFAULT_MIN_GAMES,
                        help="Min games per opening for analysis (default: 30)")
    parser.add_argument("--skip-acquire", action="store_true",
                        help="Skip Step 1 if the PGN file already exists locally")
    args = parser.parse_args()

    month_str   = f"{args.month:02d}"
    dataset_id  = f"lichess_{args.year}-{month_str}"
    raw_pgn     = f"data/raw/{dataset_id}.pgn"
    clean_csv   = f"data/clean/{dataset_id}.csv"
    integrated  = f"data/integrated/{dataset_id}_integrated.csv"
    results_dir = f"results/{dataset_id}"
    python      = sys.executable

    print("\n" + "="*60)
    print("  Chess Opening Analysis — Full Pipeline")
    print(f"  Dataset : {dataset_id}")
    print(f"  Max games (cleaning)  : {args.max_games:,}")
    print(f"  Min games (analysis)  : {args.min_games}")
    print("="*60)

    if args.skip_acquire and file_exists(raw_pgn):
        print(f"\n[SKIP] Step 1 — PGN already exists: {raw_pgn}")
    else:
        run_step(
            "1 — Data Acquisition (acquire_data.py)",
            [
                python, "acquire_data.py",
                "--year",  str(args.year),
                "--month", str(args.month),
                "--outdir", "data/raw",
                "--checksum",
            ],
        )

    run_step(
        "2 — Data Cleaning (clean_data.py)",
        [
            python, "clean_data.py",
            "--input",     raw_pgn,
            "--output",    clean_csv,
            "--max-games", str(args.max_games),
        ],
    )

    run_step(
        "3 — Data Integration (integrate_data.py)",
        [
            python, "integrate_data.py",
            "--games",  clean_csv,
            "--output", integrated,
        ],
    )

    run_step(
        "4 — Data Profiling (profile_data.py)",
        [
            python, "profile_data.py",
            "--cleaned",    clean_csv,
            "--integrated", integrated,
            "--outdir",     results_dir,
        ],
    )

    run_step(
        "5 — Statistical Analysis (analyze.py)",
        [
            python, "analyze.py",
            "--input",     integrated,
            "--outdir",    results_dir,
            "--min-games", str(args.min_games),
        ],
    )

    print("\n" + "="*60)
    print("  Pipeline complete!")
    print(f"  Results saved to: {results_dir}/")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
