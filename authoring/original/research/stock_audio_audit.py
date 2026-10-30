"""Audit installed loose audio against locally retained installed Steam depots.

Optionally quarantine non-depot files only, after a verified restore ZIP exists.
Never repairs/deletes a Steam-declared file. No Steam or Garrison state mutations.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import stat
import struct
import subprocess
import zipfile

GAME = Path(r"E:\Games\steamapps\common\Age of Empires IV")
DEPOTS = Path(r"E:\Games\depotcache")
OUT = Path(r"F:\aoe_4_temp\Berber_future_kingdom_ai_20261014\output\stock_audio_restore_20261017")
SCOPES = ("cardinal/audio/",)


def digest(path, algorithm="sha256"):
    with path.open("rb") as f:
        return hashlib.file_digest(f, algorithm).hexdigest()


def varint(buf, pos):
    value = 0
    for shift in range(0, 70, 7):
        byte = buf[pos]
        pos += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, pos
    raise ValueError("Invalid protobuf varint")


def fields(buf):
    pos = 0
    while pos < len(buf):
        tag, pos = varint(buf, pos)
        number, wire = tag >> 3, tag & 7
        if wire == 0:
            value, pos = varint(buf, pos)
        elif wire == 2:
            size, pos = varint(buf, pos)
            value = buf[pos:pos + size]
            assert len(value) == size
            pos += size
        elif wire in (1, 5):
            size = 8 if wire == 1 else 4
            value = buf[pos:pos + size]
            assert len(value) == size
            pos += size
        else:
            raise ValueError(f"Unsupported wire {wire}")
        yield number, value


def no_reparse(path):
    path = path.absolute()
    for part in (path, *path.parents):
        if part.exists():
            assert not part.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, str(part)
    return path.resolve(strict=True)


def game_closed():
    result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq RelicCardinal.exe", "/NH"], capture_output=True, text=True, check=True)
    assert "reliccardinal.exe" not in result.stdout.lower(), "Close AoE4 before changing audio"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quarantine", action="store_true")
    args = parser.parse_args()
    game_closed()
    no_reparse(GAME)
    OUT.mkdir(exist_ok=True)
    no_reparse(OUT)
    appmanifest = GAME.parents[1] / "appmanifest_1466860.acf"
    apptext = appmanifest.read_text()
    installed = re.search(r'"InstalledDepots"\s*\{(.*?)\n\t\}', apptext, re.S).group(1)
    depot_ids = re.findall(r'"(\d+)"\s*\{\s*"manifest"\s*"(\d+)"', installed)
    assert len(depot_ids) == 3, depot_ids
    stock = {}
    directories = set()
    metadata = []
    for depot, manifest in depot_ids:
        source = DEPOTS / f"{depot}_{manifest}.manifest"
        buf = source.read_bytes()
        magic, length = struct.unpack_from("<II", buf)
        assert magic == 0x71F617D0 and length <= len(buf) - 8
        metadata.append({"path": str(source), "sha256": digest(source)})
        for field, value in fields(buf[8:8 + length]):
            assert field == 1
            row = dict(fields(value))
            name = row[1].decode("utf-8").replace("\\", "/")
            assert not name.startswith("/") and ".." not in name.split("/")
            name = name.lower()
            if row.get(3, 0) & 64:
                directories.add(name)
                continue
            if name == "relicgame.module" or any(name.startswith(scope) for scope in SCOPES):
                assert isinstance(row[2], int) and len(row[5]) == 20
                entry = {"bytes": row[2], "sha1": row[5].hex()}
                assert name not in stock or stock[name] == entry
                stock[name] = entry
    # Sanity-check schema interpretation against a known installed file.
    assert digest(GAME / "RelicGame.module", "sha1") == stock["relicgame.module"]["sha1"]
    observed = {}
    observed_dirs = []
    for scope in SCOPES:
        folder = GAME / scope.rstrip("/")
        no_reparse(folder)
        for current, child_dirs, child_files in os.walk(folder, followlinks=False):
            current = Path(current)
            for name in child_dirs:
                path = current / name
                assert not path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, str(path)
                observed_dirs.append(path.relative_to(GAME).as_posix())
            for name in child_files:
                path = current / name
                assert not path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, str(path)
                relative = path.relative_to(GAME).as_posix()
                observed[relative.lower()] = (relative, path)
    print(f"Inventory: {len(observed)} loose files; checking installed Steam content hashes", flush=True)
    matched, mismatched, missing, extras = [], [], [], []
    for checked, (name, expected) in enumerate(stock.items()):
        if checked and checked % 1000 == 0:
            print(f"Steam hash verification: {checked}/{len(stock)}", flush=True)
        if name == "relicgame.module":
            continue
        if name not in observed:
            missing.append(name)
        else:
            relative, path = observed[name]
            actual = {"bytes": path.stat().st_size, "sha1": digest(path, "sha1")}
            (matched if actual == expected else mismatched).append({"path": relative, "expected": expected, "actual": actual})
    for name, (relative, path) in observed.items():
        if name not in stock:
            extras.append({"path": relative, "bytes": path.stat().st_size, "sha256": digest(path)})
    nonstock_dirs = [name for name in observed_dirs if name.lower() not in directories]
    report = {"schema": "berber-stock-audio-audit/v1", "game_root": str(GAME), "depots": metadata,
              "stock_files_matched": len(matched), "stock_bytes_matched": sum(row["actual"]["bytes"] for row in matched),
              "mismatches": mismatched, "missing": missing, "extra_files": extras,
              "extra_bytes": sum(row["bytes"] for row in extras), "nonstock_directories": nonstock_dirs,
              "stock_files_touched": 0, "scope": SCOPES, "applied": False}
    (OUT / "audit-before.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"stock_files_matched": len(matched), "mismatches": mismatched[:4], "missing": missing[:4], "extra_files": len(extras), "extra_bytes": report["extra_bytes"], "nonstock_dirs": len(nonstock_dirs)}), flush=True)
    if not args.quarantine:
        return
    assert not mismatched and not missing, "Steam-declared audio needs repair; leaving game untouched"
    backup = OUT / "nonstock-loose-audio-backup.zip"
    assert not backup.exists(), "Backup already exists; inspect audit instead of rerunning"
    with zipfile.ZipFile(backup, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for row in extras:
            z.write(GAME / row["path"], row["path"])
        z.writestr("RESTORE.txt", "Close AoE4. To restore these optional loose audio additions, extract the cardinal/ tree into the recorded game root. Stock files are not included or changed.\n")
    with zipfile.ZipFile(backup) as z:
        assert z.testzip() is None
        for row in extras:
            with z.open(row["path"]) as f:
                assert hashlib.file_digest(f, "sha256").hexdigest() == row["sha256"]
    report["backup"] = {"path": str(backup), "sha256": digest(backup), "bytes": backup.stat().st_size}
    (OUT / "approved-quarantine-inventory.json").write_text(json.dumps(report, indent=2) + "\n")
    game_closed()
    for row in extras:
        path = no_reparse(GAME / row["path"])
        assert path.is_relative_to(GAME.resolve()) and any(row["path"].lower().startswith(scope) for scope in SCOPES)
        assert row["path"].lower() not in stock and digest(path) == row["sha256"]
        path.unlink()
    removed_dirs = []
    for relative in sorted(nonstock_dirs, key=lambda x: len(Path(x).parts), reverse=True):
        path = no_reparse(GAME / relative)
        assert path.is_relative_to(GAME.resolve()) and relative.lower() not in directories
        if not any(path.iterdir()):
            path.rmdir()
            removed_dirs.append(relative)
    # Fresh post-mutation verification against every stock loose-audio entry.
    for name, expected in stock.items():
        path = GAME / name
        assert path.stat().st_size == expected["bytes"] and digest(path, "sha1") == expected["sha1"], name
    remaining = []
    for scope in SCOPES:
        for path in (GAME / scope.rstrip("/")).rglob("*"):
            if path.is_file() and path.relative_to(GAME).as_posix().lower() not in stock:
                remaining.append(str(path))
    assert not remaining, remaining
    assert digest(backup) == report["backup"]["sha256"]
    report.update(applied=True, removed_nonstock_files=len(extras), removed_empty_directories=removed_dirs,
                  post_stock_hashes_verified=True, post_nonstock_files=0,
                  result="Loose audio matches installed Steam depot manifests; all additions backed up outside game")
    (OUT / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"result": report["result"], "removed_nonstock_files": len(extras), "backup": report["backup"]}, indent=2))


if __name__ == "__main__":
    main()
