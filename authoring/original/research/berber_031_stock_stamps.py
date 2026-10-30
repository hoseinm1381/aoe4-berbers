"""Cache exact native healthy stamps referenced by the 13 source tiers."""

import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/berber_update_0_3_1"
CACHE = ROOT / "output/shared_stock_cache/buildings_031/stamps"
DATA = Path("E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Data.sga")
ARCH = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    specs = json.loads((OUT / "binding-specs.json").read_text(encoding="utf-8"))["specs"]
    sources = sorted({value.replace("\\", "/") + ".bin" for spec in specs for path, value in spec["stock_stamp_fields"] if path.startswith("default/") and "const_dest" not in value})
    manifest = []
    for member in sources:
        target = CACHE / member
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file():
            r = subprocess.run([str(ARCH), "extract-member", str(DATA), member, str(target)], capture_output=True, text=True, encoding="utf-8")
            if r.returncode:
                raise RuntimeError(f"{member}: {r.stderr}")
        manifest.append({"member": member, "bytes": target.stat().st_size, "sha256": sha(target), "file": str(target)})
        print("CACHED_STAMP", member, target.stat().st_size, flush=True)
    (OUT / "stock-stamp-provenance.json").write_text(json.dumps({"archive": str(DATA), "archive_sha256": sha(DATA), "stamps": manifest}, indent=2) + "\n", encoding="utf-8")
    print("BERBER_031_STOCK_STAMPS", len(manifest))


if __name__ == "__main__":
    main()
