"""Build a Fallout 4 + official DLC fallback translation bank."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from export_plugin_sst import export_sst

SOURCES = [
    ("fallout4_en_ko.sst", ["fallout4.esm"]),
    ("dlcrobot_en_ko.sst", ["fallout4.esm", "dlcrobot.esm"]),
    ("dlcworkshop01_en_ko.sst", ["fallout4.esm", "dlcworkshop01.esm"]),
    ("dlccoast_en_ko.sst", ["fallout4.esm", "dlccoast.esm"]),
    ("dlcworkshop02_en_ko.sst", ["fallout4.esm", "dlcworkshop02.esm"]),
    ("DLCworkshop03_en_ko.sst", ["fallout4.esm", "dlcworkshop03.esm"]),
    ("dlcnukaworld_en_ko.sst", ["fallout4.esm", "dlcnukaworld.esm"]),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sst-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows = []
    source_stats = []
    for name, masters in SOURCES:
        path = args.sst_dir / name
        if not path.is_file():
            raise FileNotFoundError(path)
        data = export_sst(path, plugins_override=masters)
        for row in data["mappings"]:
            rows.append({**row, "origin": "base_inherited"})
        source_stats.append({
            "file": name,
            "target": data["target"],
            "mappings": len(data["mappings"]),
        })

    unique = {}
    for row in rows:
        key = (
            row["owner"].casefold(),
            row["id"].upper(),
            row["record"],
            row["field"],
            row["rec_id"],
            row["source"],
            row["dest"],
        )
        unique[key] = row

    output = {
        "schema_version": 1,
        "kind": "fallout4_base_dlc_fallback",
        "sources": source_stats,
        "mappings": list(unique.values()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "sources": len(source_stats),
        "input_rows": len(rows),
        "unique_rows": len(unique),
        "output": str(args.output.resolve()),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
