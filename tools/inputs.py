"""Verify whole editable/native files already supplied by this repository."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def verify(path, row):
    assert path.is_file(), f'Missing repository file: {path}; complete the Git/Git LFS checkout'
    assert path.stat().st_size == row['bytes'], f'Size mismatch (or LFS pointer): {path}'
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert actual == row['sha256'], f'Changed source file: {path}'


def main():
    native = read(ROOT/'inputs/native-manifest.json')
    for path, row in native.items():
        verify(ROOT/'inputs/native'/path, row)
    print('VERIFIED_NATIVE_FILES', len(native), flush=True)
    portable = ROOT/'source/portable-masters.json'
    overrides = read(portable).get('files', {}) if portable.exists() else {}
    masters = read(ROOT/'source/master-index.json')['files']
    for row in masters:
        verify(ROOT/'authoring'/row['path'], overrides.get(row['path'], row))
    print('VERIFIED_EDITABLE_FILES', len(masters), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['verify'])
    parser.parse_args()
    main()
