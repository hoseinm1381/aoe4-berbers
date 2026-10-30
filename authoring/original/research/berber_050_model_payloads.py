"""Verify native variant readbacks and replace only admitted authored geometry."""
from __future__ import annotations
import argparse
import os
import math
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from berber_050_common import ART, ARCH, EXT, OUT, ROOT, read, run, sha, write
from berber_050_project import PROJECT, register
sys.path.insert(0, str(EXT))
from garrison_shared import model_variants as mv
from berber_050_materials import inventory as material_inventory, remap_albedos, canonical

# These official resources are skinned merge attachments, not standalone
# animated objects. Their native contract has no per-model RGO. The owning
# actor supplies animation; use the supported parent ONLY to cook PNG textures.
ATTACHMENT_CARRIERS = {
    'art/civilizations/abbasids/animals/abb_camel_combined_armor_age03_upgrade/abb_camel_combined_armor_age03_upgrade':
    'art/civilizations/abbasids/animals/abb_camel_combined_armor_age03/abb_camel_combined_armor_age03',
    'art/civilizations/abbasids/animals/abb_camel_combined_bow_age02_upgrade/abb_camel_combined_bow_age02_upgrade':
    'art/civilizations/abbasids/animals/abb_camel_combined_bow_age02/abb_camel_combined_bow_age02',
}


def cook_source(row):
    source = row['official_donor_rgm'].removesuffix('.rgm')
    return ATTACHMENT_CARRIERS.get(source, source)


def records(value):
    if isinstance(value, dict):
        if 'private_variant_name' in value:
            yield value
        else:
            for key, child in value.items():
                if key not in {'excluded_probes', 'rejected_probes'} and not key.startswith('rejected_'):
                    yield from records(child)
    elif isinstance(value, list):
        for child in value:
            yield from records(child)


def absolute(path):
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def source_geometry(manifest_path, manifest):
    recorded = Path(manifest['geometry']['source']['path'])
    if recorded.is_file():
        return recorded
    logical = Path(manifest['request']['logical_path'].replace('\\', '/'))
    fallback = manifest_path.parent / 'source' / logical.with_suffix('.rrgeom')
    if not fallback.is_file():
        raise FileNotFoundError(recorded)
    return fallback


def collect(manifests):
    models = {}
    for path in manifests:
        for row in records(read(path)):
            name = row['private_variant_name']
            if name in models and row != models[name]:
                raise ValueError(f'Conflicting authored model: {name}')
            for key in ('decoded_manifest', 'geometry_recipe', 'geometry_report', 'authored_rrgeom', 'editable_blend', 'authored_albedo'):
                if sha(absolute(row[key])) != row[key + '_sha256']:
                    raise ValueError(f'Changed author input {name}:{key}')
            for key in ('preview_donor_lod1', 'preview_candidate_lod1', 'preview_team_red', 'preview_team_blue'):
                if not absolute(row[key]).is_file() or sha(absolute(row[key])) != row[key + '_sha256']:
                    raise ValueError(f'Missing or changed visual review {name}:{key}')
            for atlas in row.get('albedo_variants', []):
                if sha(absolute(atlas['authored_png'])) != atlas['sha256']:
                    raise ValueError(f'Changed authored atlas {name}:{atlas["source_texture"]}')
            models[name] = row
    if not models:
        raise ValueError('No authored model records')
    return models


def atlas_jobs(row):
    entries = row.get('albedo_variants', [])
    if not entries:
        return []
    seen = set()
    jobs = []
    main_found = False
    for index, atlas in enumerate(entries, 1):
        source = canonical(atlas['source_texture'])
        if source in seen:
            raise ValueError('Native atlas mapped twice')
        seen.add(source)
        image = absolute(atlas['authored_png'])
        if sha(image) != atlas['sha256']:
            raise ValueError('Atlas input changed')
        is_main = image.resolve() == absolute(row['authored_albedo']).resolve()
        name = row['private_variant_name'] if is_main else row['private_variant_name'] + f'_atlas{index:02}'
        if is_main:
            if main_found:
                raise ValueError('Main atlas ambiguously reused for different native textures')
            main_found = True
        jobs.append({'source_texture': source, 'image': image, 'variant_name': name,
            'private_texture': f'art/scenario/garrison/{PROJECT.name}/{name}/albedotexture.rrtex'})
    if not main_found:
        raise ValueError('Main authored_albedo missing from per-atlas map')
    return jobs


def register_models(models):
    for name, row in models.items():
        source = row['official_donor_rgm'].removesuffix('.rgm')
        register(name, cook_source(row), absolute(row['authored_albedo']), expected_previous_source=source)
        for atlas in atlas_jobs(row):
            if atlas['variant_name'] != name:
                register(atlas['variant_name'], cook_source(row), atlas['image'], expected_previous_source=source)


def native_stock(row):
    manifest_path = absolute(row['decoded_manifest'])
    manifest = read(manifest_path)
    geometry = source_geometry(manifest_path, manifest)
    if sha(geometry) != row['native_source_rrgeom_sha256']:
        raise ValueError('Donor geometry changed')
    stock = {suffix: geometry.with_suffix(suffix).read_bytes() for suffix in ('.rgm', '.rrgeom', '.rrmaterial')}
    if sha(geometry.with_suffix('.rgm')) != row['official_donor_rgm_sha256']:
        raise ValueError('Native donor model does not match recorded provenance')
    if sha(geometry.with_suffix('.rrmaterial')) != manifest['material']['source']['sha256']:
        raise ValueError('Native donor material differs from pinned original projection')
    # decode-static does not retain RGO. Keep one exact native RGO beside its
    # original donor RGM in the reusable hash-keyed cache, with provenance.
    logical = row['official_donor_rgm'].removesuffix('.rgm') + '.rgo'
    dest = manifest_path.parents[2] / 'source' / Path(logical).name
    provenance = dest.with_suffix('.rgo.provenance.json')
    index = Path(os.environ['LOCALAPPDATA']) / 'Garrison/Kit/game-assets.sqlite3'
    with closing(sqlite3.connect('file:' + index.as_posix() + '?mode=ro', uri=True)) as db:
        rows = db.execute('SELECT archive_path FROM resolved_assets WHERE logical_path=?', (logical,)).fetchall()
    proof = verify_rig(manifest)
    if not rows and cook_source(row) != row['official_donor_rgm'].removesuffix('.rgm'):
        if dest.exists():
            raise ValueError('Native attachment has no RGO, but an unqualified cached companion exists')
        proof['native_rgo_contract'] = 'official skinned merge attachment has no own RGO; owning native actor animator preserved'
        proof['texture_cook_carrier'] = cook_source(row)
        return stock, proof
    if len(rows) != 1:
        raise ValueError(f'Native RGO source ambiguous or absent: {logical}')
    if not dest.exists():
        run(ARCH, 'extract-member', rows[0][0], logical, dest)
        write(provenance, {'logical_path': logical, 'archive': rows[0][0], 'sha256': sha(dest)})
    elif provenance.exists() and sha(dest) != read(provenance)['sha256']:
        raise ValueError('Cached native RGO changed')
    stock['.rgo'] = dest.read_bytes()
    proof['native_rgo_contract'] = 'exact original RGO retained'
    return stock, proof


def verify_rig(manifest):
    skeleton = manifest['skeleton']
    if (skeleton.get('status') != 'hierarchy_decoded'
        or manifest['rig_palette_binding']['status'] != 'complete'
        or manifest['rig_projection']['status'] != 'complete'
        or skeleton['rest_pose']['status'] != 'local_bind_transforms_decoded'):
        raise ValueError('Incomplete native skeleton/rest/skin palette projection')
    count = skeleton['bone_count']
    if count != len(skeleton['bones']):
        raise ValueError('Native skeleton count differs from decoded bones')
    for index, bone in enumerate(skeleton['bones']):
        if bone['index'] != index or not -1 <= bone['parent_index'] < count:
            raise ValueError('Invalid native skeleton hierarchy')
        for key in ('local_reference_transform', 'global_reference_transform'):
            if not all(math.isfinite(x) for values in bone[key].values() for x in values):
                raise ValueError('Nonfinite native bind transform')
    for palette in skeleton['skin_palettes']:
        if (palette['status'] != 'bind_palette_decoded'
            or palette['inverse_bind_validation']['status'] != 'matched'
            or palette['skln_crosscheck']['status'] != 'matched'):
            raise ValueError('Native bind matrices do not match skeleton palette')
        for bone in palette['bones']:
            if not 0 <= bone['skeleton_index'] < count:
                raise ValueError('Skin palette references an invalid native bone')
            if not all(math.isfinite(x) for values in bone['inverse_bind_transform'].values() for x in values):
                raise ValueError('Nonfinite inverse bind transform')
    vertices = 0
    groups = 0
    for group in manifest['geometry']['groups']:
        if group['stream'] != 'UnitDataStream':
            continue
        rig = group['rig_projection']
        skin = group['skin_projection']
        if rig['status'] != 'decoded' or skin['status'] != 'palette_indices_and_weights_decoded':
            raise ValueError('Native skinned LOD lacks bound weights')
        if not len(group['positions']) == len(group['skin_weights']) == len(group['skin_indices']):
            raise ValueError('Native vertex/weight/index counts differ')
        for indices, weights in zip(group['skin_indices'], group['skin_weights']):
            if not all(math.isfinite(w) and 0 <= w <= 1 for w in weights) or abs(sum(weights) - 1) > 0.00001:
                raise ValueError('Native skin weights are not normalized')
            if any(w > 0 and not 0 <= i < rig['palette_bone_count'] for i, w in zip(indices, weights)):
                raise ValueError('Native weighted vertex references an invalid palette bone')
        vertices += len(group['positions'])
        groups += 1
    if not groups:
        raise ValueError('Complete animated unit must retain skinned native LODs')
    return {'bone_count': count, 'qualified_palettes': len(skeleton['skin_palettes']),
        'skinned_lod_groups': groups, 'normalized_weight_vertices': vertices,
        'native_inverse_bind_and_skeleton_crosscheck': 'matched',
        'socket_and_animation_bytes': 'native RGM/RGO template retained; match clearance pending'}


def approve(models, names):
    path = OUT / 'art-approvals.json'
    approvals = read(path) if path.exists() else {}
    for name in names:
        row = models[name]
        approvals[name] = {'status': 'source_art_accepted',
            'comparison': 'Matched LOD1 silhouette, clothing and equipment reviewed; bounded regional redesign including geometry, within qualitative 10-50% design scope.',
            'geometry_sha256': row['authored_rrgeom_sha256'],
            'albedo_sha256': row['authored_albedo_sha256'],
            'albedo_atlas_sha256': {a['source_texture']: sha(a['image']) for a in atlas_jobs(row)},
            'donor_preview_sha256': sha(absolute(row['preview_donor_lod1'])),
            'candidate_preview_sha256': sha(absolute(row['preview_candidate_lod1'])),
            'native_appearance_animation_colour': 'pending'}
    write(path, approvals)


def validate_approvals(models):
    approvals = read(OUT / 'art-approvals.json')
    for name, row in models.items():
        approval = approvals.get(name, {})
        expected = (row['authored_rrgeom_sha256'], row['authored_albedo_sha256'],
                    sha(absolute(row['preview_donor_lod1'])), sha(absolute(row['preview_candidate_lod1'])))
        actual = tuple(approval.get(k) for k in ('geometry_sha256', 'albedo_sha256', 'donor_preview_sha256', 'candidate_preview_sha256'))
        if actual != expected or approval.get('status') != 'source_art_accepted':
            raise ValueError(f'Unreviewed or changed source art: {name}')
        if approval.get('albedo_atlas_sha256', {}) != {a['source_texture']: sha(a['image']) for a in atlas_jobs(row)}:
            raise ValueError(f'Unreviewed or changed additional albedo atlas: {name}')
    return True


def prepare(models, cook_path):
    validate_approvals(models)
    cook = read(cook_path)
    if cook['status'] != 'passed' or cook['live_reload'] is not False:
        raise ValueError('Successful Live Reload-off cook required')
    archive = Path(cook['cook']['archive'])
    if sha(archive) != cook['cook']['sha256']:
        raise ValueError('Cook archive bytes changed')
    inventory = __import__('json').loads(run(ARCH, 'list', archive, '--verify'))
    if not inventory['archive']['verification']['verified']:
        raise ValueError('Native cook archive failed integrity verification')
    readback = OUT / 'integration' / ('art-cook-readback-' + sha(archive)[:12])
    if not readback.exists():
        run(ARCH, 'unpack', archive, '--output', readback)
    variants = {r['name']: r for r in read(PROJECT / 'mod-project.json')['model_variants']}
    auxiliaries = {j['variant_name'] for r in models.values() for j in atlas_jobs(r)} - set(models)
    if set(variants) != set(models) | auxiliaries:
        raise ValueError('Registered variants differ from the exact authored roster resources')
    approvals = read(OUT / 'art-approvals.json')
    expected_art = {}
    omitted_carrier_models = set()
    model_proofs = []
    for name, row in models.items():
        approval = approvals.get(name, {})
        expected_approval = (row['authored_rrgeom_sha256'], row['authored_albedo_sha256'],
                             sha(absolute(row['preview_donor_lod1'])), sha(absolute(row['preview_candidate_lod1'])))
        actual_approval = tuple(approval.get(k) for k in ('geometry_sha256', 'albedo_sha256', 'donor_preview_sha256', 'candidate_preview_sha256'))
        if actual_approval != expected_approval or approval.get('status') != 'source_art_accepted':
            raise ValueError(f'Unreviewed or changed source art: {name}')
        if approval.get('albedo_atlas_sha256', {}) != {a['source_texture']: sha(a['image']) for a in atlas_jobs(row)}:
            raise ValueError(f'Unreviewed or changed additional albedo atlas: {name}')
        stock, rig_proof = native_stock(row)
        attachment_only = '.rgo' not in stock
        cook_stock = stock
        if attachment_only:
            parents = [r for r in models.values() if r['official_donor_rgm'].removesuffix('.rgm') == cook_source(row)]
            if not parents or not atlas_jobs(row):
                raise ValueError('Qualified attachment needs exact native parent texture carrier and explicit atlas mapping')
            cook_stock, _ = native_stock(parents[0])
        if variants[name]['source'].replace('\\', '/') != cook_source(row):
            raise ValueError('Registered cook donor differs from qualified native texture carrier')
        expected = mv.build(variants[name], cook_stock, PROJECT.name)
        for member, data in expected.items():
            cooked = readback / member
            if not cooked.exists() or cooked.read_bytes() != data:
                raise ValueError(f'Native variant readback differs from exact donor/template transformation: {member}')
            if attachment_only and member.endswith('.rgo'):
                omitted_carrier_models.add(member)
            else:
                expected_art[member] = cooked
        stem = f'art/scenario/garrison/{PROJECT.name}/{name}/{name}'
        if attachment_only:
            original_stem = row['official_donor_rgm'].removesuffix('.rgm')
            data = mv.rewrite_model_path(stock['.rgm'], original_stem, stem)
            if mv.rewrite_model_path(data, stem, original_stem) != stock['.rgm']:
                raise ValueError('Native attachment model path rewrite failed exact roundtrip')
            model_path = OUT / 'integration/model-payloads' / (stem + '.rgm')
            model_path.parent.mkdir(parents=True, exist_ok=True)
            model_path.write_bytes(data)
            expected_art[stem + '.rgm'] = model_path
        material = readback / (stem + '.rrmaterial')
        jobs = atlas_jobs(row)
        native_atlases = {canonical(value) for _, pairs in material_inventory(stock['.rrmaterial'])
                          for slot, value in pairs if slot == 'albedoTexture'}
        material_proof = None
        if jobs:
            mappings = {}
            for atlas in jobs:
                if atlas['source_texture'] not in native_atlases:
                    raise ValueError(f'Authored atlas not native to this model: {name}')
                carrier = atlas['variant_name']
                if carrier != name:
                    carrier_expected = mv.build(variants[carrier], cook_stock, PROJECT.name)
                    for member, data in carrier_expected.items():
                        if (readback / member).read_bytes() != data:
                            raise ValueError(f'Native atlas carrier readback differs: {carrier}')
                        omitted_carrier_models.add(member)
                texture = atlas['private_texture']
                if not (readback / texture).is_file():
                    raise ValueError(f'Cooked atlas texture missing: {texture}')
                expected_art[texture] = readback / texture
                mappings[atlas['source_texture']] = texture.replace('/', '\\')
            data, material_proof = remap_albedos(stock['.rrmaterial'], mappings)
            material = OUT / 'integration/material-payloads' / (stem + '.rrmaterial')
            material.parent.mkdir(parents=True, exist_ok=True)
            material.write_bytes(data)
            expected_art[stem + '.rrmaterial'] = material
        elif len(native_atlases) != 1:
            raise ValueError(f'Multiple native albedo atlases need an explicit per-atlas map: {name}')
        before = mv.material_slots(stock['.rrmaterial'])
        after = mv.material_slots(material.read_bytes())
        for slot, value in before['textures'].items():
            if slot != 'albedoTexture' and after['textures'].get(slot) != value:
                raise ValueError(f'Native material contract changed: {name}:{slot}')
        if after['parameters'] != before['parameters']:
            raise ValueError(f'Native shader parameters changed: {name}')
        if 'patternTex' not in after['textures']:
            raise ValueError(f'Native dynamic owner-color pattern missing: {name}')
        if not jobs:
            albedo = after['textures']['albedoTexture'].replace('\\', '/')
            if not albedo.startswith(f'art/scenario/garrison/{PROJECT.name}/') or not (readback / albedo).is_file():
                raise ValueError(f'Cooked private albedo absent: {name}:{albedo}')
            expected_art[albedo] = readback / albedo
        geometry = absolute(row['authored_rrgeom'])
        if sha(geometry) == row['native_source_rrgeom_sha256']:
            raise ValueError(f'Unmodified stock geometry: {name}')
        proof = read(absolute(row['geometry_report']))
        if (proof['source_sha256'] != row['native_source_rrgeom_sha256']
            or proof['output_sha256'] != sha(geometry)
            or proof['recipe_sha256'] != row['geometry_recipe_sha256']):
            raise ValueError(f'Authored native geometry proof stale: {name}')
        if not proof['groups'] or not all(g['within_original_native_bounds'] for g in proof['groups']):
            raise ValueError(f'Native geometry bounds not verified: {name}')
        expected_art[stem + '.rrgeom'] = geometry
        model_proofs.append({'variant': name, 'donor_sha256': row['official_donor_rgm_sha256'],
            'native_rgm_rgo_material_exact_template_match': not attachment_only,
            'native_attachment_rgm_exact_path_roundtrip': attachment_only,
            'native_attachment_without_own_rgo': attachment_only,
            'texture_only_cook_carrier': cook_source(row) if attachment_only else None,
            'native_skeleton_skin_uv_topology_and_lods': 'preserved by bounded native vertex-stream authoring',
            'owner_colour_contract': 'native_dynamic', 'authored_geometry_sha256': sha(geometry),
            'material_inputs_except_albedo_identical': True, 'per_atlas_material_proof': material_proof,
            'rig_weight_bind_proof': rig_proof,
            'native_runtime': 'pending'})
    cooked_art = {r['path'] for r in inventory['members'] if r['path'].startswith('art/')}
    if cooked_art != set(expected_art) | omitted_carrier_models:
        raise ValueError(f'Cooked art dependency closure differs: extra={sorted(cooked_art-set(expected_art))}, missing={sorted(set(expected_art)-cooked_art)}')
    payloads = [{'member': member, 'file': str(path), 'sha256': sha(path)} for member, path in sorted(expected_art.items())]
    result = {'status': 'passed', 'payloads': payloads, 'models': model_proofs, 'cook_readback': str(readback)}
    write(OUT / 'integration/model-payloads.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifests', nargs='+', type=Path)
    parser.add_argument('--register', action='store_true')
    parser.add_argument('--approve', nargs='*', default=[])
    parser.add_argument('--cook', type=Path)
    args = parser.parse_args()
    models = collect(args.manifests)
    if args.approve:
        approve(models, args.approve)
    if args.register:
        register_models(models)
    if args.cook:
        prepare(models, args.cook)
    print(f'Author model records verified: {len(models)}')
