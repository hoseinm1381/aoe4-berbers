"""Register and cook release-owned native variants through supported Garrison CLI."""
from __future__ import annotations
import argparse
import json
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path
from berber_050_common import CORE, EDITOR, GUID, OUT, ROOT, read, run, sha, write

PROJECT = OUT / 'garrison-library/Mods/berber_units_050'


def configuration(project=PROJECT):
    return {key: value for key, value in read(project / 'mod-project.json').items()
            if key not in {'cooks', 'created_at_utc', 'runtime_modules'}}


def short_cook_copy():
    """Keep native texture burner paths short; preserve the authoritative project."""
    anchor = Path('F:/aoe_4_temp').resolve()
    if not anchor.is_dir():
        raise ValueError('Configured temporary workspace F:/aoe_4_temp unavailable')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    clone = anchor / ('berber050_cook_' + stamp)
    if clone.exists() or not clone.resolve().is_relative_to(anchor):
        raise ValueError('Native cook copy path already exists or escapes workspace')
    clone.mkdir()
    data = read(PROJECT / 'mod-project.json')
    data['cooks'] = []
    write(clone / 'mod-project.json', data)
    copied = {}
    for source in (PROJECT / 'project/source').rglob('*.png'):
        relative = source.relative_to(PROJECT)
        target = clone / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if sha(source) != sha(target):
            raise ValueError('Native cook PNG copy differs')
        copied[relative.as_posix()] = sha(target)
    owner = {'project_guid': GUID, 'workspace': str(ROOT.resolve()), 'author_project': str(PROJECT.resolve()),
             'cook_copy': str(clone.resolve()), 'copied_source_pngs': copied,
             'source_configuration': configuration()}
    write(clone / '.berber-050-cook-owner.json', owner)
    index = OUT / 'native-cook-copies.json'
    previous = read(index) if index.exists() else []
    previous.append({'path': str(clone.resolve()), 'owner_sha256': sha(clone / '.berber-050-cook-owner.json')})
    write(index, previous)
    if configuration(clone) != configuration():
        raise ValueError('Short cook copy configuration differs from authoring project')
    return clone

def ensure_project():
    if not (PROJECT / 'mod-project.json').exists():
        run(CORE, 'mod-project', 'create', '--library', OUT / 'garrison-library', '--name', PROJECT.name)
    run(CORE, 'mod-project', 'settings', '--project', PROJECT, '--live-reload', 'off', '--mod-id', GUID)

def register(name, source, albedo=None, *, expected_previous_source=None):
    ensure_project()
    record = read(PROJECT / 'mod-project.json')
    old = next((row for row in record.get('model_variants', []) if row['name'] == name), None)
    source = source.replace('\\', '/').removesuffix('.rgm')
    if old and old['source'].replace('\\', '/') != source:
        if old['source'].replace('\\', '/') != expected_previous_source:
            raise ValueError(f'Variant donor changed: {name}')
        # Explicitly qualified texture carriers for native merge attachments
        # without an RGO. This changes only this private cook configuration.
        old['source'] = source
        write(PROJECT / 'mod-project.json', record)
    if not old:
        run(CORE, 'mod-project', 'variant', '--project', PROJECT, '--source', source, '--name', name)
    if albedo:
        run(CORE, 'mod-project', 'variant-set', '--project', PROJECT, '--name', name,
            '--slot', 'albedoTexture', '--image', Path(albedo).resolve())
    return {'name': name, 'source': source,
            'private_stem': f'art/scenario/garrison/{PROJECT.name}/{name}/{name}',
            'albedo': str(Path(albedo).resolve()) if albedo else None,
            'albedo_sha256': sha(albedo) if albedo else None,
            'status': 'registered; geometry authoring/admission and fresh final cook required'}

def cook(source_hashes_path):
    sources = read(source_hashes_path)
    if not sources or {path: sha(path) for path in sources} != sources:
        raise ValueError('Current authoring input snapshot required before final cook')
    ensure_project()
    expected_configuration = read(OUT / 'final-project-configuration.json')
    if configuration() != expected_configuration:
        raise ValueError('Registered authoring configuration differs from frozen source inputs')
    build_project = short_cook_copy()
    project_before = sha(PROJECT / 'mod-project.json')
    log = OUT / 'final-art-cook.log'
    command = [str(CORE), 'mod-project', 'cook', '--project', str(build_project),
               '--editor', str(EDITOR), '--timeout', '900']
    with log.open('w', encoding='utf8') as stream:
        result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, timeout=960)
    record = {'status': 'failed' if result.returncode else 'passed', 'exit_code': result.returncode,
              'live_reload': False, 'source_hashes': sources, 'project': str(PROJECT),
              'cook_project': str(build_project), 'short_copy_configuration_equal': True,
              'project_before_sha256': project_before, 'log': str(log),
              'scope': 'native model variants, private material textures and registered blueprints; '
                       'authored native geometry is separately verified during composition',
              'native_acceptance': 'pending'}
    if not result.returncode:
        latest = read(build_project / 'mod-project.json')['cooks'][-1]
        if latest.get('live_reload') is not False or sha(latest['archive']) != latest['sha256']:
            raise ValueError('Cook archive or Live Reload state invalid')
        if {path: sha(path) for path in sources} != sources:
            raise ValueError('Authoring inputs changed while final cook was running')
        if configuration() != expected_configuration or configuration(build_project) != expected_configuration:
            raise ValueError('Native cook altered frozen project configuration')
        record['cook'] = latest
    write(OUT / 'art-cook.json', record)
    if result.returncode:
        raise RuntimeError(f'Final art cook failed; inspect {log}')
    return record

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='stage', required=True)
    add = sub.add_parser('register')
    add.add_argument('name')
    add.add_argument('source')
    add.add_argument('--albedo', type=Path)
    build = sub.add_parser('cook')
    build.add_argument('source_hashes', type=Path)
    args = parser.parse_args()
    record = register(args.name, args.source, args.albedo) if args.stage == 'register' else cook(args.source_hashes)
    print(json.dumps({key: value for key, value in record.items() if key != 'cook'}, indent=2))
