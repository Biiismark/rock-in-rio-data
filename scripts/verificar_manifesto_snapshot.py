#!/usr/bin/env python3
"""Verify files in a pinned Rock in Rio dataset checkout against its Git blob manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the size and Git blob SHA of each file in the freeze manifest."
    )
    parser.add_argument("--manifest", required=True, type=Path, help="CSV manifest file")
    parser.add_argument("--root", required=True, type=Path, help="Checkout root containing dados/")
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    root = args.root.resolve()
    checked = 0
    errors: list[str] = []

    with manifest_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"path", "bytes", "git_blob_sha"}
        if not required.issubset(reader.fieldnames or set()):
            parser.error(f"Manifest must contain columns: {', '.join(sorted(required))}")

        for row in reader:
            relative = Path(row["path"])
            target = (root / relative).resolve()
            if not target.is_relative_to(root):
                errors.append(f"PATH_OUTSIDE_ROOT: {row['path']}")
                continue
            if not target.is_file():
                errors.append(f"MISSING: {row['path']}")
                continue

            checked += 1
            actual_size = target.stat().st_size
            if actual_size != int(row["bytes"]):
                errors.append(
                    f"SIZE_MISMATCH: {row['path']} expected={row['bytes']} actual={actual_size}"
                )
                continue

            actual_sha = git_blob_sha1(target)
            if actual_sha != row["git_blob_sha"]:
                errors.append(
                    f"GIT_BLOB_MISMATCH: {row['path']} expected={row['git_blob_sha']} actual={actual_sha}"
                )

    print(f"Arquivos verificados: {checked}")
    print(f"Falhas: {len(errors)}")
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
