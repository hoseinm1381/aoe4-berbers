"""Villager attachment-speaker fix only. No audio generation or game writes."""
from pathlib import Path
import copy
import hashlib
import json
import shutil
import stat
import subprocess
import sys
import zipfile
from investigate import ROOT, BASE, OUT, ARCH, extract, rgd
from test_speaker_overrides import MEMBERS

sys.path.insert(0, str(ROOT / "research/berber060"))
from bindings import encode, semantic

HERE = Path(__file__).parent


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def tool(*args):
    return subprocess.run([str(a) for a in args], capture_output=True, check=True, text=True, encoding="utf-8").stdout


def main():
    OUT.mkdir(exist_ok=True)
    final = OUT / "Berber_future_kingdom.sga"
    target = OUT / "Berber-0.8.1.zip"
    assert not final.exists() and not target.exists(), "Preserve existing release"
    assert sha(BASE) == "7d86a7ed79c6dcfd79dba6d69b9b4a68f6f77e2737b2989f5475cf2db866c379"
    # These controls have the same empty-speaker field representation and were
    # voiced successfully by the operator. This is a layout analogue, not a
    # replacement for the required Villager audible check.
    controls = ["attrib/attachments/attachment_lists/garrison/berber_units_050/bind_scout_a1_tier1_cavalry_scout_mal.rgd",
                "attrib/attachments/attachment_lists/garrison/berber_units_050/bind_archer_a2_tier2_archer_mal.rgd"]
    for member in controls:
        values = [n.value for _, n in rgd.flatten(rgd.read(extract(member).read_bytes()).nodes) if n.key == "attachment_speaker_code"]
        assert values and all(v == "" for v in values)
    changes, payloads = [], {}
    for member in MEMBERS:
        data = extract(member).read_bytes()
        original = rgd.read(data)
        doc = copy.deepcopy(original)
        fields = []
        for path, node in rgd.flatten(doc.nodes):
            if node.key == "attachment_speaker_code":
                assert node.kind == "CString" and node.value in ("villagerMale", "villagerFemale")
                fields.append({"path": path, "before": node.value, "after": ""})
                node.value = ""
        assert len(fields) == 52
        payload = encode(doc)
        restored = copy.deepcopy(rgd.read(payload))
        indexed = dict(rgd.flatten(restored.nodes))
        for field in fields:
            assert indexed[field["path"]].value == ""
            indexed[field["path"]].value = field["before"]
        assert semantic(restored.nodes) == semantic(original.nodes), "Non-speaker change"
        path = OUT / "payloads" / member
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        payloads[member] = path
        changes.append({"member": member, "source_sha256": hashlib.sha256(data).hexdigest(),
                        "sha256": sha(path), "fields": fields, "semantic_undo": "passed"})
    (OUT / "attachment-speaker-changes.json").write_text(json.dumps(changes, indent=2) + "\n")
    test = subprocess.run([sys.executable, "-B", str(HERE / "test_speaker_overrides.py")], check=True, capture_output=True, text=True)
    baseline = json.loads(tool(ARCH, "list", BASE, "--verify"))
    assert baseline["archive"]["verification"]["verified"]
    listing = OUT / "attrib-set-members.txt"
    listing.write_text("".join(member + "=" + str(path) + "\n" for member, path in payloads.items()), encoding="utf-8")
    tool(ARCH, "set-members", BASE, listing, final, "--alias", "attrib")
    checked = json.loads(tool(ARCH, "list", final, "--verify"))
    assert checked["archive"]["verification"]["verified"]
    before = {(r["toc"], r["path"]): (r["size"], r["crc"]) for r in baseline["members"]}
    after = {(r["toc"], r["path"]): (r["size"], r["crc"]) for r in checked["members"]}
    assert set(before) == set(after)
    assert {name for (toc, name), value in after.items() if before[(toc, name)] != value} == set(MEMBERS)
    readback = OUT / "readback"
    args = [ARCH, "extract", final, readback]
    for member in MEMBERS:
        args.extend(("--member", member))
    tool(*args)
    for member, path in payloads.items():
        assert sha(readback / member) == sha(path)
    # Independent editable metadata replaces the retired 0.8.0 ZIP dependency.
    # The retained 0.8.0 SGA is still the authoritative pre-patch binary input.
    metadata = json.loads((HERE / "package-metadata.json").read_text(encoding="utf-8"))
    manifest, coverage = metadata["manifest"], metadata["coverage"]
    manifest["members"][0]["sha256"] = sha(final)
    manifest["details"].update(version="0.8.1",
        summary="Villager overlap fix candidate: clears native male/female attachment speaker overrides",
        description="Normal Garrison import/Play. Clears 208 stock Villager speaker overrides across four age attachment lists; custom scripted voices retained. Spearman, all audio, scripts, visuals and gameplay unchanged from 0.8.0. No extra runtime or voice installer. Villager listening acceptance pending.",
        changelog="Clears only attachment_speaker_code fields in four custom Villager age-tier attachment lists. Their 104 villagerMale and 104 villagerFemale assignments were a native speech route left active after 0.8.0 removed main speech tables. Uses the empty-speaker layout of working Scout/Archer attachments. Four typed semantic-undo/readback checks passed; audible overlap check pending.")
    coverage.update(version="0.8.1", cleared_villager_native_attachment_speaker_fields=208,
                    operator_feedback_080="Spearman works great; Villager custom/original overlap",
                    runtime_test="0.8.1 Villager audible overlap pending; all other audio/scripts unchanged")
    instructions = """BERBER 0.8.1 - VILLAGER VOICE OVERLAP FIX CANDIDATE

Exit AoE IV completely. Import Berber-0.8.1.zip into normal Garrison, enable it,
then launch using Garrison Play. Select Malians + Berber Game Mode + Tuning Pack.
No START-TEST, voice installer or game-folder copying.

The Villager's age attachment lists still explicitly assigned original male and
female speakers in 0.8.0. This build clears only those 208 assignments, matching
the empty speaker override used by the working Scout/Archer attachments.
The existing custom Villager recordings and dispatcher are unchanged.
Spearman and every other unit, voice recording, script, model and gameplay value
are unchanged. No global Speech/Master setting is altered.

Test several new male and female Villagers: selection, movement, gathering,
building, stop and age upgrades. Listen for any original voice alongside custom
speech. Also check the previously working Spearman. Report the listening result;
static checks alone cannot confirm that the overlap has stopped.

For future releases keep the working Berber-0.8.1.zip as rollback. Older delivery
ZIPs can be retired after their rebuild dependencies are redirected.
"""
    gaps = """# Voice gaps / acceptance

Villager overlap in 0.8.0 was confirmed by the operator. Its four active tier
attachment lists contained 208 explicit stock male/female speaker overrides.
0.8.1 clears those CString values, preserving every other typed property.
This targets the newly discovered native path, but audible acceptance is pending.

All source recordings, scripted dispatch limitations, supported contexts and
age banks remain those of 0.8.0. Spearman was reported working well in 0.8.0;
its archive members are unchanged here. No alternate native runtime is required.
Multiplayer, complete age/context/lifecycle behavior and the handoff's preexisting
22 invalid-UV model members remain unqualified or unresolved as documented before.
"""
    files = {"garrison.json": (json.dumps(manifest, indent=2) + "\n").encode(),
             "START-HERE.txt": instructions.encode(), "VOICE_GAPS.md": gaps.encode(),
             "VOICE_COVERAGE.json": (json.dumps(coverage, indent=2) + "\n").encode()}
    with zipfile.ZipFile(target, "x", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.write(final, final.name)
        for name, data in files.items():
            z.writestr(name, data)
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    hashes[final.name] = sha(final)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None and set(z.namelist()) == set(hashes)
        assert sum(Path(p).name.lower() == "garrison.json" for p in z.namelist()) == 1
        for name, digest in hashes.items():
            with z.open(name) as f:
                assert hashlib.file_digest(f, "sha256").hexdigest() == digest
    report = {"status": "package_verified_audible_overlap_test_pending", "version": "0.8.1",
              "zip": str(target), "zip_bytes": target.stat().st_size, "zip_sha256": sha(target),
              "sga": str(final), "sga_sha256": sha(final), "base_sha256": sha(BASE),
              "modified_members": MEMBERS, "modified_speaker_fields": 208, "male_fields": 104, "female_fields": 104,
              "all_other_archive_members_crc_size_unchanged": True,
              "speech_only_semantic_undo": "passed", "payload_readback_sha256": "passed",
              "zip_members": hashes, "zip_integrity": "passed", "exactly_one_garrison_manifest": True,
              "archive_verification": checked["archive"]["verification"], "regression_test": test.stderr,
              "working_empty_override_controls": controls, "game_files_modified": False,
              "actual_import": "pending", "audible_villager_overlap": "pending"}
    (OUT / "release-validation.json").write_text(json.dumps(report, indent=2) + "\n")
    (OUT / "SHA256SUMS.txt").write_text(report["zip_sha256"] + "  " + target.name + "\n" + report["sga_sha256"] + "  " + final.name + "\n")
    temporary = [OUT / n for n in ("investigation", "payloads", "readback")]
    inventory = []
    for folder in temporary:
        assert folder.resolve().is_relative_to(OUT.resolve()) and not folder.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        for path in folder.rglob("*"):
            assert not path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
            if path.is_file():
                inventory.append({"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path),
                                  "regenerate": "extract from retained 0.8.0 SGA; apply build.py or extract candidate"})
    cleanup = {"inventory": inventory, "bytes_before": sum(p["bytes"] for p in inventory), "bytes_after": 0,
               "retained": "Final SGA/ZIP, source 0.8.0 SGA/ZIP, editable scripts and compact evidence", "status": "planned"}
    (OUT / "cleanup-report.json").write_text(json.dumps(cleanup, indent=2) + "\n")
    for folder in temporary:
        shutil.rmtree(folder)
    assert sha(target) == report["zip_sha256"] and sha(final) == report["sga_sha256"]
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
    cleanup["status"] = "completed_delivery_reverified"
    (OUT / "cleanup-report.json").write_text(json.dumps(cleanup, indent=2) + "\n")
    report["cleanup"] = {"reclaimed_E_bytes": 0, "reclaimed_F_bytes": cleanup["bytes_before"], "post_cleanup_hash_crc": "passed"}
    (OUT / "release-validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("status", "zip", "zip_bytes", "zip_sha256", "sga_sha256", "cleanup")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
