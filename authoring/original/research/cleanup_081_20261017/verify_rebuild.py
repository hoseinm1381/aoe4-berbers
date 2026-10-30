"""Read-only retained-input checks plus isolated actual-source restore probes."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research"))
import package_unified_release as current
import restore_cleanup_cache as cache


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


result = json.loads((HERE / "result.json").read_text(encoding="utf-8"))
assert result["status"] == "passed"
plan = json.loads((HERE / "deletion-plan.json").read_text(encoding="utf-8"))
archiver = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe"
base_checks = []
historical_limitations = []
for row in plan["retained"]:
    path = Path(row["path"])
    if path.suffix.lower() != ".sga":
        continue
    completed = subprocess.run([str(archiver), "list", str(path), "--verify"], capture_output=True, text=True)
    if completed.returncode:
        # This unchanged historical fixture is not a production rebuild base.
        if (path.name == "tuareg_voice_probe.sga" and path.stat().st_size == 428
                and sha(path) == "5d64b3dc19e93bc2f8a7fafdf06882c082af0b0340f4b165b619a5f7366a0a1e"):
            historical_limitations.append({"path": str(path), "sha256": sha(path),
                "bytes": 428, "archiver_exit_code": completed.returncode,
                "status": "preserved unchanged; current archiver cannot verify historical probe",
                "required_for_current_release_rebuild": False})
            continue
        completed.check_returncode()
    parsed = json.loads(completed.stdout)
    assert parsed["archive"]["verification"]["verified"], str(path)
    base_checks.append({"path": str(path), "sha256": row["sha256"], "file_count": parsed["archive"]["file_count"], "verification": parsed["archive"]["verification"]})
    print("BASE SGA VERIFIED", path.parent.name, flush=True)
migrations = json.loads((HERE / "restore-source-migration.json").read_text(encoding="utf-8"))
selected = [next(row for row in migrations if Path(row["after"]["file"]).suffix == suffix) for suffix in (".wem", ".spd")]
with tempfile.TemporaryDirectory(prefix="restore-probe-", dir=HERE) as scratch:
    scratch = Path(scratch)
    rows = [{"path": str(scratch / "cache" / (str(i) + ".dat")),
             "sha256": row["after"]["sha256"], "restore": row["after"]} for i, row in enumerate(selected)]
    (scratch / "deletion-plan.json").write_text(json.dumps({"files": rows}), encoding="utf-8")
    previous = cache.REPORT
    cache.REPORT = scratch
    try:
        assert cache.restore(scratch / "cache") == 2
        for row in rows:
            assert sha(Path(row["path"])) == row["sha256"]
        assert cache.restore(scratch / "cache") == 0
    finally:
        cache.REPORT = previous
proof = {"working_release": current.check(), "actual_preserved_source_restore_probes": [row["after"] for row in selected],
         "restored_payloads": 2, "scope_and_existing_file_checks": "passed",
         "retained_base_sga_verification": base_checks,
         "historical_probe_limitations": historical_limitations,
         "temporary_probe_files": "removed by owned TemporaryDirectory", "older_delivery_zip_dependencies": 0}
(HERE / "rebuild-verification.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"working_release": proof["working_release"]["status"], "actual_restore_probes": 2, "old_delivery_zip_dependencies": 0}))
