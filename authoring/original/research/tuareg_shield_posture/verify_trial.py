"""Verify private schema semantics, source guards and final package boundaries."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile
import zlib
import uuid

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "output/tuareg_shield_posture_test"
sys.path.insert(0, str(ROOT / "art/tuareg_shield"))
import q_posture_trial as trial

def properties(path):
    data = {}
    for node in ET.parse(path).iter("RGDNode"):
        children = list(node)
        identifiers = [x for x in children if (x.get("Key") or "").endswith("_property_id")]
        if identifiers:
            values = {x.get("Key"): x.get("Value") for x in children if x.get("Type") != "List"}
            key = identifiers[0].get("Value")
            assert key not in data or data[key] == values, key
            data[key] = values
    return data

def normalized_without_schema(path):
    root = ET.parse(path).getroot()
    for ext in root.iter("RGDNode"):
        if ext.get("Key") == "statemodel_ext":
            for child in list(ext):
                if child.get("Key") == "schema":
                    ext.remove(child)
                    ET.SubElement(ext, "RGDNode", Key="schema", Type="List")
    def canonical(node):
        return (node.tag, tuple(sorted(node.attrib.items())), tuple(canonical(child) for child in node))
    return canonical(root)

def schema_check(path):
    original = properties(WORK / "donso_mal.decoded.xml")
    private = properties(path)
    assert set(private) - set(original) == {"spearman_shield_wall_byz"}
    assert all(private.get(key) == value for key, value in original.items())
    assert private["spearman_shield_wall_byz"]["default"].lower() == "false"
    return {"donso_properties_preserved": len(original),
            "extra_properties": {key: private[key] for key in set(private) - set(original)}}

def verify():
    report = {"original_sources_preserved": trial.guard()}
    inventory = json.loads((WORK / "archive-inventory.json").read_text())
    members = {x["path"].lower(): x for x in inventory["members"]}
    delivery = json.loads((WORK / "delivery.json").read_text())
    decoded = WORK / "verification-decoded" / uuid.uuid4().hex
    decoded.mkdir(parents=True)
    report["readback_bound_to_archive"] = []
    for logical in delivery["changed_members"] + delivery["added_members"]:
        member = members[logical.lower()]
        retained = WORK / "readback" / member["path"]
        raw = retained.read_bytes()
        assert len(raw) == member["size"] and zlib.crc32(raw) == member["crc"], logical
        if logical.endswith(".rgd"):
            fresh = decoded / Path(logical).with_suffix(".xml")
            fresh.parent.mkdir(parents=True, exist_ok=True)
            trial.run([trial.ARCHIVER, "decode-rgd", retained, fresh])
            assert ET.tostring(ET.parse(fresh).getroot()) == ET.tostring(ET.parse(retained.with_suffix(".xml")).getroot()), logical
        report["readback_bound_to_archive"].append(logical)
    report["schema"] = schema_check(WORK / "readback" / f"attrib/{trial.SCHEMA}.xml")
    baseline = ROOT / "output/tuareg_shield_test/final-readback-v2-combined"
    report["compiled_records"] = []
    for logical in trial.ENTITY_FILES + trial.SQUAD_FILES:
        before = baseline / f"attrib/{logical}.xml"
        after = WORK / "readback" / f"attrib/{logical}.xml"
        assert normalized_without_schema(before) == normalized_without_schema(after), logical
        if logical in trial.ENTITY_FILES:
            references = ET.parse(after).findall('.//RGDNode[@Key="statemodel_ext"]/RGDNode[@Key="schema"]/RGDNode[@Key="$PBGNAME"]')
            assert references and all(x.get("Value") == trial.GUID + ":tuareg_shield_posture_ber" for x in references), logical
        report["compiled_records"].append({"record": logical, "non_schema_semantics": "unchanged"})
    candidate = WORK / "candidate"
    allowed_changes = {f"assets/attrib/instances/{logical}.xml" for logical in trial.ENTITY_FILES} | {"assets/" + trial.GM}
    baseline_hashes = json.loads((WORK / "source-baseline.json").read_text())
    differences = {name for name, digest in baseline_hashes.items() if trial.sha(candidate / name) != digest}
    assert differences == allowed_changes, differences
    report["candidate_changed_original_sources"] = sorted(differences)
    module = (candidate / "assets" / trial.MODULE).read_text()
    assert module == (ROOT / "art/tuareg_shield/tuareg_q_posture_trial.scar").read_text()
    for token in ("Cmd_Ability", "SGroup_AddAbility", "SGroup_RemoveAbility", "cheer_toggle", "Cmd_Move", "Cmd_Stop"):
        assert token not in module, token
    for logical in trial.ENTITY_FILES:
        text = (candidate / f"assets/attrib/instances/{logical}.xml").read_text()
        assert "spearman_shield_wall_toggle_byz" not in text
    archive = Path(delivery["archive"])
    assert trial.sha(archive) == delivery["archive_sha256"]
    with zipfile.ZipFile(delivery["zip"]) as packed:
        assert packed.testzip() is None
        assert hashlib.sha256(packed.read(archive.name)).hexdigest() == delivery["archive_sha256"]
        report["zip_members"] = packed.namelist()
    report["zip_sha256"] = trial.sha(Path(delivery["zip"]))
    assert report["zip_sha256"] == delivery["zip_sha256"]
    report["native_acceptance"] = "pending user match; no rendering or gameplay acceptance inferred"
    (WORK / "validation-summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "schema":
        result = schema_check(WORK / "private-schema-compiled.xml")
        (WORK / "schema-property-comparison.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
    else:
        verify()
