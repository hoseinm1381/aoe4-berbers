"""Compile editor-owned stamp probes to resolve private native model keys."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/berber_update_0_3_1"
STAGE = OUT / "stamp-probe"
SOURCE = STAGE / "source"
RUN = OUT / "stamp-probe-cook-model"
OLD = ROOT / "output/berber_update_0_2_6/integration/s"
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
CORE = EXT / "bin/core/garrison-core.exe"
ARCH = EXT / "bin/sga-archiver.exe"
EDITOR = Path(os.environ["LOCALAPPDATA"]) / "Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe"
sys.path[:0] = [str(ROOT / "research"), str(EXT)]
from economy_025_native_stamp import NativeTree, decompile


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(*args):
    result = subprocess.run(list(map(str, args)), capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"failed: {args}\n{result.stdout[-1000:]}\n{result.stderr[-2000:]}")
    return result.stdout


def source():
    assert (OLD / "source/_default.burnproj").exists()
    if not SOURCE.exists():
        shutil.copytree(OLD / "source", SOURCE)
        shutil.copy2(OLD / "buildings.aoe4mod", STAGE / "buildings.aoe4mod")
    burn = SOURCE / "_default.burnproj"
    raw = burn.read_text(encoding="utf-8")
    include = "art\\stamps\\garrison\\berber_buildings_031\\*.rdo"
    if include not in raw:
        assert raw.count("</Rules>") == 1
        rule = '<BurnRule><Alias>data</Alias><Burner>ReflectBurner</Burner><Configurations>Debug Release Profile RTM</Configurations><Excludes i:nil="true" /><Includes>' + include + '</Includes><IsEnabled>true</IsEnabled><NamedParameters>Reflect</NamedParameters><PathOverride i:nil="true" /><Target>Archive</Target></BurnRule>'
        burn.write_text(raw.replace("</Rules>", rule + "</Rules>"), encoding="utf-8")
    art = json.loads((OUT / "native-art-payload-report.json").read_text(encoding="utf-8"))
    assert len(art["models"]) == 13
    for entry in art["payloads"]:
        path = Path(entry["file"])
        assert sha(path) == entry["sha256"]
        dest = SOURCE / entry["member"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
    static = OUT / "garrison-cook-readback/art/scenario/b031"
    assert static.is_dir()
    for item in static.rglob("*"):
        if item.is_file():
            dest = SOURCE / item.relative_to(OUT / "garrison-cook-readback")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)
    models = [x["private"] for x in art["models"]]
    models.extend(p.with_suffix("").relative_to(OUT / "garrison-cook-readback").as_posix() for p in static.rglob("*.rgm"))
    assert len(models) == len(set(models))
    probe_stock = ROOT / "output/berber_update_0_2_5/integration/stock/art/stamps/civ_mal/mal_gristmill.bin"
    tree = NativeTree(probe_stock)
    old_model = next(tree.field(o, o["fields"]["m_blueprint"])["text"].replace("\\", "/") for o in tree.objects.values() if o["type"] == "VisualStampBlueprint" and "mal_gristmill_control" in tree.field(o, o["fields"]["m_blueprint"])["text"])
    probes = []
    for index, private in enumerate(sorted(models)):
        xml = ET.fromstring(decompile(tree, {old_model: private}))
        ids = {node.get("Id"): str(int.from_bytes(hashlib.sha256((private + ":" + node.get("Id")).encode()).digest()[:8], "little")) for node in xml.iter("DataObject")}
        for node in xml.iter():
            for attr in ("Id", "OwnerId"):
                if node.get(attr) in ids:
                    node.set(attr, ids[node.get(attr)])
            if node.tag == "DataValue" and node.text in ids:
                node.text = ids[node.text]
            if node.tag == "DataProperty" and node.get("Name") == "m_objectID" and node.get("Value") in ids:
                node.set("Value", ids[node.get("Value")])
        target = SOURCE / f"art/stamps/garrison/berber_buildings_031/probe_{index:02}.rdo"
        target.parent.mkdir(parents=True, exist_ok=True)
        ET.indent(xml)
        target.write_bytes(ET.tostring(xml, encoding="utf-8"))
        probes.append({"path": str(target), "model": private, "sha256": sha(target)})
    (STAGE / "probe-specs.json").write_text(json.dumps({"models": models, "probes": probes, "status": "source ready"}, indent=2) + "\n", encoding="utf-8")
    print("STAMP_PROBE_SOURCE_READY", len(probes), flush=True)


def cook():
    specs = json.loads((STAGE / "probe-specs.json").read_text(encoding="utf-8"))
    assert len(specs["probes"]) >= 13
    run(CORE, "essence", "build-mod", "--editor", EDITOR, "--mod", STAGE / "buildings.aoe4mod", "--run-root", RUN, "--timeout", "600")
    state = json.loads((RUN / "run.json").read_text(encoding="utf-8"))
    assert state["status"] == "succeeded"
    print("STAMP_PROBE_NATIVE_COOK_PASSED", flush=True)


def keytable():
    archives = list((RUN / "output").rglob("*.sga"))
    assert len(archives) == 1, archives
    readback = OUT / "stamp-probe-readback"
    if not readback.exists():
        run(ARCH, "unpack", archives[0], "--output", readback)
    specs = json.loads((STAGE / "probe-specs.json").read_text(encoding="utf-8"))
    keys = {}
    for index, model in enumerate(sorted(specs["models"])):
        tree = NativeTree(readback / f"art/stamps/garrison/berber_buildings_031/probe_{index:02}.bin")
        hits = [tree.field(o, o["fields"]["m_blueprint"]) for o in tree.objects.values() if o["type"] == "VisualStampBlueprint" and tree.field(o, o["fields"]["m_blueprint"])["text"].replace("\\", "/") == model]
        assert len(hits) == 1, (model, len(hits))
        keys[model.replace("/", "\\")] = {**hits[0], "kind": "Reflect::ReflectStringHash"}
    target = STAGE / "native-model-key-table.json"
    target.write_text(json.dumps({"status": "passed", "keys": keys, "archive": str(archives[0]), "archive_sha256": sha(archives[0])}, indent=2) + "\n", encoding="utf-8")
    print("STAMP_PROBE_KEYS_READY", len(keys), flush=True)


if __name__ == "__main__":
    globals()[sys.argv[1]]()
