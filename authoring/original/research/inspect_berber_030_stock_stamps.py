"""Print native visual components for the selected Age II-IV stock donors."""

from pathlib import Path
from collections import Counter

from economy_025_native_stamp import NativeTree


ROOT = Path(__file__).resolve().parents[1]
STAMPS = ROOT / "output/shared_stock_cache/buildings_030/stamps/art/stamps/civ_abbasid"

for path in sorted(STAMPS.glob("*.bin")):
    tree = NativeTree(path)
    print(f"{path.name}: {len(tree.objects)} native objects")
    components = Counter(
        tree.field(obj, obj["fields"]["m_blueprint"])["text"]
        for obj in tree.objects.values()
        if obj["type"] == "VisualStampBlueprint"
    )
    for component, count in sorted(components.items()):
        print(f"  {count:2} {component}")
