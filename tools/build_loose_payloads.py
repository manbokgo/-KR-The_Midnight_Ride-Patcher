"""Build development Interface/Translations payloads from SST dictionaries."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tmrkr_loose import translate_interface_file

TARGETS = [
    ("*/Interface/Translations/MCM_en.txt", "mcm_mcm_en_ko.sst", Path("Interface/Translations/MCM_en.txt")),
    ("*/Interface/Translations/Safe Travels_en.txt", "safe travels_mcm_en_ko.sst",
     Path("Interface/Translations/Safe Travels_en.txt")),
]


def unique_match(root: Path, pattern: str) -> Path:
    matches = list(root.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"expected one match for {pattern}, found {len(matches)}")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mods-root", type=Path, required=True)
    parser.add_argument("--sst-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    failures = 0
    for pattern, sst_name, relative in TARGETS:
        source = unique_match(args.mods_root, pattern)
        sst = args.sst_dir / sst_name
        report = translate_interface_file(source, sst, args.output_root / relative)
        print(f"{relative}: {report['matched']}/{report['translatable_lines']} matched, "
              f"{report['missing_count']} missing")
        if report["missing_count"]:
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
