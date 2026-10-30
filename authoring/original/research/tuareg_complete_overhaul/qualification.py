"""Preserve the working trial and qualify installed contracts without bypasses."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "output/tuareg_complete_overhaul"
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def preserve():
    WORK.mkdir(exist_ok=True)
    baseline = WORK / "baseline"; baseline.mkdir(exist_ok=True)
    delivery = json.loads((ROOT / "output/tuareg_shield_posture_test/delivery.json").read_text())
    assert sha(Path(delivery["zip"])) == delivery["zip_sha256"]
    assert sha(Path(delivery["archive"])) == delivery["archive_sha256"]
    inputs = [Path(delivery["zip"]), Path(delivery["archive"]),
              ROOT / "output/tuareg_shield_posture_test/delivery.json",
              Path.home() / "Documents/My Games/Age of Empires IV/warnings.log",
              ROOT / "art/tuareg_shield/Tuareg_Shield_Ages_I_IV.blend",
              ROOT / "art/tuareg_shield/Tuareg_Shield_Q_RaiseHold_SOURCE_ONLY.blend",
              ROOT / "art/spearman_test/spearman_test.blend"]
    retained = []
    for path in inputs:
        target = baseline / path.name
        if not target.exists(): shutil.copy2(path, target)
        retained.append({"source": str(path), "retained": str(target), "sha256": sha(target), "bytes": target.stat().st_size})
    sources = [ROOT / "Berber_future_kingdom.aoe4mod"] + sorted(p for p in (ROOT / "assets").rglob("*") if p.is_file())
    guard = {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}
    if (WORK / "source-baseline.json").exists():
        assert json.loads((WORK / "source-baseline.json").read_text()) == guard
    else: (WORK / "source-baseline.json").write_text(json.dumps(guard, indent=2))
    warning = (baseline / "warnings.log").read_text(errors="replace")
    lines = [x for x in warning.splitlines() if "TUAREG_Q_POSTURE_TRIAL1" in x]
    (baseline / "posture-markers.txt").write_text("\n".join(lines))
    report = {"original_sources": len(guard), "retained": retained,
              "native_observation": "User reports immediate idle posture, 3-4s delay while moving; full native gameplay acceptance not established",
              "pose_starts": sum(" START " in x for x in lines),
              "pose_stops": sum(" STOP " in x for x in lines)}
    (WORK / "baseline-provenance.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"original_sources": len(guard), "retained_files": len(retained), "pose_starts": report["pose_starts"]}))

def contracts():
    sys.path.insert(0, str(EXT.parent))
    from garrison.addon_common import core_module
    core = core_module("unit_prototypes")
    catalog = list(core.catalog())
    timings = {row["key"]: core.qualified_timings(row["key"]) for row in catalog}
    probes = []
    # Native clip names are taken from the current compiled tree, not invented.
    graph = json.loads((ROOT / "output/tuareg_shield_posture_test/shield-key-and-clip-consumers.json").read_text())
    native_clips = sorted({value["text"] for row in graph for name, value in row["fields"].items()
                           if row["type"] == "StateTree::Provider_ConstAnimationName" and value.get("text")
                           and any(x["fields"].get("m_name", {}).get("text") == "anims_spearshield" for x in row["ancestors"])})
    candidates = ["navigation\\idle_calm_basic_01"] + native_clips
    for key in ("english-spearman-2", "base_spearshield"):
        try:
            selected = core.get(key)
            prototype_status = {"status": "catalogued", "definition": selected}
        except (ValueError, KeyError) as error:
            prototype_status = {"status": "not_catalogued", "reason": str(error)}
        for clip in candidates:
            record = {"prototype": key, "prototype_lookup": prototype_status, "clip": clip,
                      "meaning": "Timing helper result only; not a unit-build admission"}
            try: record.update(status="admitted", timing=core.clip_timing(key, {"name": clip}))
            except (ValueError, KeyError) as error: record.update(status="refused", reason=str(error))
            probes.append(record)
    import importlib
    import inspect
    interfaces = []
    for name in ("unit_animation_fullbody", "unit_animation_export", "unit_clip_overrides",
                 "state_tree_authoring", "state_tree_composer", "state_tree_linker",
                 "havok_tagfile", "rhka_animation_decoder", "unit_model_export", "unit_project"):
        entry = {"module": name}
        try:
            module = core_module(name)
            entry.update(status="exposed", functions={n: str(inspect.signature(v)) for n, v in vars(module).items()
                         if not n.startswith("_") and inspect.isfunction(v)})
        except ImportError as error: entry.update(status="not_exposed", reason=str(error))
        interfaces.append(entry)
    report = {"version": tomllib.loads((EXT / "blender_manifest.toml").read_text())["version"],
              "catalog": catalog, "timings": timings, "native_clip_probes": probes,
              "public_interfaces": interfaces,
              "boundary": "Public installed routes only; no compiled module decompilation, admission edits or shared-stock mutation"}
    (WORK / "installed-contracts.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"version": report["version"], "prototype_count": len(catalog),
                      "probes": probes, "interfaces": [(x["module"], x["status"]) for x in interfaces]}, indent=2))

if __name__ == "__main__":
    {"preserve": preserve, "contracts": contracts}[sys.argv[1]]()
