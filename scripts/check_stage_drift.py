#!/usr/bin/env python3
"""Check exeqpdal stage-factory coverage against PDAL.

Two assertions:

1. The factory set covers every stage registered by the local PDAL binary
   (``pdal --drivers``). Stages the binary lacks (optional plugins) are fine.
2. Every factory name appears in the pinned list of stage names documented
   for the targeted PDAL release (``scripts/stages-2.10.txt``).

Exits 0 when both hold, 1 on drift. The PDAL binary is taken from the
``--pdal`` argument, the ``PDAL_EXECUTABLE`` environment variable, or
``pdal`` on PATH, in that order.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PINNED_LIST = Path(__file__).resolve().parent / "stages-2.10.txt"
STAGE_MODULES = [
    REPO_ROOT / "exeqpdal" / "stages" / name for name in ("readers.py", "filters.py", "writers.py")
]
STAGE_NAME = re.compile(r'"((?:readers|filters|writers)\.[A-Za-z0-9_]+)"')

# Registered by the binary but absent from the PDAL 2.10.1 documentation
# (compiled legacy plugin); deliberately not wrapped.
UNDOCUMENTED_DRIVERS = {"readers.icebridge"}


def factory_names() -> set[str]:
    names: set[str] = set()
    for module in STAGE_MODULES:
        names.update(STAGE_NAME.findall(module.read_text(encoding="utf-8")))
    return names


def driver_names(pdal: str) -> set[str]:
    result = subprocess.run(
        [pdal, "--drivers", "--showjson"],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=True,
    )
    drivers = json.loads(result.stdout)
    return {
        d["name"] for d in drivers if d["name"].split(".")[0] in ("readers", "filters", "writers")
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pdal", default=os.environ.get("PDAL_EXECUTABLE", "pdal"), help="PDAL executable"
    )
    args = parser.parse_args()

    factories = factory_names()
    drivers = driver_names(args.pdal) - UNDOCUMENTED_DRIVERS
    pinned = {
        line.strip()
        for line in PINNED_LIST.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }

    missing = sorted(drivers - factories)
    unpinned = sorted(factories - pinned)

    print(f"factories: {len(factories)}  drivers: {len(drivers)}  pinned: {len(pinned)}")
    ok = True
    if missing:
        ok = False
        print(f"DRIFT: binary registers {len(missing)} stage(s) without a factory:")
        for name in missing:
            print(f"  {name}")
    if unpinned:
        ok = False
        print(f"DRIFT: {len(unpinned)} factory name(s) not in the pinned list:")
        for name in unpinned:
            print(f"  {name}")
    if ok:
        print("OK: factories cover all binary drivers and match the pinned list")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
