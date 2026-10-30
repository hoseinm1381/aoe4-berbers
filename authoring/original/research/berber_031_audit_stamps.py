"""Inspect native stock visual-stamp model refs before scoped 0.3.1 rebinding."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))
from economy_025_native_stamp import NativeTree

OUT = ROOT / "output/berber_update_0_3_1"
CACHE = ROOT / "output/shared_stock_cache/buildings_031/stamps"


def main():
    specs = json.loads((OUT / "binding-specs.json").read_text(encoding="utf-8"))["specs"]
    report = []
    for spec in specs:
        field = next(v for p, v in spec["stock_stamp_fields"] if p.startswith("default/") and "const_dest" not in v)
        member = field.replace("\\", "/") + ".bin"
        tree = NativeTree(CACHE / member)
        models = []
        for obj in tree.objects.values():
            if obj["type"] == "VisualStampBlueprint" and "m_blueprint" in obj["fields"]:
                models.append({"id": obj["id"], "model": tree.field(obj, obj["fields"]["m_blueprint"])["text"].replace("\\", "/"), "field_type": obj["fields"]["m_blueprint"].get("FieldTypeName")})
        report.append({"family": spec["family"], "age": spec["age"], "stamp": member, "visual_models": models, "native_objects": len(tree.objects)})
        print("STAMP", spec["family"], spec["age"], len(models), "models", flush=True)
    (OUT / "stock-stamp-models.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
