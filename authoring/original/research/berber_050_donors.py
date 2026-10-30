"""Read-only intake of native Age of Empires IV model donors for Berber 0.5.0.

The only writes are verified stock extractions and Garrison decode outputs under
output/shared_stock_cache/units_050 plus the compact release donor manifest.
This script never opens Blender, edits the mod source, cooks, or packages.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import berber_050_common as common

ROOT = common.ROOT
CACHE = ROOT / 'output/shared_stock_cache/units_050'
OUT = common.OUT
CONFIG = Path(os.environ['LOCALAPPDATA']) / 'Garrison/Kit/game-assets.local.json'
INDEX = Path(os.environ['LOCALAPPDATA']) / 'Garrison/Kit/game-assets.sqlite3'

# Exact native stock model paths.  These are donor resources only; consumer
# attachment bindings are recorded by the separate 0.5.0 reference audit.
PILOT_GROUPS: dict[str, dict[str, Any]] = {
    'villager': {
        'archetype': 'civilian_humanoid', 'ages': [1, 2, 3, 4],
        'models': [
            f'art/civilizations/malian/humans/mal_villager_{sex}_age0{age}/mal_villager_{sex}_age0{age}.rgm'
            for age in range(1, 5) for sex in ('male', 'female')
        ],
    },
    'villager_abbasid_alternatives': {
        'archetype': 'civilian_humanoid_regional_alternative', 'ages': [1, 2, 3, 4],
        'models': [
            f'art/civilizations/abbasids/humans/abb_villager_male_age0{age}/abb_villager_male_age0{age}.rgm'
            for age in range(1, 5)
        ],
    },
    'archer': {
        'archetype': 'foot_ranged_humanoid', 'ages': [2, 3, 4],
        'models': [
            f'art/civilizations/malian/humans/mal_ranged_bow_age0{age}/mal_ranged_bow_age0{age}.rgm'
            for age in range(2, 5)
        ],
    },
    'archer_abbasid_alternatives': {
        'archetype': 'foot_ranged_humanoid_regional_alternative', 'ages': [2, 3, 4],
        'models': [
            f'art/civilizations/abbasids/humans/abb_ranged_bow_age0{age}/abb_ranged_bow_age0{age}.rgm'
            for age in range(2, 5)
        ],
    },
    'archer_sultanate_alternatives': {
        'archetype': 'foot_ranged_humanoid_regional_alternative', 'ages': [2, 3, 4],
        'models': [
            f'art/civilizations/sultanate/humans/sul_ranged_bow_age0{age}/sul_ranged_bow_age0{age}.rgm'
            for age in range(2, 5)
        ],
    },
    'scout': {
        'archetype': 'mounted_scout_rider_and_mount', 'ages': [1, 2, 3, 4],
        'models': [
            *[f'art/civilizations/malian/humans/mal_cavalry_scout_age0{age}/mal_cavalry_scout_age0{age}.rgm' for age in range(1, 5)],
            *[f'art/civilizations/malian/animals/mal_horse_scout_age0{age}/mal_horse_scout_age0{age}.rgm' for age in range(1, 5)],
        ],
    },
    'trader': {
        'archetype': 'mounted_trade_camel_complete_unit', 'ages': [2, 3, 4],
        'models': [f'art/civilizations/malian/animals/mal_camel_combined_trade_age0{age}/mal_camel_combined_trade_age0{age}.rgm' for age in range(2, 5)],
    },
    'mehari': {
        'archetype': 'mounted_camel_rider_and_mount', 'ages': [2, 3, 4],
        'models': [
            *[f'art/civilizations/malian/humans/mal_cavalry_light_age0{age}/mal_cavalry_light_age0{age}.rgm' for age in range(2, 5)],
            *[f'art/civilizations/abbasids/animals/abb_camel_armor_age0{age}/abb_camel_armor_age0{age}.rgm' for age in range(2, 5)],
            *[f'art/civilizations/abbasids/animals/abb_camel_combined_armor_age0{age}/abb_camel_combined_armor_age0{age}.rgm' for age in range(3, 5)],
        ],
    },
    'sanhaja': {
        'archetype': 'mounted_camel_archer_combined_unit', 'ages': [2, 3, 4],
        'models': [f'art/civilizations/abbasids/animals/abb_camel_combined_bow_age0{age}/abb_camel_combined_bow_age0{age}.rgm' for age in range(2, 5)],
    },
    'zenata': {
        'archetype': 'mounted_horseman_rider_and_mount', 'ages': [2, 3, 4],
        'models': [
            *[f'art/civilizations/malian/humans/mal_cavalry_light_age0{age}/mal_cavalry_light_age0{age}.rgm' for age in range(2, 5)],
            *[f'art/civilizations/malian/animals/mal_horse_light_age0{age}/mal_horse_light_age0{age}.rgm' for age in range(2, 5)],
        ],
    },
    'masmuda': {
        'archetype': 'foot_crossbow_humanoid', 'ages': [2, 3, 4],
        'models': [f'art/civilizations/malian/humans/mal_ranged_crossbow_age0{age}/mal_ranged_crossbow_age0{age}.rgm' for age in range(2, 5)],
    },
    'lancer': {
        'archetype': 'mounted_lancer_rider_and_armored_horse', 'ages': [3, 4],
        'models': [
            *[f'art/civilizations/malian/humans/mal_cavalry_armor_age0{age}/mal_cavalry_armor_age0{age}.rgm' for age in range(3, 5)],
            *[f'art/civilizations/malian/animals/mal_horse_armor_age0{age}/mal_horse_armor_age0{age}.rgm' for age in range(3, 5)],
        ],
    },
    'imam': {
        'archetype': 'religious_humanoid', 'ages': [3, 4],
        'models': [f'art/civilizations/malian/humans/mal_infantry_monk_age0{age}/mal_infantry_monk_age0{age}.rgm' for age in range(3, 5)],
    },
    'imam_regional_alternatives': {
        'archetype': 'religious_humanoid_regional_alternative', 'ages': [3, 4],
        'models': [
            *[f'art/civilizations/abbasids/humans/abb_infantry_monk_age0{age}/abb_infantry_monk_age0{age}.rgm' for age in range(3, 5)],
            *[f'art/civilizations/sultanate/humans/sul_infantry_monk_age0{age}/sul_infantry_monk_age0{age}.rgm' for age in range(3, 5)],
        ],
    },
    'handgunner': {
        'archetype': 'foot_firearm_humanoid', 'ages': [4],
        'models': ['art/civilizations/malian/humans/mal_ranged_cannoneer_age04/mal_ranged_cannoneer_age04.rgm'],
    },
    'king': {
        'archetype': 'conditional_regicide_humanoid', 'ages': [1, 2, 3, 4],
        'models': [
            f'art/civilizations/malian/humans/mal_infantry_light_age0{age}/mal_infantry_light_age0{age}.rgm'
            for age in range(1, 5)
        ],
    },
    'king_regional_alternatives': {
        'archetype': 'conditional_regicide_humanoid_regional_alternative', 'ages': [3, 4],
        'models': [
            'art/civilizations/abbasids/humans/abb_infantry_armor_age04/abb_infantry_armor_age04.rgm',
            'art/civilizations/sultanate/humans/sul_infantry_armor_age04/sul_infantry_armor_age04.rgm',
        ],
    },
    'horse_cavalry': {
        'archetype': 'mounted_horse_rider_and_mount', 'ages': [2, 3, 4],
        'models': [
            *[
                f'art/civilizations/malian/humans/mal_cavalry_light_age0{age}/mal_cavalry_light_age0{age}.rgm'
                for age in range(2, 5)
            ],
            *[
                f'art/civilizations/malian/animals/mal_horse_light_age0{age}/mal_horse_light_age0{age}.rgm'
                for age in range(2, 5)
            ],
        ],
    },
    'camel_archer': {
        'archetype': 'mounted_camel_archer_rider_and_mount', 'ages': [2, 3, 4],
        'models': [
            'art/civilizations/common/humans/archetypes/camel_archer/camel_archer.rgm',
            *[
                f'art/civilizations/abbasids/animals/abb_camel_combined_bow_age0{age}/abb_camel_combined_bow_age0{age}.rgm'
                for age in range(2, 5)
            ],
        ],
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def run_json(*args: str | Path) -> dict[str, Any]:
    result = subprocess.run([str(a) for a in args], capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=600, check=False)
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}): {args}\n{result.stdout[-2000:]}\n{result.stderr[-3000:]}')
    try:
        parsed = json.loads(result.stdout.strip())
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    for line in reversed(result.stdout.splitlines()):
        try:
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    raise RuntimeError(f'Command returned no JSON payload: {args}\n{result.stdout[-2000:]}')


def index_row(logical_path: str) -> dict[str, Any]:
    uri = f'file:{INDEX.as_posix()}?mode=ro'
    with sqlite3.connect(uri, uri=True) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute(
            "SELECT logical_path, extension, asset_kind, curated_category, civilization, "
            "object_class, object_type, size, archive, archive_path, archive_version, "
            "product_version, provider_count FROM resolved_assets "
            "WHERE logical_path=? AND extension='.rgm'",
            (logical_path,),
        ).fetchall()
    if len(rows) != 1:
        raise RuntimeError(f'Expected one indexed .rgm row for {logical_path}, found {len(rows)}')
    return dict(rows[0])


def decode_one(logical_path: str, *, family: str, role: str, age: int | None,
               consumer_targets: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    row = index_row(logical_path)
    archive = Path(row['archive_path'])
    if not archive.is_file():
        raise FileNotFoundError(f'Indexed archive is missing: {archive}')
    CACHE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='berber050-donor-') as tmp_name:
        staging = Path(tmp_name) / Path(logical_path).name
        extracted = run_json(common.ARCH, 'extract-member', archive, logical_path, staging)
        if not staging.is_file():
            raise RuntimeError(f'Archive extraction did not create {staging}: {extracted}')
        model_sha = sha256(staging)
        donor_id = hashlib.sha256(f'{logical_path}\0{model_sha}'.encode('utf-8')).hexdigest()
        bucket = CACHE / donor_id
        source_dir = bucket / 'source'
        decode_dir = bucket / 'decoded'
        source_dir.mkdir(parents=True, exist_ok=True)
        native_path = source_dir / Path(logical_path).name
        if native_path.exists() and sha256(native_path) != model_sha:
            raise RuntimeError(f'Existing cached donor source hash mismatch: {native_path}')
        if not native_path.exists():
            shutil.copy2(staging, native_path)
        decode_dir.mkdir(parents=True, exist_ok=True)
        # Garrison writes decoded-static.json beneath an archive-derived
        # subdirectory. Search recursively or a cached nested manifest is
        # mistaken for a miss and overwritten by later donor intake runs.
        def existing_decode() -> list[Path]:
            matches = []
            for path in decode_dir.rglob('decoded-static.json'):
                try:
                    report = json.loads(path.read_text(encoding='utf-8-sig'))
                except (OSError, json.JSONDecodeError):
                    continue
                if (report.get('request') or {}).get('logical_path') == logical_path:
                    matches.append(path)
            return matches
        manifests = existing_decode()
        if len(manifests) > 1:
            raise RuntimeError(f'Multiple cached decode manifests for {logical_path}: {manifests}')
        if not manifests:
            result = run_json(
                common.CORE, 'convert', 'decode-static',
                '--logical-path', logical_path,
                '--config', CONFIG,
                '--index', INDEX,
                '--output-root', decode_dir,
            )
            manifests = existing_decode()
        if len(manifests) != 1:
            raise RuntimeError(f'Expected one matching decoded-static.json under {decode_dir}; found {manifests}; result={result}')
        decode_report_path = manifests[0]
    decode_report = json.loads(decode_report_path.read_text(encoding='utf-8-sig'))
    skeleton = decode_report.get('skeleton') or {}
    bones = skeleton.get('bones') or []
    hierarchy = [(b.get('index'), b.get('name'), b.get('parent_index')) for b in bones]
    rest = [(b.get('index'), b.get('local_reference_transform')) for b in bones]
    geometry = decode_report.get('geometry') or {}
    groups = geometry.get('groups') or []
    material = decode_report.get('material') or {}
    texture_refs = sorted({str(t.get('logical_path')) for m in material.get('materials', [])
                           for block in m.get('blocks', []) for t in block.get('textures', [])
                           if t.get('logical_path') and t.get('logical_path') != '__default'})
    owner = decode_report.get('animation_projection') or {}
    source_entry = {'path': native_path.relative_to(bucket).as_posix(), 'bytes': native_path.stat().st_size,
                    'sha256': sha256(native_path)}
    files = []
    for path in sorted(decode_dir.rglob('*')):
        if path.is_file():
            files.append({'path': path.relative_to(bucket).as_posix(), 'bytes': path.stat().st_size,
                          'sha256': sha256(path)})
    manifest = {
        'schema': 'berber050-native-donor/v1',
        'donor_id': donor_id,
        'family': family,
        'role': role,
        'age': age,
        'exact_consumer_targets': consumer_targets or [],
        'logical_path': logical_path,
        'native_resource_sha256': model_sha,
        'archive': row['archive'],
        'archive_path': str(archive),
        'archive_version': row['archive_version'],
        'product_version': row['product_version'],
        'index_metadata': {k: row[k] for k in ('asset_kind', 'curated_category', 'civilization',
                                               'object_class', 'object_type', 'size', 'provider_count')},
        'source_copy': str(native_path.relative_to(ROOT).as_posix()),
        'decoded_manifest': str(decode_report_path.relative_to(ROOT).as_posix()),
        'geometry_summary': {
            'group_count': len(groups),
            'groups': [{k: group.get(k) for k in ('name', 'group_index', 'material', 'effect', 'stream',
                                                  'vertex_count', 'triangle_count', 'vertex_stride',
                                                  'index_stride', 'bone_count', 'maximum_influences')
                       if k in group} for group in groups],
            'rig_palette_binding': decode_report.get('rig_palette_binding'),
        },
        'skeleton_summary': {
            'status': skeleton.get('status'), 'bone_count': skeleton.get('bone_count'),
            'hierarchy_sha256': hashlib.sha256(json.dumps(hierarchy, separators=(',', ':')).encode()).hexdigest(),
            'rest_pose_sha256': hashlib.sha256(json.dumps(rest, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
            'duplicate_names': skeleton.get('duplicate_names', []),
        },
        'material_texture_logical_paths': texture_refs,
        'animation_owner': {
            'status': owner.get('status'), 'resolution': owner.get('resolution'),
            'template_id': (owner.get('template') or {}).get('template_id'),
            'source_logical_path': (owner.get('template') or {}).get('source_logical_path'),
            'clip_inventory_status': (owner.get('template') or {}).get('clip_inventory_status'),
        },
        'attachment_inventory': 'actor/tier/list/socket bindings are recorded in targets.json and confirmed roster-audit outputs; this donor manifest preserves the full decoded entity_binding but does not infer attachments from mesh names',
        'decode_report': decode_report,
        'source_files': [source_entry],
        'decoded_files': files,
        'decoder': str(common.CORE),
        'decoder_api': 'garrison-core convert decode-static --logical-path --config --index --output-root',
        'native_cook': 'not run',
    }
    common.write(bucket / 'donor-manifest.json', manifest)
    return {'donor_id': donor_id, 'family': family, 'role': role, 'age': age,
            'exact_consumer_targets': consumer_targets or [],
            'logical_path': logical_path, 'native_resource_sha256': model_sha,
            'bucket': bucket.relative_to(ROOT).as_posix(),
            'decoded_manifest': decode_report_path.relative_to(ROOT).as_posix(),
            'source_files': [source_entry, *files], 'index_metadata': manifest['index_metadata']}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--families', nargs='*', choices=sorted(PILOT_GROUPS), default=sorted(PILOT_GROUPS))
    args = parser.parse_args()
    if not CONFIG.is_file() or not INDEX.is_file():
        raise FileNotFoundError('Garrison game config or indexed game-assets.sqlite3 is unavailable')
    # Preserve earlier family intake when pilots run incrementally. Existing
    # manifests are provenance and must never disappear because a later run
    # requested only one family.
    prior_path = OUT / 'donors.json'
    prior = common.read(prior_path) if prior_path.is_file() else {}
    groups = dict(prior.get('families', {}))
    intake_errors = list(prior.get('intake_errors', []))
    # This abstract animatable archetype is not itself an authored static
    # geometry donor; concrete combined camel consumers below are decoded.
    abstract_candidate = {
        'family': 'camel_archer',
        'logical_path': 'art/civilizations/common/humans/archetypes/camel_archer/camel_archer.rgm',
        'error': 'Known nonblocking candidate failure: no same-stem RRGeometry provider; use indexed combined camel consumers.',
    }
    if abstract_candidate not in intake_errors:
        intake_errors.append(abstract_candidate)
    targets = common.read(OUT / 'targets.json') if (OUT / 'targets.json').is_file() else {'rows': []}
    target_model_map: dict[str, dict[str, list[dict[str, Any]]]] = {}
    target_rows = list(targets.get('rows', []))
    # The conditional official Regicide actor is outside the normal roster rows.
    # Walk all explicitly enumerated tier consumers so those reachable models
    # are covered without implying that absent routes are resolved.
    for conditional in targets.get('conditional_rows', []):
        target_rows.append(conditional)
    for target in target_rows:
        consumers = [target.get('age_tier_consumer') or {}]
        if target.get('family') == 'king':
            visual = target.get('current_visual_actor') or {}
            consumers.extend(visual.get('official_tier_route') or [])
            consumers.extend(target.get('current_age_visual_tier') or [])
            consumers.extend(target.get('official_tier_route') or [])
        for consumer in consumers:
            if not isinstance(consumer, dict):
                continue
            if 'consumer' in consumer and isinstance(consumer.get('consumer'), dict):
                consumer = consumer['consumer']
            for ref in consumer.get('model_refs', []):
                stem = str(ref.get('value', '')).replace('\\', '/')
                if not stem or '/archetypes/' in stem or 'parent_animator' in str(ref.get('field', '')):
                    continue
                logical_path = stem if stem.casefold().endswith('.rgm') else stem + '.rgm'
                ref_target = {
                    'age': target.get('age'), 'actor': target.get('actor') or target.get('current_actor'),
                    'actor_kind': target.get('actor_kind'), 'field': ref.get('field'),
                    'blueprint': consumer.get('blueprint'), 'tier_age': consumer.get('tier_age'),
                    'official_source': consumer.get('official_source'),
                }
                refs_for_path = target_model_map.setdefault(str(target.get('family')), {}).setdefault(logical_path, [])
                if ref_target not in refs_for_path:
                    refs_for_path.append(ref_target)
    # bindings/plan.json is the current actual-consumer source for source_model
    # paths; include all visual variants and upgrades even where the older
    # targets.json schema omitted age_tier_consumer.model_refs.
    plan_path = OUT / 'bindings/plan.json'
    if plan_path.is_file():
        plan = common.read(plan_path)
        for target in list(plan.get('rows', [])) + list(plan.get('conditional_rows', [])):
            family = str(target.get('family', ''))
            actor_obj = target.get('actor') if isinstance(target.get('actor'), dict) else {}
            actor = actor_obj.get('actor_pbg') or target.get('actor')
            for ref in target.get('consumed_visual_refs', []):
                stem = str(ref.get('source_model', '')).replace('\\', '/')
                if not stem:
                    continue
                logical_path = stem if stem.casefold().endswith('.rgm') else stem + '.rgm'
                ref_target = {
                    'age': ref.get('target_age', target.get('age')), 'actor': actor,
                    'field': ref.get('source_field'), 'consumer': ref.get('source_consumer'),
                    'blueprint': ref.get('source_consumer'), 'official_source': 'bindings/plan.json consumed_visual_refs',
                }
                refs_for_path = target_model_map.setdefault(family, {}).setdefault(logical_path, [])
                if ref_target not in refs_for_path:
                    refs_for_path.append(ref_target)
    donors = []
    for family in args.families:
        config = PILOT_GROUPS[family]
        entries = []
        exact_refs = target_model_map.get(family, {})
        model_paths = list(dict.fromkeys([*config['models'], *exact_refs.keys()]))
        for logical_path in model_paths:
            role = ('whole_unit' if '/animals/' in logical_path and '_combined_' in logical_path else
                    'mount' if '/animals/' in logical_path else
                    'rider' if family in ('horse_cavalry', 'camel_archer', 'scout', 'mehari', 'zenata', 'lancer') else 'body')
            age_match = re.search(r'age0([1-4])', logical_path)
            consumer_targets = exact_refs.get(logical_path, [])
            age = int(age_match.group(1)) if age_match else (consumer_targets[0]['age'] if consumer_targets else None)
            try:
                donor = decode_one(logical_path, family=family, role=role, age=age,
                                   consumer_targets=consumer_targets)
                entries.append(donor)
                donors.append(donor)
            except Exception as error:
                intake_errors.append({'family': family, 'logical_path': logical_path,
                                      'error': str(error)})
        if entries or family not in groups:
            groups[family] = {'archetype': config['archetype'], 'ages': config['ages'], 'donors': entries,
                              'exact_consumer_models': sorted(exact_refs),
                              'exact_consumer_row_count': len({(t['actor'], t['age']) for values in exact_refs.values() for t in values})}
    expected = ['villager', 'scout', 'trader', 'mehari', 'sanhaja', 'zenata',
                'archer', 'masmuda', 'lancer', 'imam', 'handgunner', 'king']
    covered = sorted(k for k, v in groups.items() if v.get('donors'))
    exact_missing = {
        family: sorted(set(paths) - {d.get('logical_path') for d in groups.get(family, {}).get('donors', [])})
        for family, paths in target_model_map.items()
        if set(paths) - {d.get('logical_path') for d in groups.get(family, {}).get('donors', [])}
    }
    blocking_errors = [e for e in intake_errors if e['family'] in expected]
    primary_coverage_complete = set(expected).issubset(covered) and not exact_missing and not blocking_errors
    def has_resolved_model_refs(row: dict[str, Any]) -> bool:
        consumer = row.get('age_tier_consumer')
        if isinstance(consumer, dict) and consumer.get('model_refs'):
            return True
        if row.get('family') == 'king':
            visual = row.get('current_visual_actor') or {}
            routes = list(visual.get('official_tier_route') or []) + list(row.get('current_age_visual_tier') or [])
            for route in routes:
                route_consumer = route.get('consumer') if isinstance(route, dict) else None
                if isinstance(route_consumer, dict) and route_consumer.get('model_refs'):
                    return True
        return False
    review_root = OUT / 'donor_previews'
    visual_reviews = {
        'archer_abbasid_age02': {
            'status': 'rendered_in_private_blender',
            'preview': (review_root / 'abb_archer_age02.png').relative_to(ROOT).as_posix(),
            'sha256': sha256(review_root / 'abb_archer_age02.png') if (review_root / 'abb_archer_age02.png').is_file() else None,
            'observation': 'Red turban/cloth wrap, layered gray robe over tan long tunic, cross-body strap and quiver; visually closer Saharan/Maghrebi option than plume-helmet Malian stock.',
            'rig_note': 'Same 48-bone index/name/parent hierarchy as Malian archer; local reference transforms differ. Preserve donor rig/SKIN and linked base_archer owner; no cross-rig SKIN transplant.',
        },
        'archer_sultanate_age02': {
            'status': 'rendered_in_private_blender',
            'preview': (review_root / 'sul_archer_age02.png').relative_to(ROOT).as_posix(),
            'sha256': sha256(review_root / 'sul_archer_age02.png') if (review_root / 'sul_archer_age02.png').is_file() else None,
            'observation': 'Cloth head covering, gray robe/tunic, red sash, green trousers; coherent regional candidate but less close than Abbasid robe silhouette.',
            'rig_note': 'Same 48-bone index/name/parent hierarchy as Malian archer; local reference transforms differ. Preserve donor rig/SKIN and linked base_archer owner; no cross-rig SKIN transplant.',
        },
        'mehari_abbasid_combined_age03': {
            'status': 'rendered_in_private_blender',
            'preview': (review_root / 'abb_mehari_age03.png').relative_to(ROOT).as_posix(),
            'sha256': sha256(review_root / 'abb_mehari_age03.png') if (review_root / 'abb_mehari_age03.png').is_file() else None,
            'observation': 'Exact consumed combined camel armor model; cream striped saddle blankets and tassels, with the rider visible under armor. Rider head is partly occluded at this view, so face/headgear is not visually assessed.',
            'rig_note': '92-bone combined camel rig, complete skin palette; keep the native combined rig, SKIN and base_camel_combined owner together.',
        },
        'sanhaja_abbasid_combined_age02': {
            'status': 'rendered_in_private_blender',
            'preview': (review_root / 'abb_camel_archer_age02.png').relative_to(ROOT).as_posix(),
            'sha256': sha256(review_root / 'abb_camel_archer_age02.png') if (review_root / 'abb_camel_archer_age02.png').is_file() else None,
            'observation': 'Exact consumed combined camel archer model; pale draped saddle cloth with hanging ties. Camera angle largely occludes the rider, so use this preview for mount and cloth assessment only.',
            'rig_note': '92-bone combined camel rig, complete skin palette; keep the native combined rig, SKIN and base_camel_combined owner together.',
        },
    }
    report = {
        'schema': 'berber050-donors/v1',
        'status': ('partial' if not primary_coverage_complete else
                   'candidate_errors' if intake_errors else 'passed'),
        'coverage': {'expected_primary_families': expected, 'covered_families': covered,
                     'missing_families': sorted(set(expected) - set(covered)),
                     'target_model_paths_by_family': {f: sorted(v) for f, v in target_model_map.items()},
                     'missing_exact_consumer_model_paths': exact_missing,
                     'primary_family_donor_coverage_complete': primary_coverage_complete,
                     'all_currently_resolved_target_model_refs_decoded': not exact_missing,
                     'playable_roster_binding_closure': 'pending_schema_reconciliation; current targets.json omits age_tier_consumer.model_refs on some ordinary rows',
                     'target_binding_closure_complete': False,
                     'nonblocking_candidate_errors': [e for e in intake_errors if e not in blocking_errors],
                     'target_rows_without_model_refs': [
                         {'family': r.get('family'), 'age': r.get('age'), 'actor': r.get('actor'),
                          'reason': 'age_tier_consumer.model_refs empty, absent, or not mapped by current targets schema'}
                         for r in target_rows if r.get('family') in expected and not has_resolved_model_refs(r)],
                     'target_rows_without_model_ref_count': sum(
                        1 for r in target_rows if r.get('family') in expected and not has_resolved_model_refs(r)),
                     'note': 'primary donor coverage and all currently resolved consumer refs are separate from actor/binding closure; rows without usable refs are listed pending targets-schema/roster reconciliation, not treated as donor decode failures. candidate_errors are nonblocking abstract donor lookup failures, not decoder failures on concrete consumers.'},
        'scope': 'native model extraction and Garrison static decode only; no asset authoring/cook/package',
        'game_root': common.read(CONFIG)['game_root'],
        'game_index': str(INDEX),
        'index_schema': 'garrison.game-asset-index/v1',
        'cache_root': CACHE.relative_to(ROOT).as_posix(),
        'families': groups,
        'visual_reviews': visual_reviews,
        'donor_count': sum(len(v.get('donors', [])) for v in groups.values()),
        'unique_donor_ids': len({d['donor_id'] for v in groups.values() for d in v.get('donors', [])}),
        'intake_errors': intake_errors,
        'native_cook': 'not run',
    }
    common.write(OUT / 'donors.json', report)
    print(json.dumps({'status': report['status'], 'families': list(groups),
                      'donor_count': report['donor_count'], 'manifest': str(OUT / 'donors.json')}, indent=2))


if __name__ == '__main__':
    main()
