"""Package the verified 0.3.0 candidate without modifying the 0.2.7.1 release."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "berber_update_0_3_0"
BASE = ROOT / "output" / "berber_update_0_2_7_1" / "package"
PACKAGE = OUT / "package"
SGA = OUT / "integration" / "candidate" / "Berber_future_kingdom.sga"
ZIP = OUT / "berber_future_kingdom-0.3.0.zip"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    checks = json.loads((OUT / "candidate-member-verification.json").read_text())
    sources = json.loads((ROOT / "art" / "building_remix_0_3_0" / "blender-source-validation.json").read_text())
    composition = json.loads((OUT / "integration" / "composition-report.json").read_text())
    assert checks["status"] == "passed" and checks["candidate_sha256"] == digest(SGA)
    assert checks["baseline_sha256"] == digest(BASE / "Berber_future_kingdom.sga")
    assert checks["baseline_members"] == 724 and checks["candidate_members"] == 890
    assert len(checks["changed_existing_members"]) == 4 and checks["byte_identical_existing_members"] == 720
    assert sources["status"] == "passed" and len(sources["models"]) == 12
    assert composition["status"] == "passed"

    PACKAGE.mkdir(exist_ok=True)
    target_sga = PACKAGE / "Berber_future_kingdom.sga"
    if target_sga.exists():
        assert digest(target_sga) == digest(SGA), "Existing package SGA differs; stop instead of overwriting"
    else:
        target_sga.write_bytes(SGA.read_bytes())

    manifest = json.loads((BASE / "garrison.json").read_text(encoding="utf-8"))
    manifest["members"][0]["sha256"] = digest(target_sga)
    manifest["details"].update({
        "version": "0.3.0",
        "summary": "Stock-derived Berber Age II-IV building art",
        "description": "Twelve age-tier art variants for Market, Blacksmith, Archery Range and Stable. Four Malian visual actors retargeted; gameplay and all other 0.2.7.1 members preserved.",
        "changelog": "Market gains a stock Byzantine mercenary-house annex; all four families gain three tiered Berber visual treatments. Working 0.2.7.1 Ribat precache is unchanged.",
    })
    (PACKAGE / "garrison.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    install = (
        "BERBER 0.3.0 - Age II-IV building art\n"
        "Close Age of Empires IV completely. Import this ZIP into Garrison, enable the updated Berber package, and start a fresh match.\n"
        "Select Tuning Pack The Berber Dynasties, Game Mode Berber Civilization, Civilization Malians.\n"
        "Check the Ribat has no missing-precache cube. Inspect Market, Blacksmith, Archery Range and Stable in Ages II, III and IV, with two player colours.\n"
        "Check construction/cancel, existing and new buildings after age-up, damage/destruction, scale/ground contact, unit exits, rally paths and previously accepted Age I assets.\n"
        "Runtime art and owner colour are pending this fresh-process test. The 0.2.7.1 rollback ZIP is retained separately.\n"
    )
    (PACKAGE / "INSTALL_AND_TEST.txt").write_text(install, encoding="utf-8")
    evidence = {
        "version": "0.3.0",
        "baseline_sha256": checks["baseline_sha256"],
        "sga_sha256": checks["candidate_sha256"],
        "project_guid": checks["guid"],
        "sga_members": checks["candidate_members"],
        "new_members": checks["new_members"],
        "unchanged_existing_members": checks["byte_identical_existing_members"],
        "changed_existing_members": checks["changed_existing_members"],
        "blender_sources": len(sources["models"]),
        "stock_derived_variants": 12,
        "baseline_tuning_warnings": 6,
        "runtime_test": "pending user",
    }
    (PACKAGE / "EVIDENCE.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    members = sorted(p for p in PACKAGE.iterdir() if p.is_file())
    assert {p.name for p in members} == {"Berber_future_kingdom.sga", "garrison.json", "EVIDENCE.json", "INSTALL_AND_TEST.txt"}
    with ZipFile(ZIP, "w", ZIP_DEFLATED, compresslevel=6) as archive:
        for member in members:
            archive.write(member, member.name)
    with ZipFile(ZIP) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == {p.name for p in members}
        assert hashlib.sha256(archive.read("Berber_future_kingdom.sga")).hexdigest() == digest(SGA)
        assert json.loads(archive.read("garrison.json"))["details"]["version"] == "0.3.0"
    result = {"status": "passed", "zip": str(ZIP), "zip_sha256": digest(ZIP), "sga": str(target_sga), "sga_sha256": digest(target_sga), "zip_members": [p.name for p in members]}
    (OUT / "release-validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
