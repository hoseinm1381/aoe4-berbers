"""Check whether a topology-preserving Byzantine wing collapse is acceptable."""

import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))

from berber_030_market_pilot import CACHE, add_donor, bounds, render


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    market, _ = add_donor("1ab6b9d2f7f10490f630", "Abbasid market")
    byz, _ = add_donor("4550424ff074a6ab50fd", "Byzantine annex")
    edits = 0
    for obj in byz.children_recursive:
        if obj.type != "MESH":
            continue
        for vertex in obj.data.vertices:
            if vertex.co.x < 2.35:
                vertex.co = (3.7, -2.5, 1.5)
                edits += 1
    byz.scale = (.61, .61, .61)
    byz.location = (-.65, -.1, -.66)
    bpy.context.view_layer.update()
    meshes = [o for root in (market, byz) for o in root.children_recursive if o.type == "MESH"]
    print("COLLAPSE_PREVIEW", edits, bounds(meshes))
    render("market_age02_native_collapse_test", meshes)


if __name__ == "__main__":
    main()
