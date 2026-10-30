"""Package verified Berber 0.3.1 while retaining 0.3.0 rollback."""

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/berber_update_0_3_1"
BASE = ROOT / "output/berber_update_0_3_0/package"
PACKAGE = OUT / "package"
SGA = OUT / "integration/candidate/Berber_future_kingdom.sga"
ZIP = OUT / "berber_future_kingdom-0.3.1.zip"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    checks = json.loads((OUT / "candidate-member-verification.json").read_text(encoding="utf-8"))
    composition = json.loads((OUT / "integration/composition-report.json").read_text(encoding="utf-8"))
    assert checks["status"] == "passed" and checks["candidate_sha256"] == digest(SGA)
    assert checks["baseline_sha256"] == digest(BASE / "Berber_future_kingdom.sga")
    assert checks["baseline_members"] == 890
    assert len(checks["changed_existing_members"]) == 6
    assert composition["status"] == "passed" and len(composition["native_stamps"]) == 13
    assert (ROOT / "output/berber_update_0_3_0/berber_future_kingdom-0.3.0.zip").is_file()
    PACKAGE.mkdir(exist_ok=True)
    target_sga = PACKAGE / "Berber_future_kingdom.sga"
    if target_sga.exists():
        assert digest(target_sga) == digest(SGA), "Existing package SGA differs"
    else:
        target_sga.write_bytes(SGA.read_bytes())
    manifest = json.loads((BASE / "garrison.json").read_text(encoding="utf-8"))
    manifest["members"][0]["sha256"] = digest(target_sga)
    manifest["details"].update({
        "version": "0.3.1",
        "summary": "Berber six-building stock-derived art overhaul",
        "description": "Thirteen scoped art variants for Tribal Market, Tlemcen and Marrakech landmarks, Mosque, Siege Workshop and standard Keep. Gameplay and unrelated 0.3.0 members preserved.",
        "changelog": "Market's active Byzantine annex references removed; six Berber building families have donor-remodelled Age II-IV art. 0.3.0 remains the rollback.",
    })
    (PACKAGE / "garrison.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    install = (
        "BERBER 0.3.1 - six-building art test\n"
        "Close Age of Empires IV completely. Import this ZIP into Garrison, enable the updated Berber package, and start a fresh match.\n"
        "Select Tuning Pack The Berber Dynasties, Game Mode Berber Civilization, Civilization Malians.\n"
        "Inspect Tribal Market in Ages II-IV and Great Mosque of Tlemcen, Dar al-Jihad of Marrakech, standard Mosque, Siege Workshop and standard Keep in Ages III-IV.\n"
        "Use two player colours. Check construction/cancel, existing and newly built structures after age-up, damage/destruction, scale/contact, Mosque and landmark functions, siege-engine and unit exits, Keep firing/garrison points, rally paths, and accepted 0.3.0 assets.\n"
        "Package/cook checks do not establish native runtime acceptance. The 0.3.0 rollback ZIP is retained separately.\n"
    )
    (PACKAGE / "INSTALL_AND_TEST.txt").write_text(install, encoding="utf-8")
    evidence = {"version": "0.3.1", "baseline_sha256": checks["baseline_sha256"],
                "sga_sha256": checks["candidate_sha256"], "project_guid": checks["guid"],
                "sga_members": checks["candidate_members"], "new_members": checks["new_members"],
                "unchanged_existing_members": checks["byte_identical_existing_members"],
                "changed_existing_members": checks["changed_existing_members"],
                "stock_derived_variants": 13, "baseline_tuning_warnings": 6,
                "runtime_test": "pending user"}
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
        assert json.loads(archive.read("garrison.json"))["details"]["version"] == "0.3.1"
    result = {"status": "passed", "zip": str(ZIP), "zip_sha256": digest(ZIP),
              "sga": str(target_sga), "sga_sha256": digest(target_sga),
              "zip_members": [p.name for p in members]}
    (OUT / "release-validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
