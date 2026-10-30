"""Release-owned paths and baseline preservation for the 0.5.0 unit overhaul."""
from __future__ import annotations
import hashlib
import json
import os
import subprocess
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/berber_update_0_5_0'
ART = ROOT / 'art/unit_remix_0_5_0'
BASE = ROOT / 'output/berber_update_0_4_0/package/Berber_future_kingdom.sga'
BASE_SHA = 'a23d308c4dda1af40fc6138e40b97904afd73c0a0a0816d0f3e4b1130d8718ec'
GUID = '1d3145e8-f1b2-427f-8bb0-067851fcf0f1'
EXT = Path(os.environ['APPDATA']) / 'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
CORE = EXT / 'bin/core/garrison-core.exe'
ARCH = EXT / 'bin/sga-archiver.exe'
EDITOR = Path(os.environ['LOCALAPPDATA']) / 'Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe'

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf8')

def run(*args, timeout=600):
    result = subprocess.run([str(a) for a in args], capture_output=True, text=True,
                            encoding='utf8', errors='replace', timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}): {args}\n{result.stdout[-2500:]}\n{result.stderr[-3500:]}')
    return result.stdout

def freeze_baseline():
    assert sha(BASE) == BASE_SHA, 'Packaged 0.4.0 baseline changed'
    OUT.mkdir(parents=True, exist_ok=True)
    destination = OUT / 'baseline-source-snapshot.zip'
    if destination.exists():
        record = read(OUT / 'baseline-preservation.json')
        assert sha(destination) == record['source_snapshot_sha256']
        return record
    sources = [ROOT / 'Berber_future_kingdom.aoe4mod', ROOT / 'AGENTS.md', ROOT / 'STORAGE.md']
    for folder in ('assets/attrib', 'assets/scar', 'assets/locdb'):
        sources.extend(p for p in (ROOT / folder).rglob('*') if p.is_file())
    sources.extend(p for p in (ROOT / 'assets').glob('*.rdo') if p.is_file())
    sources = sorted(set(p for p in sources if p.is_file()))
    with ZipFile(destination, 'x', ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sources:
            archive.write(path, path.relative_to(ROOT).as_posix())
    record = {'status': 'passed', 'version': '0.5.0', 'project_guid': GUID,
              'baseline': str(BASE), 'baseline_sha256': BASE_SHA,
              'source_snapshot': str(destination), 'source_snapshot_sha256': sha(destination),
              'source_files': {p.relative_to(ROOT).as_posix(): sha(p) for p in sources},
              'root_archive_is_not_baseline': True,
              'output_resolved': str(OUT.resolve()),
              'native_acceptance': 'deferred by user; package-first candidate'}
    write(OUT / 'baseline-preservation.json', record)
    return record

if __name__ == '__main__':
    result = freeze_baseline()
    print(json.dumps({k: v for k, v in result.items() if k != 'source_files'}, indent=2))
