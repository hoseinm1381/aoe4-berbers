"""Package the verified 0.7.4 development handoff as a reproducible 0.7.5 test.

No cook, paid generation, native file installation, or gameplay changes.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

SOURCE = Path(r"F:\aoe_4_temp\Berber_future_kingdom_ai_20261014\output\Berber-0.7.4-handoff.1-2026-10-17")
OUT = SOURCE.parent / "berber_update_0_7_5"
ARCHIVER = Path(r"C:\Users\RS\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\raw_githubusercontent_com\garrison\bin\sga-archiver.exe")


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def main():
    OUT.mkdir(exist_ok=True)
    delivery = OUT / "Berber-0.7.5-fixed.zip"
    if delivery.exists():
        raise FileExistsError(delivery)
    source_hashes = {}
    for row in (SOURCE / "SHA256SUMS.txt").read_text().splitlines():
        expected, name = row.split("  ", 1)
        path = (SOURCE / name).resolve(strict=True)
        assert path.is_relative_to(SOURCE.resolve()), name
        assert sha(path) == expected, name
        source_hashes[name] = expected
    manifest = json.loads((SOURCE / "garrison.json").read_text())
    archive = SOURCE / manifest["members"][0]["path"]
    assert sha(archive) == manifest["members"][0]["sha256"]
    inspected = json.loads(subprocess.run(
        [str(ARCHIVER), "list", str(archive), "--verify"],
        check=True, capture_output=True, text=True).stdout)
    assert inspected["archive"]["verification"]["verified"]
    members = {m["path"].replace("\\", "/"): m for m in inspected["members"]}
    wem = [m for p, m in members.items() if m["toc"] == "data" and p.startswith("garrison/speech/") and p.endswith(".wem")]
    assert len(wem) == 5664, len(wem)
    assert sum(m["size"] for m in wem) == 70127632
    assert members["garrison/runtime/native-speech.json"]["toc"] == "data"
    assert members["garrison/author-audio/catalog.json"]["toc"] == "data"
    assert "audio" not in {x["alias"] for x in inspected["archive"]["tocs"]}
    details = manifest["details"]
    details.update(version="0.7.5", updated="2026-10-17",
        summary="In-game test: embedded voices and experimental native Villager/Tuareg speech replacement",
        description="0.7.5 test package of the verified 0.7.4-handoff.1 archive. Requires the included paired development runtime. Villager/Tuareg use experimental native replacement; other families retain scripted WAV playback. Intermittent stock replies remain unresolved. Not an official Garrison release. Extract and run START-TEST.cmd; select Malians, Berber Game Mode and Tuning Pack.",
        changelog="Packages the handoff's existing sound integration, complete 5664-WEM bank and paired runtime for testing. Adds a click-to-start launcher and test instructions. SGA, speech mapping, gameplay and models are byte-identical to the handoff. No new listening acceptance or fixes to intermittent stock replies are claimed.")
    readme = """BERBER 0.7.5 - SOUND INTEGRATION TEST

1. Extract this entire ZIP into an ordinary folder. Do not run inside the ZIP.
2. Close AoE IV. Keep Steam open and signed in. Close the normal Garrison client.
3. Double-click START-TEST.cmd. It uses the INCLUDED matching development runtime,
   imports/enables this package, checks readiness, and launches through Steam.
   Review the displayed mod list. Disable incompatible mods using your client
   before starting this test. Do not mix different Berber versions.
4. In the lobby select MALIANS, BERBER GAME MODE and BERBER TUNING PACK.
   Use an ordinary map. Both Berber components must be selected.
5. After exiting AoE IV, run CLEANUP-TEST.cmd to end its owned staging session.

No separate voice installation is required for this integration. Existing loose
voice installations are left untouched; report that they are installed when
reporting results. Do not run the old voice installer for this test.

IMPORTANT: The ordinary Garrison client does not qualify this experimental
feature. The paired CLI/agent/backend in test-runtime are required. They target
AoE IV 16.3.11308, Steam build 24231237. Keep all binary identity gates enabled.
The runtime labels itself 0.1.0 internally; this does NOT mean public Garrison
0.1.0 supports the feature. This is not an official Garrison 0.1.6 release.

WHAT TO TEST
Villager (male/female) and Tuareg: select, move, stop, attack, gather/build where
applicable, combat, hurt/death. Leave three seconds between initial actions,
then test groups and rapid orders. Note custom replies, stock replies, overlap
or silence separately. Check ages, Speech/Master volume zero and restore,
pause/resume, menu return and a second match. Scout and other families use the
older scripted route and cannot prove native replacement works.

KNOWN LIMITS
Native Villager/Tuareg replacement remains incomplete: intermittent stock-
sounding replies were reported in the handoff. 4543 rules map to 398 author
recordings. All 5664 original WEM clips are packaged, but packaging does not
activate native replacement for the other families. They retain 1050 WAVs.
Native mapping follows stock source filenames, not individual unit identities;
units sharing those sources can share replacements. Multiplayer is unqualified.
The handoff also retains 22 model files with invalid UVs; no art fixes here.

WHAT CHANGED IN 0.7.5
Release metadata, this launcher and instructions only. The SGA and diagnostic
binaries are unchanged from 0.7.4-handoff.1. Original handoff documents, traces,
source scripts and provenance are included. No paid audio generation.

ROLLBACK
Close AoE IV, run CLEANUP-TEST.cmd, then reimport the preserved 0.7.3 main ZIP
using the normal client. Earlier installed native voices are not removed here.
Nothing in this package should be copied into the Steam game directory.
"""
    launcher = r'''@echo off
setlocal
cd /d "%~dp0"
title Berber 0.7.5 - Sound Integration Test
tasklist /FI "IMAGENAME eq RelicCardinal.exe" /NH 2>nul | findstr /I "RelicCardinal.exe" >nul
if not errorlevel 1 (
  echo Close Age of Empires IV before starting this test.
  pause
  exit /b 1
)
echo Berber 0.7.5 - paired development runtime, not an official Garrison release.
echo Close the normal Garrison client. Steam must be signed in.
echo No separate voice installation is needed. Existing voices are left alone.
echo.
"%~dp0test-runtime\garrison-play.exe" status
if errorlevel 1 goto failed
"%~dp0test-runtime\garrison-play.exe" list
if errorlevel 1 goto failed
echo.
echo Review the enabled mods above. Close this window to cancel if incompatible
echo mods are enabled; disable those in Garrison before trying again.
pause
"%~dp0test-runtime\garrison-play.exe" install "%~dp0garrison.json"
if errorlevel 1 goto failed
"%~dp0test-runtime\garrison-play.exe" enable berber_future_kingdom
if errorlevel 1 goto failed
"%~dp0test-runtime\garrison-play.exe" doctor
if errorlevel 1 goto failed
"%~dp0test-runtime\garrison-play.exe" launch
if errorlevel 1 goto failed
echo.
echo In the lobby: Malians + Berber Game Mode + Berber Tuning Pack.
echo After exiting the game, run CLEANUP-TEST.cmd.
pause
exit /b 0
:failed
echo.
echo The test stopped because a command failed. Keep the error above for review.
echo Do not bypass build or readiness gates.
pause
exit /b 1
'''
    cleanup = r'''@echo off
setlocal
cd /d "%~dp0"
echo Close Age of Empires IV before continuing.
"%~dp0test-runtime\garrison-play.exe" cleanup
if errorlevel 1 (
  echo Cleanup did not finish. Read the error above; do not delete game folders.
  pause
  exit /b 1
)
echo Owned test-session staging cleanup completed. Voice installations left alone.
pause
'''
    def encoded(text):
        return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")
    status = json.loads((SOURCE / "STATUS.json").read_text())
    status.update(version="0.7.5", state="packaged_for_operator_test",
                  source_handoff="0.7.4-handoff.1", source_sga_unchanged=True,
                  playback_work_paused=False,
                  final_archive_acceptance="Pending operator in-game check for 0.7.5; packaging checks are separate")
    additions = {
        "garrison.json": (json.dumps(manifest, indent=2) + "\n").encode(),
        "STATUS.json": (json.dumps(status, indent=2) + "\n").encode(),
        "START-HERE.txt": encoded(readme),
        "START-TEST.cmd": encoded(launcher),
        "CLEANUP-TEST.cmd": encoded(cleanup),
        "START-HERE-EN.txt": encoded(readme),
        "START-HERE-RU.txt": encoded("For current 0.7.5 instructions read START-HERE.txt. Original handoff instructions: documentation/handoff/START-HERE-RU.txt.\n"),
        "CHANGELOG-EN.txt": encoded("0.7.5 - Operator sound integration test, 2026-10-17\n\n" + details["changelog"] + "\n\nOriginal handoff changelog: documentation/handoff/CHANGELOG-EN.txt.\n"),
    }
    paths = {}
    for path in SOURCE.rglob("*"):
        if path.is_symlink():
            raise RuntimeError(f"Unexpected symlink: {path}")
        if path.is_file():
            name = path.relative_to(SOURCE).as_posix()
            if name in additions or name == "SHA256SUMS.txt":
                if name != "SHA256SUMS.txt":
                    reference_name = name + ".txt" if name.lower() == "garrison.json" else name
                    paths["documentation/handoff/" + reference_name] = path
            else:
                paths[name] = path
    hashes = {name: sha(path) for name, path in paths.items()}
    hashes.update({name: hashlib.sha256(data).hexdigest() for name, data in additions.items()})
    assert [n for n in hashes if Path(n).name.lower() == "garrison.json"] == ["garrison.json"]
    additions["SHA256SUMS.txt"] = "".join(f"{value}  {name}\n" for name, value in sorted(hashes.items())).encode()
    with zipfile.ZipFile(delivery, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as z:
        for name, path in sorted(paths.items()):
            z.write(path, name)
        for name, data in sorted(additions.items()):
            z.writestr(name, data)
    # Hash every ZIP member, including the packaged SGA. No extracted payload copies.
    with zipfile.ZipFile(delivery) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(set(z.namelist()))
        assert [n for n in z.namelist() if Path(n).name.lower() == "garrison.json"] == ["garrison.json"]
        for name, expected in hashes.items():
            with z.open(name) as f:
                assert hashlib.file_digest(f, "sha256").hexdigest() == expected, name
        assert json.loads(z.read("garrison.json"))["details"]["version"] == "0.7.5"
    report = {
        "version": "0.7.5", "status": "package_verified_runtime_pending",
        "zip": str(delivery), "zip_bytes": delivery.stat().st_size, "zip_sha256": sha(delivery),
        "source_sga": str(archive), "sga_sha256": sha(archive),
        "source_handoff_checked_files": len(source_hashes), "zip_members": len(hashes) + 1,
        "all_packaged_member_hashes_verified": True, "exactly_one_garrison_manifest": True,
        "packaging_fix": "Rename archived reference manifest to documentation/handoff/garrison.json.txt; SGA/runtime unchanged",
        "archive_verification": inspected["archive"]["verification"],
        "wem_clips": len(wem), "wem_bytes": sum(m["size"] for m in wem),
        "sga_runtime_and_mapping_unchanged": True,
        "launcher_execution": "not_run_to_preserve_user_library_and_game_session",
        "audible_gameplay": "pending_operator", "actual_client_import": "pending_operator",
        "cleanup": {"staging_created_bytes": 0, "reclaimed_E_bytes": 0, "reclaimed_F_bytes": 0,
                    "retained": "Delivery ZIP, compact report, build recipe and source handoff; no staging/readback copies created"},
        "member_sha256": hashes,
    }
    (OUT / "release-validation.json").write_text(json.dumps(report, indent=2) + "\n")
    (OUT / "SHA256SUMS.txt").write_text(report["zip_sha256"] + "  " + delivery.name + "\n")
    # Post-cleanup gate (there are no disposable copies to remove).
    assert sha(delivery) == report["zip_sha256"]
    with zipfile.ZipFile(delivery) as z:
        assert z.testzip() is None
    print(json.dumps({k: report[k] for k in ("status", "zip", "zip_bytes", "zip_sha256", "sga_sha256", "wem_clips")}, indent=2))


if __name__ == "__main__":
    main()
