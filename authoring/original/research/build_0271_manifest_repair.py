"""Repackage the unchanged 0.2.7.1 content with an importable SemVer manifest."""

import hashlib
import json
import os
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "output/berber_update_0_2_7_1/berber_future_kingdom-0.2.7.1.zip"
OUT = ROOT / "output/berber_update_0_2_7_1_manifest_repair"
TARGET = OUT / "berber_future_kingdom-0.2.8-test.zip"
TEMP = OUT / "berber_future_kingdom-0.2.8-test.tmp.zip"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    if TARGET.exists() or TEMP.exists():
        raise FileExistsError("Refusing to overwrite an existing repair package or temporary archive")
    OUT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(SOURCE, "r") as source, zipfile.ZipFile(TEMP, "w") as target:
        if source.testzip() is not None:
            raise ValueError("Original 0.2.7.1 ZIP has a bad member")
        manifest = json.loads(source.read("garrison.json"))
        if manifest["details"]["version"] != "0.2.7.1":
            raise ValueError("Source manifest is not the expected 0.2.7.1 release")
        manifest["details"]["version"] = "0.2.8"
        for item in source.infolist():
            payload = source.read(item.filename)
            if item.filename == "garrison.json":
                payload = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
            target.writestr(item, payload)
    with zipfile.ZipFile(SOURCE, "r") as source, zipfile.ZipFile(TEMP, "r") as target:
        if target.testzip() is not None or source.namelist() != target.namelist():
            raise ValueError("Repaired ZIP is unreadable or has a changed member list")
        for name in source.namelist():
            if name != "garrison.json" and source.read(name) != target.read(name):
                raise ValueError(f"Unrelated ZIP member changed: {name}")
        sga_sha = sha256(target.read("Berber_future_kingdom.sga"))
        if sga_sha != manifest["members"][0]["sha256"]:
            raise ValueError("Packaged SGA hash does not match the manifest")
    os.replace(TEMP, TARGET)
    report = {
        "purpose": "Garrison import test of unchanged 0.2.7.1 content",
        "manifest_only_change": {"details.version": ["0.2.7.1", "0.2.8"]},
        "original_zip": str(SOURCE),
        "original_zip_sha256": sha256(SOURCE.read_bytes()),
        "repaired_zip": str(TARGET),
        "repaired_zip_sha256": sha256(TARGET.read_bytes()),
        "packaged_sga_sha256": sga_sha,
        "unchanged_members": [name for name in source.namelist() if name != "garrison.json"],
        "native_import_and_gameplay": "Pending user test",
    }
    (OUT / "delivery.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
