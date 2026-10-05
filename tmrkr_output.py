"""Build a safe manual-copy MO2 Output tree for The Midnight Ride Korean patcher."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

import tmrkr
from tmrkr_mcm import translate_mcm_json

OFFICIAL_MASTERS = {
    "fallout4.esm", "dlcrobot.esm", "dlcworkshop01.esm", "dlccoast.esm",
    "dlcworkshop02.esm", "dlcworkshop03.esm", "dlcnukaworld.esm",
}
BASE_MOD = "TMR Korean - Base Game"
PLUGIN_MOD = "TMR Korean - Plugins"
MCM_MOD = "TMR Korean - MCM"


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _contained(root: Path, relative: str | Path) -> Path:
    root = root.resolve()
    target = (root / relative).resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"Path escapes root: {relative}")
    return target


def _copy_tree(source: Path, target: Path):
    if not source.is_dir():
        return 0
    count = 0
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        dest = _contained(target, relative)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        count += 1
    return count


def _decode_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    if raw.startswith(b"\xff\xfe"):
        return raw.decode("utf-16")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252")


def _translate_interface(source: Path, mapping_path: Path, output: Path) -> dict:
    mapping = _read_json(mapping_path)
    text = _decode_text(source)
    out = []
    matched = 0
    missing = []
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        newline = line[len(body):]
        if "\t" not in body:
            out.append(line)
            continue
        key, value = body.split("\t", 1)
        translated = mapping.get(value)
        if translated is None:
            if value and not value.startswith("$"):
                missing.append(value)
            out.append(body + newline)
        else:
            matched += 1
            out.append(key + "\t" + translated + newline)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(out), encoding="utf-8")
    return {"matched": matched, "missing": len(missing)}


def _copy_en_sidecars(source_dir: Path, target_strings: Path) -> int:
    strings = source_dir / "Strings"
    if not strings.is_dir():
        return 0
    copied = 0
    for path in strings.iterdir():
        if not path.is_file():
            continue
        lower = path.name.casefold()
        if "_en." not in lower:
            continue
        target_strings.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target_strings / path.name)
        copied += 1
    return copied


def _plugin_map(catalog_dir: Path, entry: dict) -> Path | None:
    relative = entry.get("direct_mapping")
    if not relative:
        return None
    path = _contained(catalog_dir, relative)
    return path if path.is_file() else None


def _run_fallback(source: Path, plugin: str, entry: dict | None, catalog_dir: Path, temp: Path) -> tuple[dict, Path | None]:
    backend = _contained(catalog_dir, "Backend/TmrPluginTranslator.exe")
    bank = _contained(catalog_dir, "fallback/fallout4-base-dlc-fallback.json")
    direct = _plugin_map(catalog_dir, entry or {})
    output_dir = temp / "fallback" / plugin.replace(":", "_")
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / plugin
    command = [str(backend), str(source), str(direct) if direct else "-", str(bank), str(output)]
    run = subprocess.run(command, text=True, encoding="utf-8", errors="replace",
                         capture_output=True, timeout=180)
    if run.returncode:
        raise RuntimeError(f"{plugin} fallback failed:\n{run.stderr[-4000:]}")
    detail = {}
    lines = [line for line in run.stdout.splitlines() if line.strip()]
    if lines:
        detail = json.loads(lines[-1])
    return detail, output if output.is_file() else None


def build_output(mo2_root: Path, base_package: Path, catalog_dir: Path, output: Path, profile: str | None = None) -> dict:
    installation = tmrkr.Installation(mo2_root, profile)
    catalog = _read_json(catalog_dir / "catalog.json")
    if catalog.get("schema_version") != 1:
        raise ValueError("Unsupported catalog")

    for required in ("Interface", "Strings"):
        if not (base_package / required).is_dir():
            raise ValueError(f"Base Korean package is missing {required}: {base_package}")

    plugins_catalog = {row["name"].casefold(): row for row in catalog["plugins"]}
    output = output.resolve()
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "schema_version": 1,
        "tool_version": tmrkr.VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "mo2_root": str(installation.root),
        "profile": installation.profile,
        "base_package": str(base_package.resolve()),
        "output": str(output),
        "plugins": [],
        "base_files": 0,
        "mcm": [],
        "interface": [],
        "warnings": list(installation.warnings),
    }

    with tempfile.TemporaryDirectory(prefix=".tmrkr-output-", dir=str(output.parent)) as tmp_name:
        temp = Path(tmp_name)
        stage = temp / "Output"
        base_mod = stage / "mods" / BASE_MOD
        plugin_mod = stage / "mods" / PLUGIN_MOD
        mcm_mod = stage / "mods" / MCM_MOD

        # Preserve the English-base runtime filenames exactly as supplied by the Korean package.
        for folder in ("Interface", "Programs", "Strings"):
            report["base_files"] += _copy_tree(base_package / folder, base_mod / folder)

        for plugin in installation.active:
            lower = plugin.casefold()
            if lower in OFFICIAL_MASTERS or (lower.startswith("cc") and lower.endswith(".esl")):
                continue
            try:
                source = installation.source(plugin)
            except Exception as exc:
                report["plugins"].append({"plugin": plugin, "status": "source_missing", "error": str(exc)})
                continue

            entry = plugins_catalog.get(lower)
            source_hash = tmrkr.sha256(source)
            result = {"plugin": plugin, "source_sha256": source_hash,
                      "provider": installation.providers[lower][-1]["provider"]}

            if entry and source_hash == entry.get("source_sha256"):
                status = entry.get("baseline_status")
                payload_rel = entry.get("payload")
                if status == "translated" and payload_rel:
                    payload = _contained(catalog_dir, payload_rel)
                    if tmrkr.sha256(payload) != entry["payload_sha256"]:
                        raise ValueError(f"Payload hash mismatch: {plugin}")
                    plugin_mod.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(payload, plugin_mod / plugin)
                    sidecars = 0
                    sidecar_dir = entry.get("sidecar_dir")
                    if sidecar_dir:
                        sidecars = _copy_en_sidecars(_contained(catalog_dir, sidecar_dir), plugin_mod / "Strings")
                    result.update(status="exact_payload", changed=entry.get("changed", 0), sidecars=sidecars)
                else:
                    result.update(status="known_no_translation_needed", changed=0)
                report["plugins"].append(result)
                continue

            # Changed or newly discovered plugin: merge direct dictionary + official base/DLC inheritance.
            detail, translated = _run_fallback(source, plugin, entry, catalog_dir, temp)
            if translated is None or detail.get("status") == "no_changes":
                result.update(status="updated_no_match" if entry else "new_no_match", changed=0,
                              detail=detail)
            else:
                plugin_mod.mkdir(parents=True, exist_ok=True)
                shutil.copy2(translated, plugin_mod / plugin)
                sidecars = _copy_en_sidecars(translated.parent, plugin_mod / "Strings")
                result.update(status="updated_fallback" if entry else "new_inherited",
                              changed=detail.get("changed", 0), sidecars=sidecars, detail=detail)
            report["plugins"].append(result)

        # Apply dictionaries to the current enabled MCM JSON so new settings are retained.
        for spec in catalog.get("mcm", []):
            relative = spec["path"]
            try:
                source = installation.source(relative)
            except Exception:
                continue
            mapping = _contained(catalog_dir, spec["mapping"])
            target = _contained(mcm_mod, relative)
            stats = translate_mcm_json(source, mapping, target)
            report["mcm"].append({"path": relative, **stats})

        # Interface/Translations also keep their _en names because Fallout 4 runs in English.
        for spec in catalog.get("interface", []):
            relative = spec["path"]
            try:
                source = installation.source(relative)
            except Exception:
                continue
            target = _contained(mcm_mod, relative)
            stats = _translate_interface(source, _contained(catalog_dir, spec["mapping"]), target)
            report["interface"].append({"path": relative, **stats})

        if not any((base_mod.exists(), plugin_mod.exists(), mcm_mod.exists())):
            raise RuntimeError("No output was generated")

        report_path = stage / "TMR-Korean-Patcher-report.json"
        _write_json(report_path, report)
        stage.rename(output)

    return report
