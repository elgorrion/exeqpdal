#!/usr/bin/env python3
"""Fetch the integration-test point cloud datasets.

Downloads the test-data-v1 release assets into tests/test_data_laz/ and
verifies their SHA-256 checksums. Files already present with a matching
checksum are left alone. Exits non-zero on download failure or checksum
mismatch.
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

BASE_URL = "https://github.com/elgorrion/exeqpdal/releases/download/test-data-v1/"
DATA_DIR = Path(__file__).resolve().parent.parent / "tests" / "test_data_laz"

DATASETS = {
    "mid_laz_original.laz": "02cfd80ec8df2e18fb07cb5d8800416f0398e76b78c709a0201c262002253425",
    "mid_copc_translated.copc.laz": "b5f3e18e5711f8de93bdecdb023488fc7adc0cbb3abc9f04e39499a868e72e21",
    "sml_copc_created.copc.laz": "abbf6d33eccfe0d51b238d33d40bbcec77b987e4530a97c2757af4630fd2afed",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name, expected in DATASETS.items():
        target = DATA_DIR / name
        if target.exists() and sha256(target) == expected:
            print(f"ok (cached): {name}")
            continue
        print(f"downloading: {name}")
        tmp = target.with_suffix(target.suffix + ".part")
        urllib.request.urlretrieve(BASE_URL + name, tmp)
        actual = sha256(tmp)
        if actual != expected:
            tmp.unlink()
            print(f"CHECKSUM MISMATCH for {name}: expected {expected}, got {actual}")
            return 1
        tmp.replace(target)
        print(f"ok (downloaded): {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
