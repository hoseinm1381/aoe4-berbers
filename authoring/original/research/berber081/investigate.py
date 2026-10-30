from pathlib import Path
import json, subprocess, sys

ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT / "research/berber080"))
from inspect_inputs import ARCH, rgd
BASE = Path(r"F:\aoe_4_temp\Berber_future_kingdom_ai_20261014\output\berber_update_0_8_0\Berber_future_kingdom.sga")
OUT = BASE.parent.parent / "berber_update_0_8_1"


def extract(member):
    path = OUT / "investigation" / member
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        subprocess.run([str(ARCH), "extract-member", str(BASE), member, str(path)], check=True, capture_output=True)
    return path


if __name__ == "__main__":
    listing = json.loads(subprocess.run([str(ARCH), "list", str(BASE)], check=True, capture_output=True, text=True).stdout)
    names = [m["path"] for m in listing["members"] if "villager" in m["path"].lower() and m["path"].endswith(".rgd")]
    print("Villager archive entries:", json.dumps(names))
    rows = []
    for name in names:
        data = rgd.read(extract(name).read_bytes())
        fields = [(p, n.kind, n.value) for p, n in rgd.flatten(data.nodes) if not isinstance(n.value, list) and any(x in p.lower() for x in ("speech", "speaker", "variant", "loadout", "spawn", "entity", "blueprint"))]
        rows.append({"member": name, "fields": fields})
        print(name, json.dumps(fields))
    (OUT / "villager-inventory.json").write_text(json.dumps(rows, indent=2) + "\n")
