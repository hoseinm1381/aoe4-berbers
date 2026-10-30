"""Make checked-out Blender image paths relative; geometry stays unchanged.

blender --background --factory-startup --python tools/relocate_blends.py -- [--check]
Only indexed repository masters are opened, with embedded Python disabled.
"""
import argparse
import hashlib
import json
import ntpath
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
AUTHORING = ROOT/'authoring'
parser = argparse.ArgumentParser()
parser.add_argument('--check', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
index = json.loads((ROOT/'source/master-index.json').read_text(encoding='utf-8'))['files']
by_original = {ntpath.normcase(ntpath.normpath(x['original'])): x for x in index}
receipt_path = ROOT/'source/portable-masters.json'
receipt = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else {'schema':'berbers.portable-masters/v1','files':{}}
relocated, checked, dependencies = 0, 0, 0


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


for row in index:
    if not row['path'].lower().endswith('.blend'):
        continue
    path = (AUTHORING/row['path']).resolve()
    assert path.is_relative_to(AUTHORING.resolve()) and path.is_file(), path
    expected = receipt['files'].get(row['path'], row)
    assert sha(path) == expected['sha256'], f'Existing user edits protected: {path}'
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False, use_scripts=False)
    changed = False
    for item in [*bpy.data.images, *bpy.data.libraries]:
        if isinstance(item,bpy.types.Image) and (item.packed_file or item.source in ('GENERATED','VIEWER')):
            continue
        if not item.filepath:
            continue
        current = item.filepath
        if current.startswith('//'):
            target = Path(bpy.path.abspath(current)).resolve()
            original = ntpath.join(ntpath.dirname(row['original']), current[2:])
        else:
            target = Path(current)
            original = current
        match = by_original.get(ntpath.normcase(ntpath.normpath(original)))
        if match:
            target = AUTHORING/match['path']
        else:
            assert target.is_file(), f'Unmapped dependency in {path}: {current}'
        target = target.resolve()
        assert target.is_relative_to(AUTHORING.resolve()) and target.is_file(), target
        portable = bpy.path.relpath(str(target), start=str(path.parent))
        assert portable.startswith('//')
        dependencies += 1
        if item.filepath != portable:
            assert not args.check, f'Nonportable dependency in {path}: {current}'
            item.filepath = portable
            changed = True
    if changed:
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(path), relative_remap=False)
        receipt['files'][row['path']] = {'bytes':path.stat().st_size,'sha256':sha(path),'original_sha256':row['sha256'],'change':'external image/library paths made repository-relative'}
        relocated += 1
    checked += 1
if not args.check:
    receipt.update(checked_blends=checked, external_dependencies=dependencies, geometry_edits=False)
    receipt_path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print('BLENDER_MASTERS_VERIFIED',checked,'EXTERNAL_DEPENDENCIES',dependencies,'RELOCATED',relocated,flush=True)
