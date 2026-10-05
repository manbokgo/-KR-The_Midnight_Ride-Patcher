"""Build development-only MCM JSON payloads from .mcmdb dictionaries."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tmrkr_mcm import translate_mcm_json


MCM_TARGETS = [
    ("Complex Vendors", "Complex Vendors_config_en_ko.mcmdb"),
    ("CraftingHighlightFix", "CraftingHighlightFix_config_en_ko.mcmdb"),
    ("LegendariesTheyCanUse", "LegendariesTheyCanUse_config_en_ko.mcmdb"),
    ("UnlimitedSurvivalMode", "UnlimitedSurvivalMode_config_en_ko.mcmdb"),
    ("Upscaling", "Upscaling_config_en_ko.mcmdb"),
]


def find_config(mods: Path, config_name: str) -> Path:
    matches = list(mods.glob(f"*/MCM/Config/{config_name}/config.json"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one config for {config_name}, found {len(matches)}")
    return matches[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mods", type=Path, required=True)
    parser.add_argument("--translator-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    exe = args.translator_root / "SimpleMcmJsonTranslator.exe"
    db_dir = args.translator_root / "db"
    export_dir = args.output_root / "_mappings"
    results = []

    for config_name, db_name in MCM_TARGETS:
        source = find_config(args.mods, config_name)
        mapping = export_dir / (Path(db_name).stem + ".json")
        subprocess.run([
            "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(ROOT / "tools" / "export_mcmdb.ps1"),
            "-TranslatorExe", str(exe),
            "-Database", str(db_dir / db_name),
            "-Output", str(mapping),
        ], check=True, capture_output=True)

        relative = Path("MCM") / "Config" / config_name / "config.json"
        report = translate_mcm_json(source, mapping, args.output_root / relative)
        results.append(report)
        print(f"{config_name}: {report['matched']} replacements "
              f"from {report['mapping_entries']} dictionary entries")

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
