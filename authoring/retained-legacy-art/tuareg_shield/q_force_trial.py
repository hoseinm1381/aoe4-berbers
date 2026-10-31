"""Isolate and package the user-authorized forced native guard experiment."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
import shrek_trigger_probe as editor_builder

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "output/tuareg_force_trial"
CANDIDATE = WORK / "candidate"
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
ARCHIVER = EXT / "bin/sga-archiver.exe"
GUID = "1d3145e8f1b2427f8bb0067851fcf0f1"
VERSION = "0.1.3-tuareg-q-force.1"
GM = "scar/winconditions/berber_future_kingdom_GM.scar"
MODULE = "scar/Units/tuareg_q_force_trial.scar"

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def guard():
    source = json.loads((WORK / "source-baseline.json").read_text())
    for file, value in source.items(): assert sha(ROOT / file) == value, file
    return len(source)
def run(args):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout
def inspect(path): return json.loads(run([ARCHIVER, "list", path, "--verify"]))

def prepare():
    WORK.mkdir(exist_ok=True)
    assert not CANDIDATE.exists()
    baseline = [ROOT / "Berber_future_kingdom.aoe4mod"] + [p for p in (ROOT / "assets").rglob("*") if p.is_file()]
    (WORK / "source-baseline.json").write_text(json.dumps({p.relative_to(ROOT).as_posix(): sha(p) for p in baseline}, indent=2))
    previous = ROOT / "output/tuareg_shield_posture_test/candidate"
    shutil.copytree(previous, CANDIDATE)
    gm = CANDIDATE / "assets" / GM
    data = gm.read_bytes()
    old = b'import("Units/tuareg_q_posture_trial.scar")'
    new = b'import("Units/tuareg_q_force_trial.scar")'
    assert data.count(old) == 1 and new not in data
    gm.write_bytes(data.replace(old, new))
    shutil.copy2(ROOT / "art/tuareg_shield/tuareg_q_force_trial.scar", CANDIDATE / "assets" / MODULE)
    for p in (previous / "assets").rglob("*"):
        if p.is_file() and p.relative_to(previous).as_posix() != "assets/" + GM:
            assert sha(p) == sha(CANDIDATE / p.relative_to(previous)), p
    (WORK / "candidate-source.json").write_text(json.dumps({
        "guid": GUID, "previous_candidate": str(previous), "changed_sources": ["assets/" + GM],
        "added_sources": ["assets/" + MODULE], "original_source_files_preserved": guard(),
        "native_calls": "StateTree_QueueGlobalStateTreeEntity(false, verified native leaf, private entity)",
        "scope": "forced guard-entry/restore experiment; no new custom clip library or redesigned model in this milestone",
        "permission": "user explicitly requested experimental force implementation and will check native behavior"}, indent=2))
    print("prepared", CANDIDATE, "original_sources", guard())

def build():
    editor_builder.WORK = WORK; editor_builder.CANDIDATE = CANDIDATE
    editor_builder.build()

def package():
    guard()
    previous = json.loads((ROOT / "output/tuareg_shield_posture_test/delivery.json").read_text())
    base = Path(previous["archive"]); assert sha(base) == previous["archive_sha256"]
    result = json.loads((WORK / "candidate-build.json").read_text())
    assert result["status"] == "succeeded" and result["exit_code"] == 0
    donor = Path(result["archives"][0]["path"]); assert sha(donor) == result["archives"][0]["sha256"]
    old_inventory = inspect(base); donor_inventory = inspect(donor)
    paths = [next(x["path"] for x in donor_inventory["members"] if x["path"].lower() == p.lower()) for p in (GM, MODULE)]
    folder = WORK / "package"; folder.mkdir(exist_ok=True)
    archive = folder / "Berber_future_kingdom.sga"; assert not archive.exists()
    (WORK / "graft-result.json").write_text(run([ARCHIVER, "graft", base, donor, archive, *paths]))
    inventory = inspect(archive)
    old = {x["path"].lower(): x for x in old_inventory["members"]}
    new = {x["path"].lower(): x for x in inventory["members"]}
    changed = [p for p in old if (old[p]["crc"], old[p]["size"]) != (new[p]["crc"], new[p]["size"])]
    assert changed == [GM.lower()]
    assert set(new) - set(old) == {MODULE.lower()} and set(old) <= set(new)
    assert len(new) == 266 and inventory["archive"]["verification"]["verified"] is True
    assert inventory["archive"]["name"].replace("-", "").lower() == GUID
    readback = WORK / "readback"; assert not readback.exists()
    run([ARCHIVER, "unpack", archive, "--output", readback])
    for logical in (GM, MODULE):
        assert sha(readback / new[logical.lower()]["path"]) == sha(CANDIDATE / "assets" / logical)
    report = {"version": VERSION, "guid": GUID, "archive": str(archive), "archive_sha256": sha(archive),
              "archive_members": len(new), "changed_members": changed, "added_members": [MODULE],
              "unchanged_previous_members": len(old) - len(changed), "original_sources_preserved": guard(),
              "original_tuning_models_voices": "byte-preserved from working posture.1",
              "native_acceptance": "pending user test; submission is not proof of playback or phase/order preservation",
              "native_root_lifetime": "leaf ExitAtEnd inspected; queued-root priority, cancellation and runtime lifetime remain unqualified",
              "full_overhaul": "pending; this is the experimental forced-transition milestone"}
    (WORK / "archive-inventory.json").write_text(json.dumps(inventory, indent=2))
    (folder / "PROBE-EVIDENCE.json").write_text(json.dumps(report, indent=2))
    shutil.copy2(WORK / "TEST-PROBE.txt", folder / "TEST-PROBE.txt")
    sys.path.insert(0, str(EXT)); from garrison_shared import mod_bundle
    details = {"id": "berber_future_kingdom", "name": "The Berber Dynasties", "version": VERSION,
               "summary": "Experimental forced Tuareg shield entry while walking",
               "author": "hossein81 and marcokistan", "updated": "2026-10-11", "min_garrison": "0.1.3",
               "content_types": ["game-mode", "tuning-pack"],
               "description": "User-authorized forced-animation trial. Existing Tuareg Q selector plus documented native Entity-tree queue, using exact stock guard/normal leaf paths for walking. No Move/Stop orders or cheer grants. Attacks, charge and brace are excluded from forced restart. Native phase/lifetime and full custom art/motion remain pending.",
               "changelog": "Experimental direct native leaf queue to investigate delayed moving shield posture."}
    mod_bundle.write_manifest(folder, bundle_key="berber_future_kingdom", members=[{
        "mod_key": "berber_future_kingdom", "role": "tuning", "path": archive.name, "sha256": sha(archive)}], details=details)
    zip_path = WORK / f"berber_future_kingdom-{VERSION}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as packed:
        for p in sorted(folder.iterdir()): packed.write(p, p.name)
    with zipfile.ZipFile(zip_path) as packed:
        assert packed.testzip() is None
        assert hashlib.sha256(packed.read(archive.name)).hexdigest() == report["archive_sha256"]
    report.update(zip=str(zip_path), zip_sha256=sha(zip_path))
    (WORK / "delivery.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("stage", choices=["prepare", "build", "package"])
    globals()[parser.parse_args().stage]()
