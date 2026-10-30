"""Preserve native trial evidence and inspect stock resources without deploying."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import sqlite3

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "output/tuareg_shield_posture_test"

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def preserve():
    WORK.mkdir(exist_ok=True)
    sources = [ROOT / "Berber_future_kingdom.aoe4mod"] + sorted(
        p for p in (ROOT / "assets").rglob("*") if p.is_file())
    baseline = {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}
    destination = WORK / "source-baseline.json"
    if destination.exists():
        assert json.loads(destination.read_text()) == baseline
    else:
        destination.write_text(json.dumps(baseline, indent=2))
    evidence = WORK / "native-cheer-pass"
    evidence.mkdir(exist_ok=True)
    inputs = {
        "warnings.log": Path.home() / "Documents/My Games/Age of Empires IV/warnings.log",
        "native-cheer-pass.mp4": Path.home() / "Videos/2026-10-11 11-24-02.mp4",
        "delivery.json": ROOT / "output/tuareg_q_command_test/delivery.json",
        "client.log": Path(os.environ["LOCALAPPDATA"]) / "Garrison/client.log",
    }
    records = []
    for name, source in inputs.items():
        target = evidence / name
        if not target.exists():
            shutil.copy2(source, target)
        records.append({"source": str(source), "retained": str(target),
                        "sha256": sha(target), "bytes": target.stat().st_size})
    warnings = (evidence / "warnings.log").read_text(errors="replace")
    markers = [line for line in warnings.splitlines() if "TUAREG_Q_ANIM_TRIAL2" in line]
    (evidence / "animation-markers.txt").write_text("\n".join(markers))
    (evidence / "provenance.json").write_text(json.dumps({
        "files": records, "observation": "User reports victory dance, temporary stop and movement restoration at 15s",
        "video_review": "Retained original; not independently visually reviewed",
        "starts": sum(" START " in x for x in markers),
        "duration_stops": sum(" STOP " in x and "reason=duration" in x for x in markers),
        "acceptance": "Q trigger, cheer playback and cleanup only; damage reduction not measured",
    }, indent=2))
    candidate = WORK / "candidate"
    if not candidate.exists():
        candidate.mkdir()
        shutil.copy2(ROOT / "Berber_future_kingdom.aoe4mod", candidate)
        shutil.copytree(ROOT / "assets", candidate / "assets")
    (WORK / "progress.md").write_text(
        "# Tuareg shield posture execution ledger\n\n"
        "Plan: user-approved stock posture, movement and combat preserved.\n"
        "Task 1 complete: retained successful native cheer log/recording and captured original source hashes.\n"
        "Ruling: isolate under output/tuareg_shield_posture_test/candidate; do not change the existing dirty checkout.\n"
        "Task 2 active: qualify independent native visual control before writing a controller.\n"
        "Export flags, Byzantine ability/modifiers and unverified statemodel writes are forbidden.\n")
    print(json.dumps({"source_files": len(baseline), "markers": len(markers), "candidate": str(candidate)}))

def index():
    db = Path(os.environ["LOCALAPPDATA"]) / "Garrison/Kit/game-assets.sqlite3"
    with sqlite3.connect("file:" + db.as_posix() + "?mode=ro", uri=True) as connection:
        tables = connection.execute("select name,sql from sqlite_master where type='table'").fetchall()
        print(json.dumps(tables, indent=2))

if __name__ == "__main__":
    import sys
    {"preserve": preserve, "index": index}[sys.argv[1]]()
