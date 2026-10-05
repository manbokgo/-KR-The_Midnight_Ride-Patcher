"""Apply development-exported SimpleMcmJsonTranslator dictionaries to MCM JSON."""
from __future__ import annotations

import json
from pathlib import Path


def load_mapping(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    mapping: dict[str, str] = {}
    for source, row in raw.items():
        if not isinstance(row, dict):
            continue
        translated = row.get("translated")
        status = str(row.get("status", "")).upper()
        if isinstance(translated, str) and translated and status in {"TRANSLATED", "VALIDATED"}:
            mapping[source.casefold()] = translated
    return mapping


def _translate(value, mapping: dict[str, str], stats: dict):
    if isinstance(value, str):
        translated = mapping.get(value.casefold())
        if translated is not None and translated != value:
            stats["matched"] += 1
            return translated
        return value
    if isinstance(value, list):
        return [_translate(item, mapping, stats) for item in value]
    if isinstance(value, dict):
        return {key: _translate(item, mapping, stats) for key, item in value.items()}
    return value


def translate_mcm_json(source: Path, mapping_path: Path, output: Path) -> dict:
    original = json.loads(source.read_text(encoding="utf-8-sig"))
    mapping = load_mapping(mapping_path)
    stats = {"matched": 0}
    translated = _translate(original, mapping, stats)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(translated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "source": str(source),
        "mapping": str(mapping_path),
        "output": str(output),
        "mapping_entries": len(mapping),
        "matched": stats["matched"],
    }
