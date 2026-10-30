"""Bind the forced-transition trial readback to its verified archive."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import zlib
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "art/tuareg_shield"))
import q_force_trial as trial
WORK = trial.WORK
delivery = json.loads((WORK / "delivery.json").read_text())
archive = Path(delivery["archive"])
assert trial.sha(archive) == delivery["archive_sha256"]
current = trial.inspect(archive)
members = {x["path"].lower(): x for x in current["members"]}
for name in delivery["changed_members"] + delivery["added_members"]:
    item = members[name.lower()]
    raw = (WORK / "readback" / item["path"]).read_bytes()
    assert len(raw) == item["size"] and zlib.crc32(raw) == item["crc"]
    assert hashlib.sha256(raw).hexdigest() == trial.sha(WORK / "candidate/assets" / name)
previous = json.loads((ROOT / "output/tuareg_shield_posture_test/delivery.json").read_text())
old = {x["path"].lower(): x for x in trial.inspect(Path(previous["archive"]))["members"]}
unchanged = [name for name, item in old.items() if name != trial.GM.lower()]
assert len(unchanged) == 264
assert all((members[name]["crc"], members[name]["size"], members[name]["toc"]) ==
           (old[name]["crc"], old[name]["size"], old[name]["toc"]) for name in unchanged)
module = (WORK / "readback" / members[trial.MODULE.lower()]["path"]).read_text()
assert module == (ROOT / "art/tuareg_shield/tuareg_q_force_trial.scar").read_text()
for token in ("Cmd_Move", "Cmd_Stop", "Cmd_Ability", "SGroup_AddAbility", "cheer_toggle"):
    assert token not in module
gm = (WORK / "readback" / members[trial.GM.lower()]["path"]).read_text()
assert 'import("Units/tuareg_q_force_trial.scar")' in gm
assert 'import("Units/tuareg_q_posture_trial.scar")' not in gm
with zipfile.ZipFile(delivery["zip"]) as packed:
    assert packed.testzip() is None
    assert hashlib.sha256(packed.read(archive.name)).hexdigest() == delivery["archive_sha256"]
assert trial.sha(Path(delivery["zip"])) == delivery["zip_sha256"]
report = {"original_sources_preserved": trial.guard(), "unchanged_previous_archive_members": len(unchanged),
          "all_tuning_models_voices": "byte-preserved", "new_import_and_module": "readback matches reviewed source",
          "zip_sha256": delivery["zip_sha256"], "native_acceptance": "pending user"}
(WORK / "validation-summary.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
