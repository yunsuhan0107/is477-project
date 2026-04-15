import argparse
import hashlib
import os
import sys

import requests
import zstandard as zstd
from tqdm import tqdm

BASE_URL = "https://database.lichess.org/standard"

CHUNK_SIZE = 8 * 1024 * 1024


def build_url(year: int, month: int) -> str:
    return f"{BASE_URL}/lichess_db_standard_rated_{year}-{month:02d}.pgn.zst"


def build_output_path(outdir: str, year: int, month: int) -> str:
    filename = f"lichess_{year}-{month:02d}.pgn"
    return os.path.join(outdir, filename)


def stream_download_and_decompress(url: str, output_path: str) -> None:
    print(f"Downloading: {url}")
    print(f"Writing to:  {output_path}")

    head = requests.head(url, timeout=30)
    head.raise_for_status()
    total_compressed = int(head.headers.get("Content-Length", 0))

    decompressor = zstd.ZstdDecompressor()

    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()

        with open(output_path, "wb") as out_file:
            with decompressor.stream_writer(out_file, closefd=False) as decom_stream:
                with tqdm(
                    total=total_compressed,
                    unit="B",
                    unit_scale=True,
                    desc="Downloading",
                ) as progress:
                    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk:
                            decom_stream.write(chunk)
                            progress.update(len(chunk))

    print(f"\nDownload complete: {output_path}")


def compute_md5(filepath: str) -> str:
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def save_checksum(filepath: str, checksum: str) -> None:
    checksum_path = filepath + ".md5"
    with open(checksum_path, "w") as f:
        f.write(f"{checksum}  {os.path.basename(filepath)}\n")
    print(f"Checksum saved: {checksum_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True, choices=range(1, 13), metavar="MONTH")
    parser.add_argument("--outdir", type=str, default="data/raw")
    parser.add_argument("--checksum", action="store_true")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    url = build_url(args.year, args.month)
    output_path = build_output_path(args.outdir, args.year, args.month)

    if os.path.exists(output_path):
        print(f"File already exists, skipping download: {output_path}")
        sys.exit(0)

    try:
        stream_download_and_decompress(url, output_path)
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error during download: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        sys.exit(1)

    if args.checksum:
        print("Computing MD5 checksum...")
        checksum = compute_md5(output_path)
        print(f"MD5: {checksum}")
        save_checksum(output_path, checksum)


if __name__ == "__main__":
    main()