"""Cook reference-only RDO probes to obtain editor-owned native model keys.

This is a temporary authoring cook. Its unrelated 0.2.6 source is a known
working validation scaffold; only the 0.3.0 probe hashes are consumed.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/berber_update_0_3_0"
STAGE = OUT / "stamp-probe"
SOURCE = STAGE / "source"
RUN = OUT / "stamp-probe-cook-short"
OLD = ROOT / "output/berber_update_0_2_6/integration/s"
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
CORE = EXT / "bin/core/garrison-core.exe"
ARCH = EXT / "bin/sga-archiver.exe"
EDITOR = Path("E:/Games/steamapps/common/Age of Empires IV/EssenceEditor.exe")
sys.path[:0] = [str(ROOT / "research"), str(EXT)]
from economy_025_native_stamp import NativeTree, decompile


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(args):
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
    text = burn.read_text(encoding="utf-8")
    include = "art\\stamps\\garrison\\berber_buildings_030\\*.rdo"
    if include not in text:
        assert text.count("</Rules>") == 1
        rule = "<BurnRule><Alias>data</Alias><Burner>ReflectBurner</Burner><Configurations>Debug Release Profile RTM</Configurations><Excludes i:nil=\"true\" /><Includes>" + include + "</Includes><IsEnabled>true</IsEnabled><NamedParameters>Reflect</NamedParameters><PathOverride i:nil=\"true\" /><Target>Archive</Target></BurnRule>"
        burn.write_text(text.replace("</Rules>", rule + "</Rules>"), encoding="utf-8")
    art = json.loads((OUT / "native-art-payload-report.json").read_text(encoding="utf-8"))
    assert len(art["models"]) == 12
    for entry in art["payloads"]:
        path = Path(entry["file"])
        assert sha(path) == entry["sha256"]
        dest = SOURCE / entry["member"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
    annex = OUT / "annex-short-readback"
    if not annex.exists():
        cooked = Path("C:/Users/RS/AppData/Local/Temp/garrison-builds/20261015T010000Z-b03a/cook/output/extension/garrison_static/garrison_static.sga")
        assert cooked.exists()
        run([ARCH, "unpack", cooked, "--output", annex])
    for item in (annex / "art/scenario/b030/aa").rglob("*"):
        if item.is_file():
            relative = item.relative_to(annex)
            dest = SOURCE / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)
    models = list(art["model_mapping"].values())
    models += [p.with_suffix("").relative_to(annex).as_posix() for p in (annex / "art/scenario/b030/aa").glob("*.rgm")]
    assert len(models) == 15
    probe_stock = ROOT / "output/berber_update_0_2_5/integration/stock/art/stamps/civ_mal/mal_gristmill.bin"
    tree = NativeTree(probe_stock)
    old_model = next(tree.field(o, o["fields"]["m_blueprint"])["text"].replace("\\", "/") for o in tree.objects.values() if o["type"] == "VisualStampBlueprint" and "mal_gristmill_control" in tree.field(o, o["fields"]["m_blueprint"])["text"])
    probes = []
    for i, private in enumerate(sorted(models)):
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
        target = SOURCE / f"art/stamps/garrison/berber_buildings_030/probe_{i:02}.rdo"
        target.parent.mkdir(parents=True, exist_ok=True)
        ET.indent(xml)
        target.write_bytes(ET.tostring(xml, encoding="utf-8"))
        probes.append({"path": str(target), "model": private, "sha256": sha(target)})
    (STAGE / "probe-specs.json").write_text(json.dumps({"models": models, "probes": probes, "status": "source ready"}, indent=2) + "\n", encoding="utf-8")
    print("STAMP_PROBE_SOURCE_READY", len(probes), flush=True)


def cook():
    specs = json.loads((STAGE / "probe-specs.json").read_text(encoding="utf-8"))
    assert len(specs["probes"]) == 15
    run([CORE, "essence", "build-mod", "--editor", EDITOR, "--mod", STAGE / "buildings.aoe4mod", "--run-root", RUN, "--timeout", "600"])
    state = json.loads((RUN / "run.json").read_text(encoding="utf-8"))
    assert state["status"] == "succeeded"
    print("STAMP_PROBE_NATIVE_COOK_PASSED", flush=True)


def keytable():
    archives = list((RUN / "output").rglob("*.sga"))
    assert len(archives) == 1, archives
    readback = OUT / "stamp-probe-short-readback"
    if not readback.exists():
        run([ARCH, "unpack", archives[0], "--output", readback])
    specs = json.loads((STAGE / "probe-specs.json").read_text(encoding="utf-8"))
    keys = {}
    for i, model in enumerate(sorted(specs["models"])):
        path = readback / f"art/stamps/garrison/berber_buildings_030/probe_{i:02}.bin"
        tree = NativeTree(path)
        hits = [tree.field(o, o["fields"]["m_blueprint"]) for o in tree.objects.values() if o["type"] == "VisualStampBlueprint" and tree.field(o, o["fields"]["m_blueprint"])["text"].replace("\\", "/") == model]
        assert len(hits) == 1, (model, len(hits))
        keys[model.replace("/", "\\")] = {**hits[0], "kind": "Reflect::ReflectStringHash"}
    target = STAGE / "native-model-key-table.json"
    target.write_text(json.dumps({"status": "passed", "keys": keys, "archive": str(archives[0]), "archive_sha256": sha(archives[0])}, indent=2) + "\n", encoding="utf-8")
    print("STAMP_PROBE_KEYS_READY", len(keys), flush=True)


if __name__ == "__main__":
    globals()[sys.argv[1]]()
