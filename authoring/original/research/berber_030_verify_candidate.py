"""Full member-byte preservation and scoped 0.3.0 candidate checks."""

import hashlib
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/berber_update_0_3_0"
INT = OUT / "integration"
BASE = ROOT / "output/berber_update_0_2_7_1/package/Berber_future_kingdom.sga"
CANDIDATE = INT / "candidate/Berber_future_kingdom.sga"
ARCH = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(path):
    result = subprocess.run([str(ARCH), "list", str(path), "--verify"], capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
    document = json.loads(result.stdout)
    assert document["archive"]["verification"]["verified"]
    return document


def main():
    assert sha(BASE) == "6f2d9844e2a932bd4ae9e440d2e07720dfd6e0fe1c60e9b53b23cc0549cb8faf"
    old = inventory(BASE)
    new = inventory(CANDIDATE)
    before = {r["path"]: r for r in old["members"]}
    after = {r["path"]: r for r in new["members"]}
    assert len(before) == 724 and len(after) == 890
    payload = json.loads((INT / "composition-report.json").read_text(encoding="utf-8"))
    allowed = {x["member"] for x in payload["payloads"]}
    assert len(allowed) == 170 and set(after) == set(before) | allowed
    baseline = INT / "baseline-readback"
    candidate = INT / "candidate-readback"
    changes = []
    unchanged_bytes = 0
    for member in before:
        source = baseline / member
        result = candidate / member
        assert source.is_file() and result.is_file(), member
        assert before[member]["toc"] == after[member]["toc"]
        if sha(source) == sha(result):
            unchanged_bytes += source.stat().st_size
        else:
            assert member in allowed, member
            changes.append(member)
    expected_changed = {r["member"] for r in payload["actors"]}
    assert set(changes) == expected_changed, (changes, expected_changed)
    for row in payload["payloads"]:
        assert sha(candidate / row["member"]) == row["sha256"]
    names = set(after)
    expected_stamps = {f"art/stamps/garrison/berber_buildings_030/{family}_age{age:02}.bin" for family in ("market", "blacksmith", "archery_range", "stable") for age in (2, 3, 4)}
    assert expected_stamps <= names
    expected_tiers = {f"attrib/attachments/attachment_lists/garrison/berber_buildings_030/{family}_age{age:02}_tier.rgd" for family in ("market", "blacksmith", "archery_range", "stable") for age in (2, 3, 4)}
    assert expected_tiers <= names
    annex = [x for x in names if x.startswith("art/scenario/b030/aa/")]
    assert len([x for x in annex if x.endswith(".rgm")]) == 3
    assert len([x for x in annex if x.endswith(".rgo")]) == 3
    assert len([x for x in annex if x.endswith(".rrgeom")]) == 3
    assert len([x for x in annex if x.endswith(".rrmaterial")]) == 3
    assert not any("building_landmark_age1_landmarka_mal" in x for x in changes)
    report = {"status": "passed", "baseline_sha256": sha(BASE), "candidate_sha256": sha(CANDIDATE), "guid": new["archive"]["name"], "baseline_members": len(before), "candidate_members": len(after), "new_members": len(set(after) - set(before)), "changed_existing_members": sorted(changes), "byte_identical_existing_members": len(before) - len(changes), "unchanged_existing_bytes": unchanged_bytes, "expected_private_stamps": len(expected_stamps), "expected_private_tiers": len(expected_tiers), "annex_model_parts": 3, "archive_crc_sha1_verified": True, "native_test": "pending user"}
    (OUT / "candidate-member-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("BERBER_030_CANDIDATE_BYTES_VERIFIED", report["byte_identical_existing_members"], "unchanged", len(changes), "changed")


if __name__ == "__main__":
    main()
