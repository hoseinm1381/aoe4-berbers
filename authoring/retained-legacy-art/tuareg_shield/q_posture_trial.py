"""Stage, cook and package the source-proven native shield selector trial."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
import shrek_trigger_probe as editor_builder

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "output/tuareg_shield_posture_test"
CANDIDATE = WORK / "candidate"
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
ARCHIVER = EXT / "bin/sga-archiver.exe"
GUID = "1d3145e8f1b2427f8bb0067851fcf0f1"
VERSION = "0.1.3-tuareg-q-posture.1"
GM = "scar/winconditions/berber_future_kingdom_GM.scar"
MODULE = "scar/Units/tuareg_q_posture_trial.scar"
SCHEMA = "statemodel_schema/garrison/tuareg_posture_schema/tuareg_shield_posture_ber"
ENTITY_FILES = [f"ebps/races/malian/units/unit_spearman_tuareg_{age}_ber" for age in range(1, 5)]
SQUAD_FILES = [f"sbps/races/malian/berbers/unit_spearman_tuareg_{age}_ber" for age in range(1, 5)]

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def inspect(path): return json.loads(subprocess.check_output([str(ARCHIVER), "list", str(path), "--verify"], text=True))
def guard():
    baseline = json.loads((WORK / "source-baseline.json").read_text())
    for name, digest in baseline.items(): assert sha(ROOT / name) == digest, name
    return len(baseline)
def run(args):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout

def prepare():
    guard()
    recipe = json.loads((WORK / "schema-library/Mods/tuareg_posture_schema/mod-project.json").read_text())
    cook = recipe["cooks"][-1]
    donor = Path(cook["archive"])
    assert sha(donor) == cook["sha256"]
    resource = WORK / "serializer-schema.rgd"
    run([ARCHIVER, "extract-member", donor, f"attrib/{SCHEMA}.rgd", resource])
    run([ARCHIVER, "decode-rgd", resource, WORK / "serializer-schema.xml"])
    compiled = ET.parse(WORK / "serializer-schema.xml").getroot()
    identifier = compiled.find("./RGDNode/RGDNode[@Key='pbgid']").get("Value")
    for path in (CANDIDATE / "assets/attrib/instances").rglob("*.xml"):
        assert all(x.get("value") != identifier for x in ET.parse(path).iter("uniqueid")), path

    official = ET.parse(WORK / "spearman_byz_schema.xml").getroot()
    schema = ET.Element("instance", version=official.get("version"), template=official.get("template"),
                        description="Private Tuareg native posture flag and unchanged Donso schema")
    ET.SubElement(schema, "uniqueid", name="pbgid", value=identifier)
    group = ET.SubElement(schema, "group", name="schema_bag")
    schemas = ET.SubElement(group, "list", name="sub_schemas")
    reference = copy.deepcopy(official.find("./group/list[@name='sub_schemas']/instance_reference"))
    reference.set("List.ParentItemID", reference.get("List.ItemID"))
    reference.set("overrideParent", "True")
    reference.set("value", "statemodel_schema\\units\\civilizations\\malian\\donso_mal")
    schemas.append(reference)
    ET.SubElement(schema, "instance_reference", name="parent_pbg", value="statemodel_schema\\units\\civilizations\\byzantine\\spearman_byz")
    target = CANDIDATE / f"assets/attrib/instances/{SCHEMA}.xml"
    assert not target.exists(); target.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(schema, space="\t")
    ET.ElementTree(schema).write(target, encoding="utf-8", xml_declaration=True)
    changes = []
    for logical in ENTITY_FILES:
        path = CANDIDATE / f"assets/attrib/instances/{logical}.xml"
        before = path.read_bytes()
        old = b'<instance_reference name="schema" value="statemodel_schema\\units\\civilizations\\malian\\donso_mal" overrideParent="True" />'
        new = ('<instance_reference name="schema" value="' + SCHEMA.replace("/", "\\") + '" mod="' + GUID + '" overrideParent="True" />').encode()
        assert before.count(old) == 1, logical
        path.write_bytes(before.replace(old, new))
        assert path.read_bytes().replace(new, old) == before
        changes.append(str(path.relative_to(CANDIDATE)).replace("\\", "/"))
    module = CANDIDATE / "assets" / MODULE
    assert not module.exists(); shutil.copy2(ROOT / "art/tuareg_shield/tuareg_q_posture_trial.scar", module)
    gm = CANDIDATE / "assets" / GM
    original = gm.read_bytes(); marker = b'import("Units/tuareg_voice_profile.scar")'
    assert original.count(marker) == 1 and b"tuareg_q_cheer_trial" not in original
    gm.write_bytes(original.replace(marker, marker + b'\r\nimport("Units/tuareg_q_posture_trial.scar")'))
    changes.append("assets/" + GM)
    report = {"guid": GUID, "schema_identity": int(identifier), "identity_source": cook,
              "changed_sources": changes, "added_sources": ["assets/" + MODULE, str(target.relative_to(CANDIDATE)).replace("\\", "/")],
              "original_source_files_preserved": guard(), "native_control": "spearman_shield_wall_byz",
              "gameplay_branch": "Mode_Chooser absent from Tuareg action trees and never installed"}
    (WORK / "candidate-source.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

def build():
    editor_builder.WORK = WORK; editor_builder.CANDIDATE = CANDIDATE
    editor_builder.build()

def package():
    guard()
    build = json.loads((WORK / "candidate-build.json").read_text())
    assert build["status"] == "succeeded" and build["exit_code"] == 0
    donor = Path(build["archives"][0]["path"]); assert sha(donor) == build["archives"][0]["sha256"]
    working = json.loads((ROOT / "output/tuareg_shield_test/delivery-verification.json").read_text())
    base = Path(working["archive"]); assert sha(base) == working["archive_sha256"]
    before = inspect(base); donor_inventory = inspect(donor)
    old = {x["path"].lower(): x for x in before["members"]}
    available = {x["path"].lower(): x for x in donor_inventory["members"]}
    logical = [GM, MODULE, f"attrib/{SCHEMA}.rgd"] + [f"attrib/{p}.rgd" for p in ENTITY_FILES + SQUAD_FILES]
    members = [available[p.lower()]["path"] for p in logical]
    package_dir = WORK / "package"; package_dir.mkdir(exist_ok=True)
    archive = package_dir / "Berber_future_kingdom.sga"; assert not archive.exists()
    (WORK / "graft-result.json").write_text(run([ARCHIVER, "graft", base, donor, archive, *members]))
    after = inspect(archive); new = {x["path"].lower(): x for x in after["members"]}
    expected_added = {MODULE.lower(), f"attrib/{SCHEMA}.rgd".lower()}
    assert set(new) - set(old) == expected_added
    assert after["archive"]["verification"]["verified"] is True
    assert after["archive"]["name"].replace("-", "").lower() == GUID
    changes = [p for p in old if (old[p]["crc"], old[p]["size"]) != (new[p]["crc"], new[p]["size"])]
    assert set(changes) <= {p.lower() for p in logical} - expected_added
    assert GM.lower() in changes
    for p in ENTITY_FILES: assert f"attrib/{p}.rgd".lower() in changes
    readback = WORK / "readback"; assert not readback.exists()
    run([ARCHIVER, "unpack", archive, "--output", readback])
    for p in (GM, MODULE):
        assert sha(readback / new[p.lower()]["path"]) == sha(CANDIDATE / "assets" / p)
    report = {"version": VERSION, "guid": GUID, "archive": str(archive), "archive_sha256": sha(archive),
              "archive_members": len(new), "changed_members": changes, "added_members": sorted(expected_added),
              "unchanged_previous_members": len(old) - len(changes), "original_sources_preserved": guard(),
              "original_ability": "byte-preserved", "native_visual_acceptance": "pending fresh user test",
              "native_gameplay_acceptance": "pending speed, cadence and damage comparison",
              "renderer": "source-proven native posture selector; no orders or ability grants"}
    (WORK / "archive-inventory.json").write_text(json.dumps(after, indent=2))
    (package_dir / "PROBE-EVIDENCE.json").write_text(json.dumps(report, indent=2))
    shutil.copy2(WORK / "TEST-PROBE.txt", package_dir / "TEST-PROBE.txt")
    sys.path.insert(0, str(EXT)); from garrison_shared import mod_bundle
    details = {"id": "berber_future_kingdom", "name": "The Berber Dynasties", "version": VERSION,
               "summary": "Tuareg Q shield posture trial with native movement and attacks",
               "author": "hossein81 and marcokistan", "updated": "2026-10-11", "min_garrison": "0.1.3",
               "content_types": ["game-mode", "tuning-pack"],
               "description": "Private Tuareg schema adds the native shield posture selector while retaining the Donso schema. Existing Q controls its lifetime without issuing orders. No Byzantine Mode_Chooser, modifier or cheer command is added. Native appearance, speed, attacks and damage acceptance pending.",
               "changelog": "Replace movement-locking native cheer commands with the source-proven shield posture selector."}
    mod_bundle.write_manifest(package_dir, bundle_key="berber_future_kingdom", members=[{
        "mod_key": "berber_future_kingdom", "role": "tuning", "path": archive.name, "sha256": sha(archive)}], details=details)
    zip_path = WORK / f"berber_future_kingdom-{VERSION}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as output:
        for p in sorted(package_dir.iterdir()): output.write(p, p.name)
    with zipfile.ZipFile(zip_path) as output:
        assert output.testzip() is None
        assert hashlib.sha256(output.read(archive.name)).hexdigest() == report["archive_sha256"]
    report.update(zip=str(zip_path), zip_sha256=sha(zip_path))
    (WORK / "delivery.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("stage", choices=["prepare", "build", "package"])
    globals()[parser.parse_args().stage]()
