"""Test scaled whole Byzantine donor as a market architectural insert."""

import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from berber_030_market_pilot import add_donor, bounds, render


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    market, _ = add_donor("1ab6b9d2f7f10490f630", "Abbasid market")
    byz, _ = add_donor("4550424ff074a6ab50fd", "Byzantine mercenary frontage")
    byz.scale = (.5, .5, .5)
    byz.location = (0.0, -.4, -.82)
    bpy.context.view_layer.update()
    core = [o for o in market.children_recursive if o.type == "MESH"]
    annex = [o for o in byz.children_recursive if o.type == "MESH"]
    print("WHOLE_BYZ_MARKET", bounds(core), bounds(annex))
    render("market_age02_whole_byz_test", core + annex)


if __name__ == "__main__":
    main()
