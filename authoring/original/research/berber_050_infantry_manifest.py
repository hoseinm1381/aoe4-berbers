"""Rebuild the hash-pinned, source-only Berber 0.5.0 infantry art ledger."""
from __future__ import annotations

import json
from pathlib import Path

from berber_050_common import ART, OUT, ROOT, read, sha, write


SOURCES = [
    ('archer', 2, 'abb_archer_age2_pilot'),
    ('archer', 3, 'abb_archer_age3_candidate'),
    ('archer', 4, 'abb_archer_age4_candidate'),
    ('masmuda', 2, 'masmuda_age2_candidate'),
    ('masmuda', 3, 'masmuda_age3_candidate'),
    ('masmuda', 4, 'masmuda_age4_candidate'),
    ('handgunner', 4, 'handgunner_age4_candidate'),
]


def rel(path: Path) -> str:
    # Keep the documented workspace output junction spelling, rather than
    # resolving it to the external F: storage target.
    return str(path.absolute().relative_to(ROOT.absolute()))


def main() -> None:
    donors = read(OUT / 'donors.json')
    rows = {'archer': [], 'masmuda': [], 'handgunner': []}
    for family, age, name in SOURCES:
        folder = ART / 'pilots' / name
        recipe_path = folder / 'recipe.json'
        recipe = read(recipe_path)
        manifest_path = ROOT / recipe['manifest']
        manifest = read(manifest_path)
        logical = recipe['logical_path']
        donor = next((d for grouping in donors['families'].values()
                      for d in grouping.get('donors', [])
                      if d.get('logical_path') == logical), None)
        if donor is None:
            raise ValueError(f'Official donor provenance unavailable: {logical}')
        geometry_report_path = folder / 'geometry-report.json'
        geometry_report = read(geometry_report_path)
        if (sha(manifest_path) != recipe['manifest_sha256']
                or manifest['request']['logical_path'] != logical
                or geometry_report['recipe_sha256'] != sha(recipe_path)
                or geometry_report['output_sha256'] != sha(folder / f'{name}.rrgeom')):
            raise ValueError(f'Stale donor, recipe or native geometry: {name}')
        if not all(group['within_original_native_bounds'] for group in geometry_report['groups']):
            raise ValueError(f'Native bounds exceeded: {name}')
        source_sha = manifest['geometry']['source']['sha256']
        if recipe['geometry_sha256'] != source_sha:
            raise ValueError(f'Native RRGeom identity changed: {name}')
        albedo_name = recipe.get('preview_albedo', 'indigo-underrobe-albedo.png')
        files = {
            'geometry_recipe': recipe_path,
            'authored_rrgeom': folder / f'{name}.rrgeom',
            'editable_blend': folder / f'{name}.blend',
            'authored_albedo': folder / albedo_name,
        }
        for path in files.values():
            if not path.is_file():
                raise FileNotFoundError(path)
        previews = {
            'preview_donor_lod1': folder / 'textured-donor.png',
            'preview_candidate_lod1': folder / 'textured-candidate.png',
            'preview_team_red': folder / 'textured-team-red.png',
            'preview_team_blue': folder / 'textured-team-blue.png',
        }
        for path in previews.values():
            if not path.is_file():
                raise FileNotFoundError(path)
        row = {
            'family': family,
            'age': age,
            'private_variant_name': f'{family}_age0{age}',
            'official_donor_rgm': logical,
            'official_donor_rgm_sha256': donor['native_resource_sha256'],
            'decoded_manifest': rel(manifest_path),
            'decoded_manifest_sha256': sha(manifest_path),
            'native_source_rrgeom_sha256': source_sha,
        }
        for key, path in files.items():
            row[key] = rel(path)
            row[f'{key}_sha256'] = sha(path)
        row['geometry_report'] = rel(geometry_report_path)
        row['geometry_report_sha256'] = sha(geometry_report_path)
        for key, path in previews.items():
            row[key] = rel(path)
            row[f'{key}_sha256'] = sha(path)
        row['native_material_cook'] = ('passed private pilot' if family == 'archer' and age == 2
                                       else 'pending root batch cook')
        row['native_animation'] = 'unverified'
        rows[family].append(row)
    report = {
        'schema': 'berber-050-infantry-art/v1',
        'status': 'seven_source_directions_approved_native_runtime_unverified',
        **rows,
        'source_cook_vs_runtime': ('Source geometry, packed editable Blender files, protected albedos and '
                                   'red/blue preview renders are prepared. Archer II has a private native '
                                   'cook/geometry splice proof; final cook, consumer bindings and native '
                                   'animation remain separate gates.'),
    }
    write(ART / 'infantry-manifest.json', report)
    print(json.dumps({'status': report['status'], 'entries': sum(map(len, rows.values())),
                      'manifest': rel(ART / 'infantry-manifest.json'),
                      'sha256': sha(ART / 'infantry-manifest.json')}, indent=2))


if __name__ == '__main__':
    main()
