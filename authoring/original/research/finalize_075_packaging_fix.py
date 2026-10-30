"""Validate corrected 0.7.5 and remove only its rejected duplicate-manifest ZIP."""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path(r"F:\aoe_4_temp\Berber_future_kingdom_ai_20261014\output\berber_update_0_7_5").resolve(strict=True)
fixed = root / "Berber-0.7.5-fixed.zip"
old = root / "Berber-0.7.5.zip"
report_path = root / "release-validation.json"
report = json.loads(report_path.read_text())


def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


assert report["zip"] == str(fixed)
assert sha(fixed) == report["zip_sha256"]
with zipfile.ZipFile(fixed) as z:
    assert z.testzip() is None
    assert [n for n in z.namelist() if Path(n).name.lower() == "garrison.json"] == ["garrison.json"]
    manifest = json.loads(z.read("garrison.json"))
    for member in manifest["members"]:
        with z.open(member["path"]) as f:
            assert hashlib.file_digest(f, "sha256").hexdigest() == member["sha256"]
assert old.resolve(strict=True).parent == root
assert not old.is_symlink()
assert sha(old) == "4e071ac619b9cad1be0cbd109f13fb58946675fca5dcbeb938f88c09401bbae0"
with zipfile.ZipFile(old) as z:
    rejected_manifests = [n for n in z.namelist() if Path(n).name.lower() == "garrison.json"]
    assert len(rejected_manifests) == 2
removed = old.stat().st_size
cleanup = {"target": str(old), "sha256": sha(old), "bytes": removed,
           "reason": "Rejected duplicate-manifest delivery; corrected ZIP verified before deletion",
           "rejected_manifest_paths": rejected_manifests,
           "disposable_bytes_before": removed, "disposable_bytes_after": 0,
           "reclaimed_E_bytes": 0, "reclaimed_F_bytes": removed}
# Save ownership/evidence before deleting the sole verified target.
(root / "packaging-fix-cleanup.json").write_text(json.dumps(cleanup, indent=2) + "\n")
old.unlink()
assert sha(fixed) == report["zip_sha256"]
with zipfile.ZipFile(fixed) as z:
    assert z.testzip() is None
report["cleanup"] = cleanup
report["post_cleanup_zip_hash_and_crc_verified"] = True
report_path.write_text(json.dumps(report, indent=2) + "\n")
project = Path(__file__).resolve().parents[1]
rebuild = project / "REBUILD_NEXT.md"
rebuild.write_text(rebuild.read_text().replace("berber_update_0_7_5/Berber-0.7.5.zip", "berber_update_0_7_5/Berber-0.7.5-fixed.zip"))
with (project / "STORAGE.md").open("a") as f:
    f.write("\n\n0.7.5 packaging correction: the first ZIP contained an archived second garrison.json and was rejected by the client. Corrected delivery is `output/berber_update_0_7_5/Berber-0.7.5-fixed.zip`, "
            + str(fixed.stat().st_size) + " bytes, SHA-256 `" + report["zip_sha256"]
            + "`. Exactly one garrison.json, every member hash, SGA hash and ZIP CRC passed. SGA/audio/runtime unchanged. Removed only the rejected original ZIP after verification, reclaiming "
            + str(removed) + " bytes on F: and 0 on E:. Detailed evidence: output/berber_update_0_7_5/packaging-fix-cleanup.json and release-validation.json. Prior 0.7.5 delivery path/hash above is superseded. Client import and audible testing remain pending.\n")
print(json.dumps({"zip": str(fixed), "sha256": sha(fixed), "manifest_count": 1,
                  "reclaimed_F_bytes": removed, "bytes": fixed.stat().st_size}, indent=2))
