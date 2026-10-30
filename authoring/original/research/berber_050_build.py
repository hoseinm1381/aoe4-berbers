"""Rebuild the fully admitted private 0.5.0 candidate on packaged 0.4.0."""
from __future__ import annotations
import argparse
from pathlib import Path
from berber_050_common import ART, ARCH, BASE, BASE_SHA, CORE, EDITOR, OUT, ROOT, read, sha, write
from berber_050_admission import EXPECTED, admit_coverage
from berber_050_project import PROJECT, configuration, cook
from berber_050_model_payloads import (absolute, atlas_jobs, collect, prepare, register_models,
                                       validate_approvals, native_stock, source_geometry, cook_source)
from berber_050_native_bindings import candidate_manifest, prepare_actors, register_bindings
from berber_050_semantics import attachments, final_report
from berber_050_compose import compose


MANIFESTS = [ART / path for path in (
    'infantry-manifest.json', 'civilian/villager/villager-manifest.json',
    'civilian/imam/imam-manifest.json', 'civilian/king/king-manifest.json',
    'civilian/trader/trader-manifest.json', 'mounted/mounted-manifest.json',
    'mounted_upgrades/upgrades-manifest.json')]


def qualified_models():
    models = collect(MANIFESTS)
    routes = {r['private_variant_name']: r for r in read(OUT / 'bindings/model-routes.json')['models']}
    if set(models) != set(routes) or len(models) != 49:
        raise ValueError('Full native route/resource closure requires exactly the 49 admitted art resources')
    for name, row in models.items():
        if (row['family'], row['age']) != (routes[name]['family'], routes[name]['age']):
            raise ValueError(f'Art family/age differs from exact native route: {name}')
        source = routes[name]['source_model'] + '.rgm'
        if row['official_donor_rgm'] != source:
            allowed = {
                'villager': f"art/civilizations/abbasids/humans/abb_villager_male_age0{row['age']}/abb_villager_male_age0{row['age']}.rgm",
                'archer': f"art/civilizations/abbasids/humans/abb_ranged_bow_age0{row['age']}/abb_ranged_bow_age0{row['age']}.rgm",
                'imam': f"art/civilizations/sultanate/humans/sul_infantry_monk_age0{row['age']}/sul_infantry_monk_age0{row['age']}.rgm",
                'king': 'art/civilizations/abbasids/humans/abb_infantry_armor_age04/abb_infantry_armor_age04.rgm',
            }
            if row['official_donor_rgm'] != allowed.get(row['family']):
                raise ValueError(f'Unqualified alternative native donor: {name}')
    native_proofs = []
    for name, row in models.items():
        stock, proof = native_stock(row)
        if '.rgo' not in stock and not any(r['official_donor_rgm'].removesuffix('.rgm') == cook_source(row) for r in models.values()):
            raise ValueError(f'No qualified texture carrier for native merge attachment: {name}')
        native_proofs.append({'variant': name, **proof})
    write(OUT / 'all-model-source-rig-proof.json', {'status': 'passed', 'models': native_proofs,
          'native_animation': 'pending', 'scope': 'native skeleton, weights, rest/palette and exact RGO-or-merge-attachment contract'})
    return models


def freeze_inputs(models):
    write(OUT / 'final-project-configuration.json', configuration())
    paths = set(MANIFESTS)
    for row in models.values():
        manifest_path = absolute(row['decoded_manifest'])
        geometry = source_geometry(manifest_path, read(manifest_path))
        paths.update(geometry.with_suffix(suffix) for suffix in ('.rgm', '.rrgeom', '.rrmaterial'))
        rgo = manifest_path.parents[2] / 'source' / Path(row['official_donor_rgm']).with_suffix('.rgo').name
        if rgo.exists():
            paths.add(rgo)
        for key in ('decoded_manifest', 'geometry_recipe', 'geometry_report', 'authored_rrgeom',
                    'editable_blend', 'authored_albedo', 'preview_donor_lod1',
                    'preview_candidate_lod1', 'preview_team_red', 'preview_team_blue'):
            paths.add(absolute(row[key]))
        for atlas in atlas_jobs(row):
            paths.add(atlas['image'])
            record = next(r for r in read(PROJECT / 'mod-project.json')['model_variants']
                          if r['name'] == atlas['variant_name'])
            copied = PROJECT / 'project/source' / record['textures']['albedoTexture']
            if sha(copied) != sha(atlas['image']):
                raise ValueError('Registered copied texture differs from pinned authoring PNG')
            paths.add(copied)
        if not atlas_jobs(row):
            record = next(r for r in read(PROJECT / 'mod-project.json')['model_variants']
                          if r['name'] == row['private_variant_name'])
            copied = PROJECT / 'project/source' / record['textures']['albedoTexture']
            if sha(copied) != row['authored_albedo_sha256']:
                raise ValueError('Registered texture differs from authored input')
            paths.add(copied)
    paths.update((OUT / relative) for relative in (
        'final-project-configuration.json', 'bindings/final-candidates.json',
        'bindings/model-routes.json', 'bindings/actor-payloads.json', 'art-approvals.json',
        'baseline-preservation.json', 'baseline-member-sha256.json'))
    paths.update(ROOT / 'research' / p.name for p in (ROOT / 'research').glob('berber_050*.py'))
    paths.update(ART.rglob('*.py'))
    paths.update(ROOT / 'Design/asset_overhaul' / name for name in
                 ('BERBER_050_PLAN.md', 'BERBER_050_ART_BRIEF.md', 'BERBER_050_REBUILD.md'))
    paths.update((CORE, ARCH, EDITOR))
    snapshot = {str(path.resolve()): sha(path) for path in sorted(paths)}
    write(OUT / 'final-source-hashes.json', snapshot)
    return OUT / 'final-source-hashes.json'


def coverage(models, model_proofs):
    proofs = {r['variant']: r for r in model_proofs['models']}
    rows = []
    for family, ages in EXPECTED.items():
        for age in ages:
            if family == 'tuareg':
                rows.append({'family': family, 'age': age, 'status': 'preserved_accepted',
                    'source': 'packaged 0.4.0', 'baseline_sha256': BASE_SHA,
                    'native_acceptance': 'accepted existing art; baseline actor/model members preserved'})
                continue
            selected = [r for r in models.values() if r['family'] == family and r['age'] == age]
            if not selected or any(r['private_variant_name'] not in proofs for r in selected):
                raise ValueError(f'Missing native model readback for {family} age {age}')
            resources = []
            for row in selected:
                name = row['private_variant_name']
                proof = proofs[name]
                resources.append({'variant': name, 'stem': f'art/scenario/garrison/{PROJECT.name}/{name}/{name}',
                    'donor': row['official_donor_rgm'], 'donor_sha256': row['official_donor_rgm_sha256'],
                    'geometry_sha256': row['authored_rrgeom_sha256'],
                    'rig_weight_bind_proof': proof['rig_weight_bind_proof'],
                    'per_atlas_material_proof': proof['per_atlas_material_proof'],
                    'owner_colour_contract': proof['owner_colour_contract']})
            rows.append({'family': family, 'age': age, 'status': 'export_verified',
                'geometry_modified': True, 'donor_sha256': selected[0]['official_donor_rgm_sha256'],
                'owner_colour_contract': 'native_dynamic', 'resources': resources,
                'export_route': 'native skinned RRGeom edit + original RGM/material and exact native RGO-or-merge-attachment contract; per-atlas texture cook',
                'design_review': 'matched source comparisons accepted; 10-50% qualitative visible design target, not vertex percentage',
                'native_appearance_animation_player_colour': 'pending'})
    result = {'status': 'passed', 'scope': 'native format/resource coverage; native appearance, animation and player colour pending', 'version': '0.5.0',
        'family_count': len(EXPECTED), 'family_age_entries': len(rows), 'authored_resources': len(models),
        'rows': rows, 'excluded': ['siege', 'naval'],
        'extra_reachable_actor': 'Malian Regicide King I-IV from official per-race deployment',
        'native_acceptance': 'pending user testing'}
    admit_coverage(result)
    write(OUT / 'coverage.json', result)
    return result


def build(*, do_cook):
    if sha(BASE) != BASE_SHA:
        raise ValueError('Authoritative packaged 0.4.0 changed')
    bindings = candidate_manifest()
    prepare_actors(bindings)
    models = qualified_models()
    validate_approvals(models)
    if do_cook:
        register_bindings(bindings)
        register_models(models)
        frozen = freeze_inputs(models)
        cook(frozen)
    else:
        frozen = OUT / 'final-source-hashes.json'
    native_models = prepare(models, OUT / 'art-cook.json')
    attachments(OUT / 'art-cook.json')
    final_report(OUT / 'integration/model-payloads.json', OUT / 'bindings/actor-payloads.json',
                 OUT / 'integration/attachment-payloads.json')
    coverage(models, native_models)
    result = compose(OUT / 'coverage.json', OUT / 'art-cook.json', frozen,
        OUT / 'integration/gameplay-semantics.json', [OUT / 'integration/model-payloads.json',
        OUT / 'bindings/actor-payloads.json', OUT / 'integration/attachment-payloads.json'])
    from berber_050_review import generate
    review = generate(MANIFESTS, coverage=OUT / 'coverage.json',
        composition=OUT / 'integration/composition-report.json', cook=OUT / 'art-cook.json')
    write(OUT / 'final-review-artifacts.json', review)
    print('050_COMPLETE_CANDIDATE_COMPOSITION', result['archive_sha256'])
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cook', action='store_true', help='register complete sources, freeze and freshly cook; otherwise reuse only hash-current final cook')
    args = parser.parse_args()
    build(do_cook=args.cook)
