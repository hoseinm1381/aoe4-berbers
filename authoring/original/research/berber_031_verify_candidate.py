"""Verify scoped 031 member payloads and byte preservation against 030."""

import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/berber_update_0_3_1"
INT = OUT / "integration"
BASE = ROOT / "output/berber_update_0_3_0/package/Berber_future_kingdom.sga"
CANDIDATE = INT / "candidate/Berber_future_kingdom.sga"
ARCH = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inventory(path):
    p = subprocess.run([str(ARCH), "list", str(path), "--verify"], capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 0, p.stderr
    doc = json.loads(p.stdout)
    assert doc["archive"]["verification"]["verified"]
    return doc


def main():
    assert sha(BASE) == "33cbb2d3d60914da49e893fe0f19c37dc6cb9aaaa120c0d00613a26a2ebbe5af"
    old, new = inventory(BASE), inventory(CANDIDATE)
    before = {x["path"]: x for x in old["members"]}
    after = {x["path"]: x for x in new["members"]}
    assert len(before) == 890
    composition = json.loads((INT / "composition-report.json").read_text(encoding="utf-8"))
    allowed = {x["member"] for x in composition["payloads"]}
    assert set(after) == set(before) | allowed
    baseline = INT / "baseline-readback"
    candidate = INT / "candidate-readback"
    assert baseline.is_dir() and candidate.is_dir()
    changes, unchanged_bytes = [], 0
    for member in before:
        lhs, rhs = baseline / member, candidate / member
        assert lhs.is_file() and rhs.is_file(), member
        if member not in allowed:
            assert before[member]["toc"] == after[member]["toc"], member
        if sha(lhs) == sha(rhs):
            unchanged_bytes += lhs.stat().st_size
        else:
            assert member in allowed, member
            changes.append(member)
    expected = {x["member"] for x in composition["actors"]}
    assert set(changes) == expected, (changes, expected)
    for row in composition["payloads"]:
        assert sha(candidate / row["member"]) == row["sha256"]
    assert len(composition["native_stamps"]) == len(composition["private_tiers"]) == 13
    for family, ages in {"market": (2, 3, 4), "mosque": (3, 4), "siege": (3, 4),
                         "keep": (3, 4), "tlemcen": (3, 4), "marrakech": (3, 4)}.items():
        for age in ages:
            assert f"art/stamps/garrison/berber_buildings_031/{family}_age{age:02}.bin" in after
            assert f"attrib/attachments/attachment_lists/garrison/berber_buildings_031/v031_{family}_age{age:02}_tier.rgd" in after
    assert not any("b030\\aa" in (candidate / f"art/stamps/garrison/berber_buildings_031/market_age{age:02}.bin").read_bytes().decode("latin1") for age in (2,3,4))
    report = {"status": "passed", "baseline_sha256": sha(BASE), "candidate_sha256": sha(CANDIDATE),
              "guid": new["archive"]["name"], "baseline_members": len(before), "candidate_members": len(after),
              "new_members": len(set(after) - set(before)), "changed_existing_members": sorted(changes),
              "byte_identical_existing_members": len(before) - len(changes),
              "unchanged_existing_bytes": unchanged_bytes, "expected_private_stamps": 13,
              "expected_private_tiers": 13, "archive_crc_sha1_verified": True, "native_test": "pending user"}
    (OUT / "candidate-member-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("BERBER_031_CANDIDATE_BYTES_VERIFIED", report["byte_identical_existing_members"], "unchanged", len(changes), "changed")


if __name__ == "__main__":
    main()
