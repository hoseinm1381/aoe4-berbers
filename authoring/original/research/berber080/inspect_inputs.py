from pathlib import Path
import hashlib, json, re, subprocess, sys

ROOT = Path(__file__).absolute().parents[2]
SOURCE = Path(r"F:\aoe_4_temp\Berber_future_kingdom_ai_20261014\output\Berber-0.7.4-handoff.1-2026-10-17")
OUT = SOURCE.parent / "berber_update_0_8_0"
HERE = Path(__file__).parent
sys.path.insert(0, str(ROOT / "research/berber060"))
from common import ARCH, EXT
sys.path.insert(0, str(EXT))
from garrison_shared import rgd


def extract(member):
    target = OUT / "inspection" / member
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        subprocess.run([str(ARCH), "extract-member", str(SOURCE / "berber_future_kingdom.sga"), member, str(target)], capture_output=True, check=True)
    return target


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    inventory = json.loads(subprocess.run([str(ARCH), "list", str(SOURCE / "berber_future_kingdom.sga"), "--verify"], check=True, capture_output=True, text=True).stdout)
    bank = (SOURCE / "mod-source/scar/berber_voice_bank.scar").read_text()
    families = re.findall(r'^\["([a-z_]+)"\]=\{\s*$', bank, re.M)
    for family in ("villager", "tuareg"):
        section = re.search(r'^\["' + family + r'"\]=\{\n(.*?)^\},', bank, re.M | re.S)
        clips = re.findall(r'"(audio/voices/[a-f0-9]+\.wav)"', section.group(1)) if section else []
        paths = {m["path"] for m in inventory["members"]}
        print(family, "actions", re.findall(r'^\["([a-z]+)"\]', section.group(1), re.M) if section else [], "unique WAVs", len(set(clips)), "missing WAVs", len(set(clips) - paths))
    restored = json.loads((SOURCE / "evidence/restored-native-bindings.json").read_text())
    rows = []
    for member in [r["member"] for r in restored] + ["attrib/ebps/races/malian/units/unit_scout_1_mal.rgd", "attrib/sbps/races/malian/berbers/unit_scout_1_mal.rgd"]:
        if not any(m["path"] == member for m in inventory["members"]):
            continue
        path = extract(member)
        doc = rgd.read(path.read_bytes())
        speakers = [(p, n.kind, n.value) for p, n in rgd.flatten(doc.nodes) if "speaker_code" in p or "speech_ext" in p and n.kind == "CString"]
        row = {"member": member, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "speakers": speakers}
        rows.append(row)
        print(json.dumps(row))
    (OUT / "input-speech-inventory.json").write_text(json.dumps({"families": families, "rows": rows, "base_verified": inventory["archive"]["verification"]}, indent=2) + "\n")
