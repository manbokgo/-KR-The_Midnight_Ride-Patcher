"""Match a TMR MO2 profile against local Korean translation source dictionaries.

Development helper only. Local source paths are provided by command-line arguments and
are never embedded into release metadata.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import tmrkr


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def files_by_norm(root: Path, suffix: str) -> dict[str, list[Path]]:
    result: dict[str, list[Path]] = {}
    for path in root.glob(f"*{suffix}"):
        stem = path.name[: -len(suffix)] if suffix else path.stem
        result.setdefault(norm(stem), []).append(path)
    return result


PLUGIN_ALIASES = {
    "ppf": "ppf_en_ko.sst",
}

TRANSLATION_TXT_ALIASES = {
    "mcm_en.txt": "mcm_mcm_en_ko.sst",
    "safe travels_en.txt": "safe travels_mcm_en_ko.sst",
}


def find_sst(plugin: str, sst_dir: Path, index: dict[str, list[Path]]) -> list[str]:
    stem = Path(plugin).stem
    alias = PLUGIN_ALIASES.get(stem.casefold())
    if alias and (sst_dir / alias).is_file():
        return [str((sst_dir / alias).resolve())]

    wanted = norm(stem + "_en_ko")
    exact = index.get(wanted, [])
    if exact:
        return [str(path.resolve()) for path in exact]

    base = norm(stem)
    candidates = []
    for key, paths in index.items():
        candidate_base = key.removesuffix("enko")
        if key.startswith(base) or base.startswith(candidate_base):
            candidates.extend(paths)
    return [str(path.resolve()) for path in candidates[:10]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mo2-root", type=Path, required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--sst-dir", type=Path, required=True)
    parser.add_argument("--mcmdb-dir", type=Path, required=True)
    parser.add_argument("--base-korean", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    install = tmrkr.Installation(args.mo2_root, args.profile)
    sst_index = files_by_norm(args.sst_dir, ".sst")
    mcmdb_index = files_by_norm(args.mcmdb_dir, ".mcmdb")

    plugins = []
    official = {
        "fallout4.esm", "dlcrobot.esm", "dlcworkshop01.esm", "dlccoast.esm",
        "dlcworkshop02.esm", "dlcworkshop03.esm", "dlcnukaworld.esm",
    }
    for plugin in install.active:
        lower = plugin.casefold()
        if lower in official or (lower.startswith("cc") and lower.endswith(".esl")):
            continue
        chain = install.providers.get(lower, [{}])
        plugins.append({
            "plugin": plugin,
            "provider": chain[-1].get("provider"),
            "sst_candidates": find_sst(plugin, args.sst_dir, sst_index),
        })

    mcm_json = []
    translations_txt = []
    for _, chain in sorted(install.providers.items()):
        winner = chain[-1]
        lower = winner["path"].casefold()
        physical = Path(winner["physical"])
        if lower.endswith("/config.json") and lower.startswith("mcm/config/"):
            config_name = physical.parent.name
            wanted = norm(config_name + "_config_en_ko")
            mcm_json.append({
                "provider": winner["provider"],
                "path": winner["path"],
                "config_name": config_name,
                "mcmdb_candidates": [str(p.resolve()) for p in mcmdb_index.get(wanted, [])],
            })
        elif lower.startswith("interface/translations/") and lower.endswith("_en.txt"):
            alias = TRANSLATION_TXT_ALIASES.get(physical.name.casefold())
            if alias and (args.sst_dir / alias).is_file():
                candidates = [args.sst_dir / alias]
            else:
                wanted = norm(physical.stem + "_ko")
                candidates = sst_index.get(wanted, [])
            translations_txt.append({
                "provider": winner["provider"],
                "path": winner["path"],
                "sst_candidates": [str(p.resolve()) for p in candidates],
            })

    base_files = [
        path.relative_to(args.base_korean).as_posix()
        for path in sorted(args.base_korean.rglob("*"))
        if path.is_file()
    ]

    report = {
        "schema_version": 1,
        "mo2_root": str(args.mo2_root.resolve()),
        "profile": args.profile,
        "plugins": plugins,
        "mcm_json": mcm_json,
        "interface_translations": translations_txt,
        "base_korean": {
            "root": str(args.base_korean.resolve()),
            "files": base_files,
        },
        "warnings": install.warnings,
    }
    tmrkr.write_json(args.output, report)
    print(json.dumps({
        "plugins": len(plugins),
        "plugins_with_sst": sum(bool(row["sst_candidates"]) for row in plugins),
        "mcm_json": len(mcm_json),
        "mcmdb_matched": sum(bool(row["mcmdb_candidates"]) for row in mcm_json),
        "translations_txt": len(translations_txt),
        "translations_sst_matched": sum(bool(row["sst_candidates"]) for row in translations_txt),
        "output": str(args.output.resolve()),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
