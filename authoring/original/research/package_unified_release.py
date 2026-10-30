"""Package future unified releases from working 0.8.1, without older ZIPs.

This packages an already validated SGA; it does not cook assets or change audio.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).absolute().parents[1]
SOURCE = ROOT / "output/berber_update_0_8_1"
SGA = SOURCE / "Berber_future_kingdom.sga"
ZIP_NAME = "Berber-0.8.1.zip"
ZIP_SHA = "a57bf7ce3beb8614cb8df2f4ee8349ca1d02e8adeb5d6909401c39667f6fb54c"
SGA_SHA = "c58ef43ad4b0e664609161eb35178c97500837e9a844d7583fb014a50b7cc441"


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def check():
    source = SOURCE / ZIP_NAME
    if sha(source) != ZIP_SHA or sha(SGA) != SGA_SHA:
        raise ValueError("Working 0.8.1 input changed")
    expected = json.loads((SOURCE / "release-validation.json").read_text(encoding="utf-8"))["zip_members"]
    with zipfile.ZipFile(source) as z:
        if z.testzip() is not None or set(z.namelist()) != set(expected):
            raise ValueError("Retained ZIP members/CRC changed")
        if sum(Path(n).name.lower() == "garrison.json" for n in z.namelist()) != 1:
            raise ValueError("Exactly one manifest required")
        for name, value in expected.items():
            with z.open(name) as f:
                if hashlib.file_digest(f, "sha256").hexdigest() != value:
                    raise ValueError("Retained member hash changed: " + name)
    return {"status": "passed", "retained_package": str(source), "base_sga": str(SGA),
            "base_sga_sha256": SGA_SHA, "dependencies": "Working 0.8.1 ZIP + SGA + compact report only; no older delivery ZIPs"}


def build(version, summary, sga=SGA, output=None):
    if not re.fullmatch(r"\d+\.\d+\.\d+", version) or version == "0.8.1":
        raise ValueError("Use a new three-part version")
    if not summary.strip() or len(summary) > 180:
        raise ValueError("Summary must be 1-180 characters")
    sga = Path(sga).absolute()
    if not sga.is_file() or sga.suffix.lower() != ".sga":
        raise ValueError("Supply an already validated SGA")
    destination = Path(output) if output else ROOT / "output" / ("berber_update_" + version.replace(".", "_"))
    target = destination / ("Berber-" + version + ".zip")
    if target.exists():
        raise FileExistsError("Existing delivery preserved")
    check()
    with zipfile.ZipFile(SOURCE / ZIP_NAME) as old:
        if sum(Path(n).name.lower() == "garrison.json" for n in old.namelist()) != 1:
            raise ValueError("Source contains more than one manifest")
        manifest = json.loads(old.read("garrison.json"))
        coverage = json.loads(old.read("VOICE_COVERAGE.json"))
        gaps = old.read("VOICE_GAPS.md")
    digest = sha(sga)
    manifest["members"][0].update(path="Berber_future_kingdom.sga", sha256=digest)
    manifest["details"].update(version=version, summary=summary, updated=str(datetime.date.today()),
                               changelog=summary,
                               description=summary + " Normal Garrison import/Play; no separate voice installer. See START-HERE and coverage. Runtime acceptance pending for this version.")
    coverage.update(version=version, runtime_test="Pending for this new package; 0.8.1 baseline Villager overlap fix was operator-confirmed")
    instructions = f"""BERBER {version}

{summary}

Close AoE IV. Import Berber-{version}.zip in normal Garrison, enable it and use
Garrison Play. Select Malians + Berber Game Mode + Berber Tuning Pack.
No voice installation or alternate launcher. Start a fresh game process.

This package contains the supplied validated SGA. Packaging does not cook source
changes or establish in-game acceptance. Test the new content and voices.
The baseline 0.8.1 Villager attachment-speaker correction must be preserved when
authoring new archives. Keep the working 0.8.1 ZIP for rollback.
"""
    files = {"garrison.json": (json.dumps(manifest, indent=2) + "\n").encode(),
             "VOICE_COVERAGE.json": (json.dumps(coverage, indent=2) + "\n").encode(),
             "VOICE_GAPS.md": b"# Baseline voice limitations\n\nThe following records 0.8.1 baseline scope. The reported Villager overlap was subsequently operator-confirmed resolved; full matrix coverage remains separate.\n\n" + gaps,
             "START-HERE.txt": instructions.encode()}
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "x", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.write(sga, "Berber_future_kingdom.sga")
        for name, data in files.items():
            z.writestr(name, data)
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    hashes["Berber_future_kingdom.sga"] = digest
    with zipfile.ZipFile(target) as z:
        if z.testzip() is not None or set(z.namelist()) != set(hashes):
            raise ValueError("Package member/CRC failure")
        for name, value in hashes.items():
            with z.open(name) as f:
                if hashlib.file_digest(f, "sha256").hexdigest() != value:
                    raise ValueError("Packaged member hash failure")
    result = {"version": version, "status": "package_verified_runtime_pending",
              "zip": str(target), "zip_sha256": sha(target), "zip_bytes": target.stat().st_size,
              "sga_sha256": digest, "zip_members": hashes, "source_baseline": "0.8.1",
              "disposable_staging_bytes_created": 0, "voice_install_required": False}
    (destination / "release-validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--version")
    parser.add_argument("--summary")
    parser.add_argument("--sga", type=Path, default=SGA)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.check:
        result = check()
    elif args.version and args.summary:
        result = build(args.version, args.summary, args.sga, args.output)
    else:
        parser.error("Choose --check or --version and --summary")
    print(json.dumps({k: v for k, v in result.items() if k != "zip_members"}, indent=2))


if __name__ == "__main__":
    cli()
