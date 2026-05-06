import argparse
import csv
import os
import re
import sys

import chess
import chess.pgn
from tqdm import tqdm


OPENING_MOVE_DEPTH = 10
MATE_CP            = 1000


def parse_result(result_str: str) -> str | None:
    mapping = {
        "1-0":     "white",
        "0-1":     "black",
        "1/2-1/2": "draw",
    }
    return mapping.get(result_str)


def extract_opening_moves(game: chess.pgn.Game, depth: int) -> tuple[str, int]:
    board  = game.board()
    moves  = []
    node   = game

    for _ in range(depth):
        next_node = node.next()
        if next_node is None:
            break
        move = next_node.move
        moves.append(board.san(move))
        board.push(move)
        node = next_node

    return " ".join(moves), len(moves)


_EVAL_RE = re.compile(r"\[%eval\s+([^\]]+)\]")

def parse_eval(comment: str) -> float | None:
    match = _EVAL_RE.search(comment)
    if not match:
        return None
    raw = match.group(1).strip()
    if raw.startswith("#"):
        try:
            n = int(raw[1:])
            return float(MATE_CP) if n > 0 else float(-MATE_CP)
        except ValueError:
            return None
    try:
        return float(raw)
    except ValueError:
        return None


def compute_post_opening_acpl(game: chess.pgn.Game,
                               opening_depth: int) -> float | None:
    evals_with_color: list[tuple[float, chess.Color]] = []
    node   = game
    ply    = 0

    while True:
        next_node = node.next()
        if next_node is None:
            break
        ply  += 1
        color = chess.WHITE if (ply % 2 == 1) else chess.BLACK
        ev    = parse_eval(next_node.comment)
        if ev is not None:
            evals_with_color.append((ev, color, ply))
        node = next_node

    cpl_values: list[float] = []

    for i in range(1, len(evals_with_color)):
        e_before, _,      ply_before = evals_with_color[i - 1]
        e_after,  color,  ply_after  = evals_with_color[i]

        if ply_after <= opening_depth:
            continue

        if color == chess.WHITE:
            cpl = max(0.0, e_before - e_after) * 100
        else:
            cpl = max(0.0, e_after - e_before) * 100

        cpl = min(cpl, float(MATE_CP * 100))
        cpl_values.append(cpl)

    if len(cpl_values) < 2:
        return None

    return round(sum(cpl_values) / len(cpl_values), 2)


def count_moves(game: chess.pgn.Game) -> int:
    count = 0
    node  = game
    while node.next() is not None:
        count += 1
        node   = node.next()
    return count


def clean_pgn(
    input_path:  str,
    output_path: str,
    min_moves:   int       = 5,
    max_games:   int | None = None,
) -> None:

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = [
        "white_elo",
        "black_elo",
        "result",
        "time_control",
        "opening_moves",
        "num_opening_moves",
        "post_opening_acpl",
    ]

    total_read    = 0
    total_written = 0
    total_skipped = 0
    games_with_eval = 0

    print(f"Reading : {input_path}")
    print(f"Writing : {output_path}")
    print(f"Min moves filter : {min_moves} half-moves")
    if max_games:
        print(f"Max games cap    : {max_games:,}")

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
                headers    = game.headers

                white_elo    = headers.get("WhiteElo", "?")
                black_elo    = headers.get("BlackElo", "?")
                result_raw   = headers.get("Result", "*")
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

                if count_moves(game) < min_moves:
                    total_skipped += 1
                    progress.update(1)
                    continue

                opening_moves, num_opening_moves = extract_opening_moves(
                    game, OPENING_MOVE_DEPTH
                )
                post_opening_acpl = compute_post_opening_acpl(
                    game, OPENING_MOVE_DEPTH
                )

                if post_opening_acpl is not None:
                    games_with_eval += 1

                writer.writerow({
                    "white_elo":         int(white_elo),
                    "black_elo":         int(black_elo),
                    "result":            result,
                    "time_control":      time_control,
                    "opening_moves":     opening_moves,
                    "num_opening_moves": num_opening_moves,
                    "post_opening_acpl": post_opening_acpl if post_opening_acpl is not None else "",
                })

                total_written += 1
                progress.update(1)

                if max_games and total_written >= max_games:
                    print(f"\nReached max-games cap of {max_games:,}. Stopping.")
                    break

    print(f"\n--- Summary ---")
    print(f"Total games read         : {total_read:,}")
    print(f"Games written (CSV)      : {total_written:,}")
    print(f"Games skipped            : {total_skipped:,}")
    print(f"Games with eval data     : {games_with_eval:,} "
          f"({100*games_with_eval/max(total_written,1):.1f}%)")
    print(f"Output                   : {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Clean a raw Lichess PGN file into a structured CSV."
    )
    parser.add_argument("--input",     type=str, required=True,
                        help="Path to the input .pgn file")
    parser.add_argument("--output",    type=str, required=True,
                        help="Path for the output .csv file")
    parser.add_argument("--min-moves", type=int, default=5,
                        help="Minimum half-moves to keep a game (default: 5)")
    parser.add_argument("--max-games", type=int, default=None,
                        help="Maximum valid games to write (useful for testing)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    clean_pgn(
        input_path  = args.input,
        output_path = args.output,
        min_moves   = args.min_moves,
        max_games   = args.max_games,
    )


if __name__ == "__main__":
    main()
