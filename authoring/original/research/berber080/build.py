"""Build one normal-Garrison 0.8.0 ZIP; never writes the game installation."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import shutil
import stat
import subprocess
import sys
import zipfile
from prepare import prepare, read, sha, OLD
from inspect_inputs import ROOT, SOURCE, OUT, HERE, ARCH, extract


def run(*args):
    result = subprocess.run([str(x) for x in args], check=True, capture_output=True, text=True, encoding="utf-8")
    return result.stdout


def main():
    target = OUT / "Berber-0.8.0.zip"
    final = OUT / "Berber_future_kingdom.sga"
    if target.exists() or final.exists():
        raise FileExistsError("Retain existing release; use a new output directory/version")
    proof = prepare()
    assert proof["base_sha256"] == "559f71581f91c1fee77a5eba81c0613496c080a7d262a8ef9f80bdba037a317f"
    test_results = {}
    for test in ("test_dispatcher.py", "test_recording_bank.py"):
        r = subprocess.run([sys.executable, "-B", str(HERE / test)], check=True, capture_output=True, text=True)
        test_results[test] = r.stderr
    base = Path(proof["base_sga"])
    baseline = json.loads(run(ARCH, "list", base, "--verify"))
    assert baseline["archive"]["verification"]["verified"]
    old = {(m["toc"], m["path"]): m for m in baseline["members"]}
    payloads = read(OUT / "payload-files.json")
    # Verify the handoff's supplied source snapshots match its actual archive.
    for script in ("berber_scripted_speech.scar", "berber_voice_bank.scar"):
        assert sha(extract("scar/" + script)) == sha(SOURCE / "mod-source/scar" / script)
    stage = OUT / "attrib-stage.sga"
    assert not stage.exists()
    expected = {}
    current = base
    for alias in ("attrib", "data"):
        selected = {member: path for member, path in payloads.items() if (member.startswith("attrib/")) == (alias == "attrib")}
        listing = OUT / (alias + "-set-members.txt")
        listing.write_text("".join(member + "=" + path + "\n" for member, path in selected.items()), encoding="utf-8")
        expected.update({(alias, member): sha(Path(path)) for member, path in selected.items()})
        destination = stage if alias == "attrib" else final
        run(ARCH, "set-members", current, listing, destination, "--alias", alias)
        current = destination
        print("Archive composed:", alias, flush=True)
    candidate = json.loads(run(ARCH, "list", final, "--verify"))
    assert candidate["archive"]["verification"]["verified"]
    new = {(m["toc"], m["path"]): m for m in candidate["members"]}
    assert set(new) == set(old) | set(expected)
    for key, member in old.items():
        if key not in expected:
            assert (member["crc"], member["size"]) == (new[key]["crc"], new[key]["size"]), key
    # Read back every added/changed member once, then hash the decoded bytes.
    readback = OUT / "readback"
    args = [ARCH, "extract", final, readback]
    for _, member in expected:
        args.extend(("--member", member))
    run(*args)
    for (_, member), digest in expected.items():
        assert sha(readback / member) == digest, member
    bank_paths = set(__import__("re").findall(r'"(audio/voices/[0-9a-f]+\.wav)"', (HERE / "berber_voice_bank.scar").read_text(encoding="utf-8")))
    assert all(("data", path) in new for path in bank_paths)
    assert not proof["unavailable_contexts"]
    manifest = read(SOURCE / "garrison.json")
    manifest["members"][0].update(path=final.name, sha256=sha(final))
    manifest["details"].update(version="0.8.0", min_garrison="0.1.6", updated="2026-10-17",
        summary="Villager and Tuareg voices enabled through normal Garrison audio; no voice installer",
        description="Single-package Berber release using normal Garrison scripted voice playback for all 26 families. Adds retained Villager and Tuareg recordings, with one Villager take per action across ages and four Tuareg age banks. No separate voice installation, bundled runtime or START-TEST required. Select Malians, Berber Game Mode and Tuning Pack. Audible overlap qualification remains pending.",
        changelog="Adds 101 retained PCM recordings for Villager/Tuareg and removes their scripted exclusions and unsupported native-speech API calls. Removes only their 11 native speech tables, matching the other working families. Preserves all unrelated handoff archive content. No new generation or game-file installation.")
    coverage = {
        "version": "0.8.0", "route": "Garrison.audio scripted local-player playback",
        "families_enabled": 26, "added_unique_recordings": len(proof["unique_pcm_payloads"]),
        "added_source_pcm_bytes": sum(x["bytes"] for x in proof["unique_pcm_payloads"]),
        "villager": {"actions": 14, "takes_per_action": 1, "all_ages_shared": True},
        "tuareg": {"actions_per_age": 11, "ages": [1, 2, 3, 4], "frequent_takes_cap": 3, "effort_takes_cap": 2},
        "existing_other_families_unchanged": True, "paid_requests": 0,
        "added_actions": {family: sorted({row["action"] for row in proof["recordings"] if row["family"] == family}) for family in ("villager", "tuareg")},
        "runtime_test": "pending operator; static/Lua/archive verification is not audible acceptance",
    }
    instructions = """BERBER 0.8.0 - NORMAL GARRISON VOICES

Close AoE IV. Import Berber-0.8.0.zip into your normal Garrison client (0.1.6),
enable The Berber Dynasties, then use Garrison's normal Play button.
In the lobby select Malians, Berber Game Mode AND Berber Tuning Pack.

No START-TEST launcher, experimental runtime or separate voice installer.
Do not copy anything into the Steam game folder. The previous loose audio
installation is unnecessary. Keep other Berber versions disabled.

Villager and Tuareg Spearman now use the same scripted playback route as the
other units you tested in 0.7.5. Their previously recorded voices are included.
Villager: one take per action across all ages. Tuareg: existing dialogue for
each age tier; up to three takes, with shared nonverbal efforts.
Group arbitration and cooldown behavior are retained. No paid generation.
The other families, landmarks, geometry and gameplay are unchanged from the
0.7.5/0.7.4 handoff archive.

TEST FIRST: select a Villager and a Tuareg individually; move, attack and stop
with three seconds between actions. Test gathering/building with the Villager.
Then check groups, age upgrades, damage/death and a second match.
Report custom voice, original voice overlap, or silence separately.
This build removes their native speech tables to match the working families;
absence of native overlap requires your listening test and is not guaranteed
by a static check. Earlier 0.7.1 attempts failed this test; stock audio has since
been restored and this build uses the newer working dispatcher/bindings.

READ VOICE_GAPS.md for limitations. No runtime/audible pass is claimed yet.
To roll back: close AoE IV and reimport the preserved 0.7.5-fixed ZIP.
"""
    gaps = """# Voice qualification gaps

- Villager/Tuareg playback and absence of original-voice overlap are pending an
  operator test. Speech-table removal matches the other user-tested families;
  earlier two-unit pilots did not prove reliable suppression for these units.
- This is scripted Garrison playback, not native PostEvent substitution. The
  dispatcher does not call the unsupported native_speech API. The handoff's
  native declaration/WEM inventory remain unchanged as inactive archive data.
- Villager uses one normal-delivery take per supported action across all ages.
  Tuareg dialogue follows its age-tier squad blueprint; an unknown name falls
  back to its Age I bank. Efforts share their age-independent recordings.
- Movement uses recorded movegc lines; attack-move uses the same attack lines,
  matching the existing adapter's semantics. Delivery/stealth variants are not
  automatically selected by this adapter.
- Selection and supported explicit commands/work state transitions, pain and
  death are implemented. Unobservable native contexts are not substituted by
  random ambient playback. Repeated/default/queued orders still inherit the
  existing command-callback and polling limitations; cooldowns may suppress cues.
- Other 24 scripted families are unchanged. Navy, siege, King, group/age/lifecycle
  coverage, disabled-mod isolation and multiplayer have not been newly qualified.
- Handed-off art limitations (22 invalid-UV model files) are retained, not repaired.
"""
    entries = {
        "garrison.json": (json.dumps(manifest, indent=2) + "\n").encode(),
        "START-HERE.txt": instructions.encode(),
        "VOICE_GAPS.md": gaps.encode(),
        "VOICE_COVERAGE.json": (json.dumps(coverage, indent=2) + "\n").encode(),
    }
    with zipfile.ZipFile(target, "x", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.write(final, final.name)
        for name, data in entries.items():
            z.writestr(name, data)
    expected_zip = {**{name: hashlib.sha256(data).hexdigest() for name, data in entries.items()}, final.name: sha(final)}
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None and set(z.namelist()) == set(expected_zip)
        assert sum(Path(n).name.lower() == "garrison.json" for n in z.namelist()) == 1
        for name, digest in expected_zip.items():
            with z.open(name) as f:
                assert hashlib.file_digest(f, "sha256").hexdigest() == digest
    report = {"version": "0.8.0", "status": "package_verified_awaiting_operator",
              "zip": str(target), "zip_bytes": target.stat().st_size, "zip_sha256": sha(target),
              "sga": str(final), "sga_bytes": final.stat().st_size, "sga_sha256": sha(final),
              "base_sga_sha256": proof["base_sha256"], "zip_members": expected_zip,
              "archive_verification": candidate["archive"]["verification"],
              "changed_member_count": len(expected), "changed_members_sha256": {p: h for (_, p), h in expected.items()},
              "all_other_members_crc_size_unchanged": True,
              "added_audio_sha256_readback": "passed", "coverage": coverage,
              "tests": test_results, "scar_check": read(HERE / "scar-code-check.json"),
              "scar_check_unknowns_explained": "family/speak/track are local; forMod/play/pulse/session are existing Garrison.audio API; unit_spearman_tuareg_ is a regex string false positive",
              "speech_only_rgd_semantic_undo": "passed for all 11 modified blueprints",
              "game_files_modified": False, "actual_import": "pending", "audible": "pending"}
    (OUT / "release-validation.json").write_text(json.dumps(report, indent=2) + "\n")
    (OUT / "SHA256SUMS.txt").write_text(report["zip_sha256"] + "  " + target.name + "\n" + report["sga_sha256"] + "  " + final.name + "\n")
    finalize_cleanup(report, target, final)


def finalize_cleanup(report, target, final):
    assert sha(target) == report["zip_sha256"] and sha(final) == report["sga_sha256"]
    # Required release cleanup: only inventoried regenerable copies inside this
    # physical release folder. Sources/recipes and final SGA/ZIP stay retained.
    disposable = [OUT / name for name in ("inspection", "payloads", "readback", "attrib-stage.sga")]
    inventory = []
    for item in disposable:
        assert item.resolve().is_relative_to(OUT.resolve()) and item.exists()
        paths = [item] if item.is_file() else list(item.rglob("*"))
        for path in paths:
            assert not path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
            if path.is_file():
                inventory.append({"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path),
                                  "regeneration": "prepare.py from retained handoff/receipts; archiver set-members/extract; no unique input"})
    reclaimed = sum(x["bytes"] for x in inventory)
    cleanup = {"inventory": inventory, "bytes_before": reclaimed, "bytes_after": 0,
               "reclaimed_E_bytes": 0, "reclaimed_F_bytes": reclaimed,
               "retained_inputs": [str(SOURCE), str(HERE), str(OLD), str(ROOT / "art/voices_0_6_0")],
               "status": "planned"}
    (OUT / "cleanup-report.json").write_text(json.dumps(cleanup, indent=2) + "\n")
    for item in disposable:
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    assert sha(target) == report["zip_sha256"] and sha(final) == report["sga_sha256"]
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
    cleanup["status"] = "completed_delivery_reverified"
    (OUT / "cleanup-report.json").write_text(json.dumps(cleanup, indent=2) + "\n")
    report["cleanup"] = {k: v for k, v in cleanup.items() if k != "inventory"}
    (OUT / "release-validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("status", "zip", "zip_bytes", "zip_sha256", "sga_sha256")}, indent=2), flush=True)
    print("Reclaimed temporary bytes:", reclaimed, flush=True)


if __name__ == "__main__":
    if "--finish-cleanup" in sys.argv:
        report = read(OUT / "release-validation.json")
        finalize_cleanup(report, Path(report["zip"]), Path(report["sga"]))
    else:
        main()
