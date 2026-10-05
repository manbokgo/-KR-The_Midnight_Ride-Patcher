"""Export xTranslator plugin SST records into a Mutagen-friendly JSON map."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tmrkr_sst import read_sst


def export_sst(path: Path, plugins_override: list[str] | None = None) -> dict:
    sst = read_sst(path)
    plugins = list(sst.plugins or plugins_override or [])
    if not plugins:
        raise ValueError(f"plugin SST has no plugin header and no override: {path}")
    target = plugins[-1]
    rows = []
    skipped_header = 0
    skipped_unchanged = 0
    skipped_old_data = 0
    for entry in sst.entries:
        if entry.rec.startswith("TES4") or entry.rec == "********":
            skipped_header += 1
            continue

        # SSU8/SSU9 stores colabId in the low byte and xTranslator's
        # sStrParams in the high byte. oldData is bit 6 (0x40) and is
        # deliberately deprioritized by xTranslator during SST matching.
        status_flags = (entry.flags >> 8) & 0xFF
        if status_flags & 0x40:
            skipped_old_data += 1
            continue

        if entry.source == entry.dest:
            skipped_unchanged += 1
            continue
        index = (entry.form_id >> 24) & 0xFF
        local_id = entry.form_id & 0x00FFFFFF
        if index >= len(plugins):
            raise ValueError(
                f"SST form owner index {index} exceeds plugin header ({len(plugins)}): "
                f"0x{entry.form_id:08X}"
            )
        rows.append({
            "owner": plugins[index],
            "id": f"{local_id:06X}",
            "record": entry.rec[:4],
            "field": entry.rec[4:],
            "rec_id": entry.rec_id,
            "rec_id_max": entry.rec_id_max,
            "string_id": entry.string_id,
            "source": entry.source,
            "dest": entry.dest,
        })
    return {
        "schema_version": 1,
        "sst_format": sst.format,
        "source_file": path.name,
        "plugins": plugins,
        "target": target,
        "mappings": rows,
        "stats": {
            "sst_entries": len(sst.entries),
            "mappings": len(rows),
            "skipped_tes4": skipped_header,
            "skipped_unchanged": skipped_unchanged,
            "skipped_old_data": skipped_old_data,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    data = export_sst(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(data["stats"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
