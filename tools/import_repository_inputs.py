"""One-time migration of verified Release blobs into whole repository files."""
import hashlib
import json
import os
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def git(*args):
    subprocess.run(['git', *args], cwd=ROOT, check=True)


def install(path, raw):
    target = (ROOT/path).resolve()
    assert target.is_relative_to(ROOT) and not target.is_symlink(), path
    if target.exists():
        assert target.read_bytes() == raw, f'Existing edits protected: {path}'
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)


def main():
    assert os.environ.get('GITHUB_ACTIONS') == 'true'
    assert os.environ.get('GITHUB_REPOSITORY') == 'hoseinm1381/aoe4-berbers'
    assert os.environ.get('GITHUB_REF') == 'refs/heads/main'
    packs = read(ROOT/'docs/preservation/packed-inputs.json')['packs']
    rows = read(ROOT/'source/master-index.json')['files']
    paths = []
    native = {}
    with tempfile.TemporaryDirectory() as temporary:
        for pack in packs:
            archive = Path(temporary)/pack['name']
            with urllib.request.urlopen(pack['url'], timeout=120) as response, archive.open('wb') as out:
                while chunk := response.read(4*1024*1024):
                    out.write(chunk)
            assert archive.stat().st_size == pack['bytes'] and sha(archive) == pack['sha256']
            with zipfile.ZipFile(archive) as source:
                assert source.testzip() is None
                if pack['kind'] == 'editable-masters':
                    for row in rows:
                        if row['pack'] != pack['name']:
                            continue
                        raw = source.read(row['member'])
                        assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
                        path = 'authoring/'+row['path']
                        install(path, raw)
                        paths.append((path, len(raw)))
                else:
                    for member in sorted(source.namelist()):
                        assert not member.endswith('/') and not Path(member).is_absolute() and '..' not in Path(member).parts
                        raw = source.read(member)
                        path = 'inputs/native/'+member
                        install(path, raw)
                        native[member] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
                        paths.append((path, len(raw)))
            print('RESTORED', pack['name'], flush=True)
    write(ROOT/'inputs/native-manifest.json', native)
    large = [path for path, size in paths if size >= 100_000_000]
    attributes = '* -text\n' + ''.join(f'/{path} filter=lfs diff=lfs merge=lfs -text\n' for path in sorted(large))
    (ROOT/'.gitattributes').write_text(attributes, encoding='utf-8')
    git('lfs', 'install', '--local')
    git('config', 'user.name', 'github-actions[bot]')
    git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    git('add', '.gitattributes', 'inputs/native-manifest.json')
    result = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT)
    if result.returncode == 1:
        git('commit', '-m', 'Index complete repository-native build inputs and large files')
        git('push', 'origin', 'HEAD:main')
    else:
        assert result.returncode == 0
    # Bounded pushes; whole files keep their natural paths, with no download parts.
    batch, size, number = [], 0, 0
    def push_batch():
        nonlocal batch, size, number
        if not batch:
            return
        number += 1
        pathspec = Path(tempfile.gettempdir())/'berbers-git-paths'
        pathspec.write_bytes(b'\0'.join(p.encode() for p in batch)+b'\0')
        git('add', '--force', '--pathspec-from-file='+str(pathspec), '--pathspec-file-nul')
        result = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT)
        if result.returncode == 1:
            git('commit', '-m', f'Preserve editable masters and native inputs in repository ({number})')
            git('push', 'origin', 'HEAD:main')
        else:
            assert result.returncode == 0
        print('COMMITTED_BATCH', number, len(batch), size, flush=True)
        batch, size = [], 0
    for path, count in sorted(paths):
        if size+count > 350_000_000:
            push_batch()
        batch.append(path)
        size += count
    push_batch()
    subprocess.run(['python3', 'tools/inputs.py', 'verify'], cwd=ROOT, check=True)
    git('lfs', 'fsck')
    write(ROOT/'docs/preservation/repository-import.json', {
        'schema': 'berbers.repository-import/v1',
        'editable_files': len(rows), 'editable_bytes': sum(x['bytes'] for x in rows),
        'native_files': len(native), 'native_bytes': sum(x['bytes'] for x in native.values()),
        'lfs_paths': large, 'whole_files': True, 'separate_downloads_required': False,
        'all_source_hashes_verified': True,
        'playable_zip_sha256': 'b8c016ecfba0c4fab3a210bd4b4a58eed6a088fbbe8dac759f65a35c19e9f7dd',
    })
    git('add', 'docs/preservation/repository-import.json')
    git('commit', '-m', 'Record verified single-repository preservation')
    git('push', 'origin', 'HEAD:main')


if __name__ == '__main__':
    main()
