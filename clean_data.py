import argparse
import csv
import os
import re
import sys

import chess
import chess.pgn
import pandas as pd
from tqdm import tqdm

OPENING_MOVE_DEPTH = 10


def parse_result(result_str: str) -> str | None:
    mapping = {
        "1-0": "white",
        "0-1": "black",
        "1/2-1/2": "draw",
    }
    return mapping.get(result_str)


def extract_opening_moves(game: chess.pgn.Game, depth: int) -> str:
    board = game.board()
    moves = []
    node = game

    for _ in range(depth):
        next_node = node.next()
        if next_node is None:
            break
        move = next_node.move
        moves.append(board.san(move))
        board.push(move)
        node = next_node

    return " ".join(moves)


def count_moves(game: chess.pgn.Game) -> int:
    count = 0
    node = game
    while node.next() is not None:
        count += 1
        node = node.next()
    return count


def clean_pgn(
    input_path: str,
    output_path: str,
    min_moves: int = 5,
    max_games: int | None = None,
) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = [
        "white_elo",
        "black_elo",
        "result",
        "time_control",
        "opening_moves",
    ]

    total_read = 0
    total_written = 0
    total_skipped = 0

    print(f"Reading:  {input_path}")
    print(f"Writing:  {output_path}")
    print(f"Min moves filter: {min_moves} half-moves")
    if max_games:
        print(f"Max games cap: {max_games:,}")

    with open(input_path, "r", encoding="utf-8", errors="replace") as pgn_file, \
         open(output_path, "w", newline="", encoding="utf-8") as csv_file:

        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        with tqdm(desc="Games processed", unit=" games") as progress:
            while True:
                game = chess.pgn.read_game(pgn_file)
                if game is None:
                    break

                total_read += 1

                headers = game.headers
                white_elo = headers.get("WhiteElo", "?")
                black_elo = headers.get("BlackElo", "?")
                result_raw = headers.get("Result", "*")
                time_control = headers.get("TimeControl", "?")

                if white_elo == "?" or black_elo == "?":
                    total_skipped += 1
                    progress.update(1)
                    continue

                result = parse_result(result_raw)
                if result is None:
                    total_skipped += 1
                    progress.update(1)
                    continue

                move_count = count_moves(game)
                if move_count < min_moves:
                    total_skipped += 1
                    progress.update(1)
                    continue

                opening_moves = extract_opening_moves(game, OPENING_MOVE_DEPTH)

                writer.writerow({
                    "white_elo": int(white_elo),
                    "black_elo": int(black_elo),
                    "result": result,
                    "time_control": time_control,
                    "opening_moves": opening_moves,
                })

                total_written += 1
                progress.update(1)

                if max_games and total_written >= max_games:
                    print(f"\nReached max_games cap of {max_games:,}. Stopping.")
                    break

    print(f"\n--- Summary ---")
    print(f"Total games read:    {total_read:,}")
    print(f"Games written (CSV): {total_written:,}")
    print(f"Games skipped:       {total_skipped:,}")
    print(f"Output: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Clean a raw Lichess PGN file into a structured CSV."
    )
    parser.add_argument(
        "--input", type=str, required=True,
        help="Path to the input .pgn file",
    )
    parser.add_argument(
        "--output", type=str, required=True,
        help="Path for the output .csv file",
    )
    parser.add_argument(
        "--min-moves", type=int, default=5,
        help="Minimum number of half-moves for a game to be kept (default: 5)",
    )
    parser.add_argument(
        "--max-games", type=int, default=None,
        help="Maximum number of valid games to write (useful for testing)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    clean_pgn(
        input_path=args.input,
        output_path=args.output,
        min_moves=args.min_moves,
        max_games=args.max_games,
    )


if __name__ == "__main__":
    main()
