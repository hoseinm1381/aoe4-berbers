"""Verified, scoped 0.5.0 cache cleanup; plan never deletes or creates bundles.

Usage: py -3.13 research/berber_050_cleanup.py {plan,run,restore,verify}
Run only after release-validation.json passes. Restore decoded manifests before
rebuilding sources that read decoded-static.json. Native game acceptance remains
a separate gate. No recursive deletion or traversal through internal reparse points.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile

from berber_050_common import ART, BASE, BASE_SHA, GUID, OUT, ROOT, read, sha, write
from berber_050_release import verify_zip

CACHE = ROOT / 'output/shared_stock_cache/units_050'
PROJECT = OUT / 'garrison-library/Mods/berber_units_050'
EXTERNAL = Path('F:/aoe_4_temp')
MAP = EXTERNAL / 'Berber_future_kingdom_ai_20261014/path-map.json'
REBUILD = OUT / 'rebuild'
BUNDLE = REBUILD / 'decoded-manifests.zip'
INDEX = REBUILD / 'cache-bundle.json'
REPARSE = getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)


def is_reparse(path):
    record = path.lstat()
    return stat.S_ISLNK(record.st_mode) or bool(getattr(record, 'st_file_attributes', 0) & REPARSE)


def mapped(path):
    """Permit only the existing STORAGE.md relocation map at scope boundaries."""
    path = Path(path).absolute()
    expected = ROOT.resolve() / path.relative_to(ROOT)
    matches = []
    relocation_rows = read(MAP)
    approved_boundaries = {}
    for row in relocation_rows:
        source, destination = Path(row['Source']), Path(row['Destination'])
        if path.is_relative_to(source):
            if row.get('SHA256Verified') is not True or not destination.resolve().is_relative_to(MAP.parent.resolve()):
                raise ValueError(f'Unverified external storage mapping: {source}')
            matches.append((len(source.parts), destination / path.relative_to(source)))
            approved_boundaries[source.absolute()] = destination.absolute()
    current = ROOT.absolute()
    for part in path.relative_to(ROOT).parts:
        current /= part
        if current.exists() and is_reparse(current):
            if current not in approved_boundaries or current.resolve() != approved_boundaries[current]:
                raise ValueError(f'Unapproved reparse boundary in scope path: {current}')
    if matches:
        expected = max(matches, key=lambda row: row[0])[1]
    resolved = path.resolve()
    if resolved != expected.absolute():
        raise ValueError(f'Unexpected resolved scope: {path} -> {resolved}')
    return resolved


def safe_relative(value):
    if not isinstance(value, str) or '\\' in value or ':' in value:
        raise ValueError(f'Unsafe relative bundle path: {value!r}')
    relative = PurePosixPath(value)
    if relative.is_absolute() or not relative.parts or any(p in ('..', '.') for p in relative.parts):
        raise ValueError(f'Unsafe relative bundle path: {value!r}')
    return Path(*relative.parts)


def no_reparse(path, scope):
    """Recheck every existing component immediately before reading/deleting."""
    path, scope = Path(path).absolute(), Path(scope).absolute()
    if not path.is_relative_to(scope) or path == scope:
        raise ValueError(f'Target outside exact scope: {path}')
    current = scope
    if is_reparse(scope):
        raise ValueError(f'Reparse scope root refused: {scope}')
    for part in path.relative_to(scope).parts:
        current /= part
        if current.exists() or current.is_symlink():
            if is_reparse(current):
                raise ValueError(f'Reparse component refused: {current}')
    if path.resolve() != path:
        raise ValueError(f'Target resolution changed: {path}')


def owned_output(path):
    out = mapped(OUT)
    path = Path(path).absolute()
    if path.is_relative_to(OUT.absolute()):
        path = out / path.relative_to(OUT.absolute())
    if not path.is_relative_to(out):
        raise ValueError(f'Report/bundle output is outside the release scope: {path}')
    no_reparse(path, out)
    return path


def save(path, value):
    write(owned_output(path), value)


def inventory(scope):
    files, skipped = [], []
    if not scope.exists():
        return files, skipped
    if is_reparse(scope):
        raise ValueError(f'Reparse scope root refused: {scope}')
    stack = [scope]
    while stack:
        folder = stack.pop()
        with os.scandir(folder) as entries:
            for entry in entries:
                path = Path(entry.path)
                if is_reparse(path):
                    skipped.append(str(path))
                elif entry.is_dir(follow_symlinks=False):
                    stack.append(path)
                elif entry.is_file(follow_symlinks=False):
                    files.append(path)
    return sorted(files), sorted(skipped)


def delivery():
    """Pin delivery, package contents, preserved baseline and rebuild document."""
    out = mapped(OUT)
    record = read(out / 'release-validation.json')
    if record.get('status') != 'passed' or record.get('baseline_sha256') != BASE_SHA or sha(BASE) != BASE_SHA:
        raise ValueError('Release validation/baseline gate failed')
    zip_path, sga = Path(record['zip']).resolve(), Path(record['sga']).resolve()
    if zip_path.parent != out or sga != out / 'package/Berber_future_kingdom.sga':
        raise ValueError('Delivery paths are not the exact release-owned ZIP/package')
    no_reparse(zip_path, out)
    no_reparse(sga, out)
    if sha(zip_path) != record['zip_sha256'] or sha(sga) != record['sga_sha256']:
        raise ValueError('ZIP or packaged SGA changed')
    validation = verify_zip(zip_path, record['sga_sha256'])
    with ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            target = out / 'package' / safe_relative(info.filename)
            no_reparse(target, out)
            if sha(target) != hashlib.sha256(archive.read(info)).hexdigest():
                raise ValueError(f'ZIP/package member differs: {info.filename}')
    preserved = read(out / 'baseline-preservation.json')
    snapshot = out / 'baseline-source-snapshot.zip'
    if sha(snapshot) != preserved['source_snapshot_sha256']:
        raise ValueError('Baseline source snapshot changed')
    live_sources = {relative: sha(ROOT / relative) for relative in preserved['source_files']}
    if live_sources != preserved['source_files']:
        raise ValueError('Original live project/source files changed from baseline preservation')
    with ZipFile(snapshot) as archive:
        if archive.testzip() is not None:
            raise ValueError('Baseline snapshot CRC failed')
    document = ROOT / 'Design/asset_overhaul/BERBER_050_REBUILD.md'
    if sha(document) != sha(out / 'package/REBUILD_050.md'):
        raise ValueError('Delivered rebuild guide differs from frozen author guide')
    return {'status': 'passed', 'zip': str(zip_path), 'zip_sha256': sha(zip_path),
            'sga': str(sga), 'sga_sha256': sha(sga), 'baseline_sha256': sha(BASE),
            'snapshot_sha256': sha(snapshot), 'rebuild_document_sha256': sha(document),
            'original_live_source_hash_checks': len(live_sources),
            'original_live_source_hashes': live_sources,
            'zip_members': validation['members']}


def external_copies(out):
    records = read(out / 'native-cook-copies.json') if (out / 'native-cook-copies.json').exists() else []
    result = []
    for row in records:
        raw = Path(row['path'])
        path = raw.resolve()
        anchor = EXTERNAL.resolve()
        if path.parent != anchor or not path.name.startswith('berber050_cook_') or raw.absolute() != path:
            raise ValueError(f'External cook path is not an exact owned direct child: {raw}')
        if not path.exists():
            continue
        if is_reparse(path):
            raise ValueError(f'External cook root is a reparse point: {path}')
        sentinel = path / '.berber-050-cook-owner.json'
        no_reparse(sentinel, path)
        if sha(sentinel) != row['owner_sha256']:
            raise ValueError(f'External cook sentinel changed: {path}')
        owner = read(sentinel)
        if (owner['project_guid'] != GUID or Path(owner['workspace']).resolve() != ROOT.resolve()
                or Path(owner['author_project']).resolve() != PROJECT.resolve()
                or Path(owner['cook_copy']).resolve() != path):
            raise ValueError(f'External cook ownership differs: {path}')
        for relative, expected in owner['copied_source_pngs'].items():
            relative = safe_relative(relative)
            source = owned_output(PROJECT / relative)
            no_reparse(source, PROJECT.resolve())
            if source.suffix.lower() != '.png' or sha(source) != expected:
                raise ValueError(f'Cook copy author source is not retained unchanged: {source}')
        if inventory(path)[1]:
            raise ValueError(f'External cook copy contains internal reparse points: {path}')
        result.append((path, owner))
    return result


def scopes():
    result = {'out': mapped(OUT), 'art': mapped(ART), 'cache': mapped(CACHE)}
    owners = external_copies(result['out'])
    for number, (path, owner) in enumerate(owners):
        result[f'external_{number}'] = path
    if len(set(result.values())) != len(result):
        raise ValueError('Overlapping/duplicate cleanup scope roots')
    for name, path in result.items():
        if any(path != other and path.is_relative_to(other) for other in result.values()):
            raise ValueError(f'Nested scope refused: {name}')
    return result, owners


def verify_bundle():
    owned_output(INDEX)
    owned_output(BUNDLE)
    record = read(INDEX)
    cache = mapped(CACHE)
    if record['schema'] != 'berber-050-decoded-cache-bundle/v1' or Path(record['cache_root']).resolve() != cache:
        raise ValueError('Bundle identity/scope differs')
    if sha(BUNDLE) != record['zip_sha256']:
        raise ValueError('Decoded manifest rebuild ZIP changed')
    expected = {entry['relative']: entry for entry in record['files']}
    if len(expected) != len(record['files']):
        raise ValueError('Duplicate bundle index path')
    with ZipFile(BUNDLE) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected) or archive.testzip() is not None:
            raise ValueError('Bundle members/CRC differ from index')
        for name in names:
            relative = safe_relative(name)
            if relative.name != 'decoded-static.json':
                raise ValueError('Unexpected rebuild bundle member')
            data = archive.read(name)
            if len(data) != expected[name]['bytes'] or hashlib.sha256(data).hexdigest() != expected[name]['sha256']:
                raise ValueError(f'Lossless bundle verification failed: {name}')
    return record


def ensure_bundle(cache, files):
    owned_output(INDEX)
    owned_output(BUNDLE)
    manifests = [p for p in files if p.name == 'decoded-static.json']
    if INDEX.exists() or BUNDLE.exists():
        if not (INDEX.exists() and BUNDLE.exists()):
            raise ValueError('Partial existing rebuild bundle; inspect before retrying')
        record = verify_bundle()
        old = {e['relative']: e for e in record['files']}
        for path in manifests:
            relative = path.relative_to(cache).as_posix()
            if relative not in old or sha(path) != old[relative]['sha256']:
                raise ValueError('New/changed decoded cache requires a separately reviewed bundle refresh')
        return record
    REBUILD.mkdir(parents=True, exist_ok=True)
    rows = []
    temporary = BUNDLE.with_suffix('.zip.partial')
    owned_output(temporary)
    if temporary.exists():
        raise ValueError('Partial rebuild bundle exists; inspect before retrying')
    with ZipFile(temporary, 'x', ZIP_DEFLATED, compresslevel=9) as archive:
        for path in manifests:
            no_reparse(path, cache)
            relative = path.relative_to(cache).as_posix()
            rows.append({'relative': relative, 'sha256': sha(path), 'bytes': path.stat().st_size})
            archive.write(path, relative)
    temporary.replace(BUNDLE)
    record = {'schema': 'berber-050-decoded-cache-bundle/v1', 'cache_root': str(cache),
              'zip': str(BUNDLE.resolve()), 'zip_sha256': sha(BUNDLE), 'files': rows,
              'restore': 'py -3.13 research/berber_050_cleanup.py restore',
              'reason': 'Recipes read decoded-static.json; restore this lossless bundle before rebuilding. Native donor and DDS inputs remain uncompressed in the one shared cache.'}
    save(INDEX, record)
    return verify_bundle()


def disposable(scope_name, relative, path):
    parts = relative.parts
    lower = [p.lower() for p in parts]
    if scope_name.startswith('external_'):
        return 'verified release-owned short cook copy'
    if scope_name == 'cache':
        return 'losslessly bundled decoded donor manifest' if path.name == 'decoded-static.json' else None
    if '__pycache__' in lower:
        return 'regenerable Python bytecode cache'
    if scope_name == 'art':
        if path.suffix.lower() in ('.blend1', '.blend2') and path.with_suffix('.blend').is_file():
            return 'redundant Blender save backup; main editable Blend retained'
        return None
    if path.name == 'mod-project.json':
        return None
    if len(parts) >= 2 and lower[0] == 'integration':
        if len(parts) == 2 and lower[1] in ('data-candidate.sga', 'attrib-candidate.sga'):
            return 'composition intermediate/final duplicate; identical validated package SGA retained'
        if len(parts) >= 3 and ('readback' in lower[1] or lower[1] in ('actor-payloads','attachment-payloads','material-payloads','model-payloads')):
            return 'release integration readback or reproducible payload copy'
    if lower[0] in ('pilot-native-variant-readback', 'pilot-library', 'sol-pilot-library'):
        if path.suffix.lower() == '.json':
            return None
        return 'superseded feasibility project/cook/readback; active ART recipes checked independent and compact configs retained'
    if lower[0] == 'garrison-library' and ('dist' in lower or 'project' in lower):
        if 'source' in lower:
            return None
        return 'canonical project generated cook/export copy; mod-project.json and project/source retained'
    # Compact reports outside explicitly disposable generated trees are retained.
    if path.suffix.lower() == '.json':
        return None
    if len(parts) == 1 and path.name in ('sol-abb-geometry-pilot.sga','sol-abb-geometry-pilot-readback.rrgeom'):
        return 'superseded private feasibility cook/readback; current authored/native inputs retained'
    return None


def make_plan():
    validated = delivery()
    roots, owners = scopes()
    # These OUT libraries are technical feasibility projects. Accepted art lives
    # in ART/pilots; refuse removal if an active recipe/manifest references a copy.
    for path in inventory(roots['art'])[0] + [owned_output(PROJECT / 'mod-project.json')]:
        if path.suffix.lower() != '.json' or not (path.name == 'recipe.json' or 'manifest' in path.name or path.name == 'mod-project.json'):
            continue
        text = path.read_text(encoding='utf-8-sig').replace('\\', '/').lower()
        if any(token in text for token in ('/pilot-library/', '/sol-pilot-library/')):
            raise ValueError(f'Active rebuild input references superseded feasibility project: {path}')
    inventories, skipped, targets = {}, [], []
    for name, root in roots.items():
        files, links = inventory(root)
        skipped.extend(links)
        inventories[name] = {'root': str(root), 'files': len(files), 'bytes': sum(p.stat().st_size for p in files)}
        for path in files:
            reason = disposable(name, path.relative_to(root), path)
            if reason:
                no_reparse(path, root)
                targets.append({'path': str(path), 'scope': name, 'bytes': path.stat().st_size, 'sha256': sha(path), 'reason': reason})
    return {'schema': 'berber-050-cleanup/v1', 'status': 'verified_plan_no_deletion',
            'utc': datetime.now(timezone.utc).isoformat(), 'delivery': validated,
            'scopes': inventories, 'before_bytes': sum(r['bytes'] for r in inventories.values()),
            'planned_removed_bytes': sum(r['bytes'] for r in targets), 'targets': targets,
            'skipped_reparse_points': skipped, 'external_owners': [o for p,o in owners],
            'retained_rebuild_inputs': ['all editable .blend, authored PNG/RRGeom, recipes/scripts and manifests',
                'all native donor RGM/RGO/RRGeom/material/texture/DDS inputs and shared cache provenance',
                'all pinned authoring/review PNGs, delivery ZIP/package, baseline snapshot and compact proof',
                'mod-project.json and project/source PNGs needed by native short-cook reproduction'],
            'retained_cache_reason': 'Native source and DDS dependencies remain; only decoded manifests are bundled losslessly. Restore before recipe rebuild.'}


def run_cleanup():
    plan = make_plan()
    roots, _ = scopes()
    bundle = ensure_bundle(roots['cache'], inventory(roots['cache'])[0])
    plan['bundle'] = {'index': str(INDEX), 'zip_sha256': bundle['zip_sha256'], 'files': len(bundle['files'])}
    # Preserve configs before deleting any generated files, including external copies.
    configs = {}
    for name, root in roots.items():
        for path in inventory(root)[0]:
            if path.name == 'mod-project.json':
                configs[str(path)] = {'sha256': sha(path), 'configuration': read(path)}
    save(REBUILD / 'project-configurations.json', configs)
    save(OUT / 'cleanup-preflight.json', plan)
    removed = []
    try:
        for target in plan['targets']:
            path, scope = Path(target['path']), roots[target['scope']]
            no_reparse(path, scope)
            if path.stat().st_size != target['bytes'] or sha(path) != target['sha256']:
                raise ValueError(f'Target changed after verified plan: {path}')
            if target['scope'] == 'cache':
                member = path.relative_to(scope).as_posix()
                entry = next(e for e in bundle['files'] if e['relative'] == member)
                if entry['sha256'] != target['sha256']:
                    raise ValueError('Bundle pin differs from deletion target')
            path.unlink()
            removed.append(target)
        # Verified external owner roots contain only disposable copies. Remove
        # empty directories bottom-up without recursive deletion or link traversal.
        for name, root in roots.items():
            if not name.startswith('external_'):
                continue
            directories, pending = [], [root]
            while pending:
                directory = pending.pop()
                if is_reparse(directory):
                    raise ValueError(f'External directory became a reparse point: {directory}')
                directories.append(directory)
                with os.scandir(directory) as entries:
                    for item in entries:
                        child = Path(item.path)
                        if is_reparse(child):
                            raise ValueError(f'External reparse point appeared: {child}')
                        if item.is_dir(follow_symlinks=False):
                            pending.append(child)
                        else:
                            raise ValueError(f'Unexpected file remains in disposable cook copy: {child}')
            for directory in reversed(directories):
                if directory != root:
                    no_reparse(directory, root)
                elif is_reparse(directory):
                    raise ValueError('External root became a reparse point')
                directory.rmdir()
        after_delivery = delivery()
        if after_delivery != plan['delivery']:
            raise ValueError('Protected delivery hashes changed after cleanup')
        verify_bundle()
        plan['status'] = 'cleanup_complete' if not plan['skipped_reparse_points'] else 'cleanup_incomplete_reparse_points_retained'
    except Exception as error:
        plan['status'] = 'cleanup_incomplete'
        plan['error'] = str(error)
        raise
    finally:
        plan['removed_targets'] = removed
        plan['removed_bytes'] = sum(r['bytes'] for r in removed)
        report = OUT / 'cleanup-report.json'
        for attempt in range(8):
            plan['after_scopes'] = {name: {'root':str(root),'bytes':sum(p.stat().st_size for p in inventory(root)[0])} for name,root in roots.items()}
            plan['after_bytes'] = sum(r['bytes'] for r in plan['after_scopes'].values())
            plan['net_bytes_reclaimed'] = plan['before_bytes'] - plan['after_bytes']
            save(report, plan)
            observed = sum(p.stat().st_size for root in roots.values() for p in inventory(root)[0])
            if observed == plan['after_bytes']:
                break
        else:
            raise ValueError('Cleanup report byte-count fixed point did not converge')
    return plan


def restore():
    record = verify_bundle()
    cache = mapped(CACHE)
    restored, identical = [], []
    with ZipFile(BUNDLE) as archive:
        # Check every existing destination before writing any destination.
        for row in record['files']:
            target = cache / safe_relative(row['relative'])
            no_reparse(target, cache)
            if target.exists() and sha(target) != row['sha256']:
                raise ValueError(f'Restore refuses different existing bytes: {target}')
        for row in record['files']:
            target = cache / safe_relative(row['relative'])
            no_reparse(target, cache)
            if target.exists():
                identical.append(str(target))
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            no_reparse(target, cache)
            with target.open('xb') as output:
                output.write(archive.read(row['relative']))
            if sha(target) != row['sha256']:
                raise ValueError('Restored manifest hash differs')
            restored.append(str(target))
    return {'status':'restored_verified','restored':restored,'already_identical':identical}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('plan','run','restore','verify'))
    parser.add_argument('--output', type=Path, help='Optional plan/result JSON; no deletion in plan mode')
    args = parser.parse_args()
    if args.mode == 'plan':
        result = make_plan()
    elif args.mode == 'run':
        result = run_cleanup()
    elif args.mode == 'restore':
        result = restore()
    else:
        result = {'status':'verified','delivery':delivery()}
        if INDEX.exists() or BUNDLE.exists():
            result['bundle'] = verify_bundle()
    if args.output:
        save(args.output, result)
    compact = {k:v for k,v in result.items() if k not in ('targets','removed_targets','external_owners','bundle')}
    compact['target_count'] = len(result.get('targets', []))
    print(json.dumps(compact,indent=2))


if __name__ == '__main__':
    main()
