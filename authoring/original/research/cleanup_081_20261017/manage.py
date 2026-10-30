"""Explicit older-delivery cleanup; preserve all loose assets and base SGAs."""
from pathlib import Path
import hashlib
import json
import os
import stat
import subprocess
import sys
import zipfile

ROOT = Path(__file__).absolute().parents[2]
EXTERNAL = Path(r"F:\aoe_4_temp\Berber_future_kingdom_ai_20261014")
OUT = EXTERNAL / "output"
REPORT = Path(__file__).parent
MAP = ROOT / "research/cleanup_20261016/deletion-plan.json"
CURRENT = OUT / "berber_update_0_8_1/Berber-0.8.1.zip"
OLD_ZIPS = [OUT / p for p in (
    "berber_update_0_7_3/Berber-0.7.3-MAIN-GARRISON.zip",
    "berber_update_0_7_3/Berber-0.7.3-VOICES-INSTALLER.zip",
    "Berber-0.7.4-handoff.1-2026-10-17.zip",
    "berber_update_0_7_5/Berber-0.7.5-fixed.zip",
    "berber_update_0_8_0/Berber-0.8.0.zip",
)]


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def safe(path):
    path = Path(path)
    assert path.is_absolute() and path.resolve(strict=True) == path
    assert path.is_relative_to(ROOT) or path.is_relative_to(EXTERNAL)
    for ancestor in (path, *path.parents):
        assert not ancestor.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, str(ancestor)
    return path


def validate_current():
    sys.path.insert(0, str(ROOT / "research"))
    import package_unified_release
    return package_unified_release.check()


def expanded_proof(source_zip, folder):
    result, unmatched = {}, []
    with zipfile.ZipFile(source_zip) as z:
        assert z.testzip() is None
        files = [x for x in z.infolist() if not x.is_dir()]
        for number, item in enumerate(files):
            member = item.filename
            relative = member
            if relative.startswith(folder.name + "/"):
                relative = relative[len(folder.name) + 1:]
            target = folder / relative
            if not target.is_file() or target.stat().st_size != item.file_size:
                unmatched.append(member)
                continue
            with z.open(member) as f:
                digest = hashlib.file_digest(f, "sha256").hexdigest()
            if sha(safe(target)) != digest:
                unmatched.append(member)
                continue
            result[member] = {"file": str(target), "sha256": digest}
            if number % 1000 == 0:
                print("PRESERVED EXPANDED MEMBERS", source_zip.name, number, "/", len(files), flush=True)
    return {"zip": str(source_zip), "expanded": str(folder), "matched": result, "unmatched": unmatched}


def prepare():
    print("Verifying working release", flush=True)
    current = validate_current()
    names = subprocess.run(["rg", "--files", "--hidden", "-g", "*.zip", "-g", "*.sga", "-g", "!**/.git/**", str(ROOT), str(EXTERNAL)], check=True, capture_output=True, text=True).stdout.splitlines()
    archives = sorted({str(Path(name).resolve()) for name in names})
    inventory = []
    for name in archives:
        path = safe(Path(name))
        inventory.append({"path": name, "bytes": path.stat().st_size, "sha256": sha(path)})
    save(REPORT / "archives-inventory.json", inventory)
    print("Archives inventoried:", len(inventory), flush=True)
    proofs = {}
    for source, folder in (
        (OLD_ZIPS[1], OUT / "berber_update_0_7_3/Berber-0.7.3-VOICES-INSTALLER"),
        (OLD_ZIPS[2], OUT / "Berber-0.7.4-handoff.1-2026-10-17"),
    ):
        if source.exists():
            proofs[str(source)] = expanded_proof(source, folder)
    save(REPORT / "archive-preservation-proof.json", proofs)
    candidates, retained = [], []
    for row in inventory:
        path = Path(row["path"])
        if path in OLD_ZIPS:
            proof = proofs.get(str(path))
            if proof and proof["unmatched"]:
                retained.append({**row, "reason": "Archive has unmatched expanded inputs; preserve until resolved", "unmatched": proof["unmatched"]})
            else:
                candidates.append({**row, "mtime_ns": path.stat().st_mtime_ns,
                                   "reason": "Older delivery; retained base SGA/recipes or hash-matching expanded source preserve rebuild inputs"})
        else:
            reason = "Working 0.8.1 delivery" if path == CURRENT else (
                "Required base/source SGA; existing patch-chain or authoring provenance" if path.suffix.lower() == ".sga" else
                "Voice backup or compressed source/rebuild/tool input; not an obsolete delivery")
            retained.append({**row, "reason": reason})
    removal = {r["path"] for r in candidates}
    restore = read(MAP)
    edits = []
    for row in restore["files"]:
        source = row["restore"]
        if "zip" not in source:
            continue
        canonical = str(Path(source["zip"]).resolve())
        if canonical not in removal:
            continue
        replacement = proofs.get(canonical, {}).get("matched", {}).get(source["member"])
        assert replacement and replacement["sha256"] == row["sha256"], "Restore source not preserved: " + source["member"]
        edits.append({"path": row["path"], "before": source, "after": replacement})
        row["restore"] = replacement
    # Check all unique remaining restore inputs still exist, not merely changed references.
    dependencies = set()
    resolved_dependencies = {}
    for row in restore["files"]:
        source = row["restore"]
        for key in ("file", "zip", "wem", "decoder"):
            if key in source:
                if source[key] not in resolved_dependencies:
                    p = Path(source[key]).resolve()
                    assert str(p) not in removal and p.is_file(), str(p)
                    resolved_dependencies[source[key]] = p
                p = resolved_dependencies[source[key]]
                dependencies.add(str(p))
    save(REPORT / "restore-source-migration.json", edits)
    save(REPORT / "migrated-restore-map.json", restore)
    plan = {"status": "prepared", "current_preflight": current, "files": candidates,
            "retained": retained, "bytes_before": sum(r["bytes"] for r in candidates),
            "restore_references_migrated": len(edits), "restore_dependencies_present": len(dependencies),
            "temporary_sgas_removed": 0,
            "temporary_builds": "Recent release-owned temporary builds already removed by verified 0.8.0/0.8.1 cleanup; remaining SGAs retained as inputs",
            "scope": "Explicit older delivery ZIPs only; no Blender, loose voice, texture, model, source, game or Git files deleted"}
    save(REPORT / "deletion-plan.json", plan)
    print(json.dumps({k: v for k, v in plan.items() if k not in ("files", "retained", "current_preflight")}, indent=2), flush=True)


def apply():
    plan = read(REPORT / "deletion-plan.json")
    print("Rechecking selected deliveries and protected bases", flush=True)
    validate_current()
    for row in plan["files"]:
        path = safe(Path(row["path"]))
        assert path in OLD_ZIPS and path.suffix == ".zip" and path != CURRENT
        assert path.stat().st_size == row["bytes"] and path.stat().st_mtime_ns == row["mtime_ns"] and sha(path) == row["sha256"]
    for row in plan["retained"]:
        assert sha(safe(Path(row["path"]))) == row["sha256"]
    verified_restore_files = {}
    for number, row in enumerate(read(REPORT / "restore-source-migration.json")):
        name = row["after"]["file"]
        if name not in verified_restore_files:
            verified_restore_files[name] = sha(safe(Path(name)))
        assert verified_restore_files[name] == row["after"]["sha256"]
        if number % 1000 == 0:
            print("RESTORE SOURCE PREFLIGHT", number, "/", plan["restore_references_migrated"], flush=True)
    # Commit verified restore redirects before retiring their ZIP containers.
    migrated = REPORT / "migrated-restore-map.json"
    temp = MAP.with_suffix(".081-migration.tmp")
    temp.write_bytes(migrated.read_bytes())
    os.replace(temp, MAP)
    result = {"status": "in_progress", "removed": [], "bytes_reclaimed_by_drive": {"E:": 0, "F:": 0}}
    save(REPORT / "result.json", result)
    try:
        for row in plan["files"]:
            path = safe(Path(row["path"]))
            assert sha(path) == row["sha256"]
            path.unlink()
            print("REMOVED", path.name, flush=True)
            result["removed"].append(row)
            result["bytes_reclaimed_by_drive"][path.drive] += row["bytes"]
            save(REPORT / "result.json", result)
        for row in plan["retained"]:
            assert sha(Path(row["path"])) == row["sha256"]
        result["working_release_postflight"] = validate_current()
        remaining_refs = read(MAP)["files"]
        removed = {r["path"] for r in plan["files"]}
        dependency_cache = set()
        for row in remaining_refs:
            for key in ("file", "zip", "wem", "decoder"):
                if key in row["restore"]:
                    value = row["restore"][key]
                    if value not in dependency_cache:
                        p = Path(value).resolve()
                        assert p.is_file() and str(p) not in removed
                        dependency_cache.add(value)
        assert sha(MAP) == sha(migrated)
        result["removed_own_temporary_map_copy_bytes"] = migrated.stat().st_size
        safe(migrated).unlink()
        result.update(status="passed", bytes_before=plan["bytes_before"], bytes_after=0,
                      restore_references_migrated=plan["restore_references_migrated"],
                      preserved_sga_count=sum(Path(r["path"]).suffix == ".sga" for r in plan["retained"]),
                      loose_blender_and_voice_files_deleted=0, game_files_modified=False)
    finally:
        save(REPORT / "result.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "removed"}, indent=2), flush=True)


def document():
    result = read(REPORT / "result.json")
    assert result["status"] == "passed"
    plan = read(REPORT / "deletion-plan.json")
    rebuild = ROOT / "REBUILD_NEXT.md"
    previous = REPORT / "previous-rebuild-instructions.md"
    if not previous.exists():
        previous.write_bytes(rebuild.read_bytes())
    text = """# Building future Berber versions from working 0.8.1

## Retained working release

- Import ZIP: `output/berber_update_0_8_1/Berber-0.8.1.zip`.
  SHA-256: `a57bf7ce3beb8614cb8df2f4ee8349ca1d02e8adeb5d6909401c39667f6fb54c`.
- Authoritative current SGA: `output/berber_update_0_8_1/Berber_future_kingdom.sga`.
  SHA-256: `c58ef43ad4b0e664609161eb35178c97500837e9a844d7583fb014a50b7cc441`.
- Operator confirmed Spearman playback and the 0.8.1 Villager overlap fix.
  An exhaustive every-age/context/lifecycle/multiplayer matrix is separate.

`output` is a junction to
`F:/aoe_4_temp/Berber_future_kingdom_ai_20261014/output`. Keep F: connected.
The old delivery ZIPs are no longer rebuild inputs. Compressed source/rebuild
bundles, the voice backup and base SGAs are retained intentionally.

## Verify inputs before working

Run from the project root:

```powershell
& 'C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe' -B research/package_unified_release.py --check
```

The compatibility command `research/next_release.py --check` now delegates to
this same unified route. Its old imported two-package functions are historical
fixtures only; do not call those functions for new voice releases.

## Build the next version

1. Start from the retained working 0.8.1 SGA, not an older project cook/archive.
   Its archive includes the later handoff repairs and the complete voice work.
2. Edit the retained Blender/attribute/SCAR/audio inputs for the actual change.
   Cook or compose changed resources with the matching tools into an isolated
   candidate SGA. Preserve unrelated members, IDs, skins and gameplay. Read back
   and validate the candidate. Packaging does not cook edited source.
3. Package the already validated candidate:

```powershell
& 'C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe' -B research/package_unified_release.py --version 0.8.2 --summary 'Describe actual changes' --sga 'ABSOLUTE_PATH_TO_VALIDATED_CANDIDATE.sga'
```

This writes **one** `Berber-0.8.2.zip` and a validation report under
`output/berber_update_0_8_2`. It uses the retained 0.8.1 package metadata,
updates the manifest/version/SGA hash, and checks every output member/CRC.
It refuses an existing delivery. No separate voice ZIP/installer is generated.
For a metadata-only package, omit `--sga` to reuse the current 0.8.1 archive.
The same command shape works with a later three-part version. `--output` can
select an isolated packaging directory. No actual 0.8.2 content release was
created during cleanup; fixture tests verify packaging behavior only.

Import through normal Garrison, enable the mod, close/restart AoE4 and select
Malians plus the required Berber Game Mode and Tuning Pack. Keep 0.8.1 as rollback
until the new version is accepted. Follow AGENTS.md for verified release cleanup.

## Rebuild inputs that must stay

- `research/berber080`: editable dispatcher and voice bank, preparation recipe,
  accepted-recording receipt checks and Lua tests. Reuses 101 PCM clips for the
  added families; Villager is one take/action/shared ages, Tuareg has four age
  banks with shared efforts. Other 24 banks were preserved.
- `research/berber081`: attachment-speaker patch/regression/build recipe and
  **package-metadata.json**. That independent metadata replaces the old 0.8.0
  ZIP dependency. The 0.8.0 SGA remains its pre-patch source. Existing final paths
  are protected by collision checks; reproduce older recipes in an isolated
  output configuration, never by deleting the working release.
- `output/berber_update_0_8_0/Berber_future_kingdom.sga`: pre-attachment-fix base.
- `output/Berber-0.7.4-handoff.1-2026-10-17/`: authoritative handoff SGA, exact
  source-script snapshots, native/WEM catalog, provenance, and diagnostic tools.
  Its redundant download ZIP was removed only after all expanded members matched.
- 0.6.1 SGA and civilian selected-recording evidence, 0.6.0 candidate SGA, 0.5.1
  protected rollback SGA, and earlier art-chain/source SGAs recorded in the
  current cleanup plan. They remain because existing art/skin/voice recipes
  consume them. Do not remove an old SGA merely because its version is old.
- All Blender files/backups, models, textures, original voice masters, normalized
  WAVs, accepted encoded WEMs, private profiles, generation receipts, scripts,
  recipes, project configuration and compressed source/rebuild/tool bundles.
- `output/berber_update_0_7_3/Berber-0.7.3-VOICES-INSTALLER/`: expanded files are
  retained as voice/profile/rebuild sources. The redundant delivery ZIP was
  removed after full member hash comparison. This folder is an archival source,
  not a required installation for the current Garrison-only mod.
- `output/stock_audio_restore_20261017/nonstock-loose-audio-backup.zip`: preserved
  old Tuareg voice additions, not a current mod dependency. Do not reinstall it
  for normal Garrison playback.

## Do not reintroduce the Villager overlap

Preserve both parts: the 0.8.0 scripted/main speech-table changes and the 0.8.1
clearance of 208 attachment_speaker_code CStrings in the four custom Villager
age attachment lists. Main-field-only binding helpers miss those overrides.
The later 0.8.1 source/SGA is the proper future base. Gameplay, geometry, sex
variants and other units were not changed by the attachment correction.

## Cache restoration after cleanup

`research/restore_cleanup_cache.py` still restores only inventory-owned files and
verifies their hashes. Its map now reads the preserved expanded voice payloads
directly instead of opening the retired 0.7.3 voice ZIP. All referenced inputs
were checked before and after deletion; migration evidence is retained.

```powershell
& 'C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe' -B research/restore_cleanup_cache.py --root 'PHYSICAL_CACHE_DIRECTORY'
```

Current cleanup evidence is in `research/cleanup_081_20261017`: deletion plan,
retained base hashes, archive/member preservation proofs, restore-source ledger,
result and a snapshot of the superseded rebuild instructions. Historical reports
may mention deleted deliveries; use this document and the current entry point.
"""
    rebuild.write_text(text, encoding="utf-8")
    storage = ROOT / "STORAGE.md"
    note = ("Cleanup after accepted 0.8.1, 2026-10-17: removed " + str(len(result["removed"]))
            + " older delivery ZIPs, reclaiming " + str(result["bytes_reclaimed_by_drive"]["F:"])
            + " bytes on F: and 0 on E:. Selected obsolete-delivery bytes before/after: "
            + str(result["bytes_before"]) + "/0. Working 0.8.1 ZIP/SGA and "
            + str(result["preserved_sga_count"]) + " total required base/source SGAs remain hash-verified. "
            + str(result["restore_references_migrated"]) + " cache restore references now use fully hash-matching expanded voice/profile files instead of the retired 0.7.3 voice ZIP. All Blender/voice/model/texture files, receipts, recipes, compressed source/rebuild inputs and the old Tuareg voice backup were preserved; no game/Git files changed. No loose asset files were deleted. Recent 0.8.0/0.8.1 temporary build copies had already been removed at release verification, so this pass did not delete any further SGA. Future builds use research/package_unified_release.py (also reached by next_release.py CLI) from working 0.8.1 to produce one ZIP; 0.8.1 rebuilding uses independent package-metadata.json rather than the deleted 0.8.0 ZIP. See REBUILD_NEXT.md and research/cleanup_081_20261017/result.json. Older retention statements below are historical and superseded by this record.\n\n")
    original = storage.read_text(encoding="utf-8")
    if note not in original:
        storage.write_text(original.replace("# External storage\n", "# External storage\n\n" + note, 1), encoding="utf-8")
    print("Updated current rebuild and storage documentation", flush=True)


if __name__ == "__main__":
    {"prepare": prepare, "apply": apply, "document": document}[sys.argv[1]]()
