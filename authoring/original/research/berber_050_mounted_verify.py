"""Verify mounted source handoff without asserting native cook or match success."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageChops

from berber_050_common import ROOT, ART, sha


def main():
    manifest = json.loads((ART/'mounted/mounted-manifest.json').read_text(encoding='utf8'))
    routes = json.loads((ROOT/'output/berber_update_0_5_0/bindings/model-routes.json').read_text(encoding='utf8'))['models']
    expected = {r['private_variant_name']:r for r in routes
                if r['family'] in {'scout','mehari','sanhaja','zenata','lancer'} and r['state']=='body'}
    rows = manifest['variants']
    actual = {r['private_variant_name']:r for r in rows}
    if len(rows)!=len(actual) or set(actual)!=set(expected):
        raise ValueError(f'Route closure mismatch: missing={set(expected)-set(actual)}, extra={set(actual)-set(expected)}')
    for name,row in actual.items():
        route = expected[name]
        if row['official_donor_rgm'].lower()!=route['source_model'].lower()+'.rgm':
            raise ValueError(f'{name}: official donor/source route mismatch')
        if row['private_stem']!=route['private_stem'] or row['consumers']!=route['consumers']:
            raise ValueError(f'{name}: consumer route mismatch')
        for key in ('decoded_manifest','geometry_recipe','authored_rrgeom','geometry_report',
                    'editable_blend','preview_donor_lod1','preview_candidate_lod1',
                    'preview_rider_close','preview_team_red','preview_team_blue',
                    'preview_donor_lod2','preview_candidate_lod2',
                    'preview_donor_lod3','preview_candidate_lod3'):
            file = ROOT/row[key]
            if not file.is_file() or sha(file)!=row[key+'_sha256']:
                raise ValueError(f'{name}: {key} missing or hash mismatch')
        if name.startswith(('mehari','sanhaja','zenata_age04')):
            for key in ('preview_donor_rider_only','preview_candidate_rider_only'):
                file = ROOT/row[key]
                if not file.is_file() or sha(file)!=row[key+'_sha256']:
                    raise ValueError(f'{name}: {key} missing or hash mismatch')
        if len(row['albedo_variants'])!=2 or len({a['source_texture'] for a in row['albedo_variants']})!=2:
            raise ValueError(f'{name}: missing exact separate rider/mount atlases')
        for atlas in row['albedo_variants']:
            if sha(ROOT/atlas['authored_png']) != atlas['sha256']:
                raise ValueError(f'{name}: authored atlas SHA mismatch')
        recipe=json.loads((ROOT/row['geometry_recipe']).read_text(encoding='utf8'))
        decoded=json.loads((ROOT/row['decoded_manifest']).read_text(encoding='utf8'))
        report=json.loads((ROOT/row['geometry_report']).read_text(encoding='utf8'))
        if recipe['manifest_sha256']!=row['decoded_manifest_sha256'] or recipe['geometry_sha256']!=row['native_source_rrgeom_sha256']:
            raise ValueError(f'{name}: pinned native source hash mismatch')
        if report['output_sha256']!=row['authored_rrgeom_sha256'] or report['source_sha256']!=row['native_source_rrgeom_sha256']:
            raise ValueError(f'{name}: native geometry report hash mismatch')
        if len(report['groups'])<6 or any(g['edited_vertices']<=0 or not g['within_original_native_bounds'] for g in report['groups']):
            raise ValueError(f'{name}: incomplete edited rider/mount LODs')
        for g in recipe['groups']:
            source_group=decoded['geometry']['groups'][g['index']]
            if (source_group.get('skin_projection') or {}).get('status')!='palette_indices_and_weights_decoded':
                raise ValueError(f'{name}: selected group without native SKIN')
        for visual in ('preview_candidate_lod1','preview_candidate_lod2',
                       'preview_candidate_lod3','preview_team_red','preview_team_blue'):
            image=Image.open(ROOT/row[visual])
            if image.size!=(850,850):
                raise ValueError(f'{name}: unexpected render size')
        red=Image.open(ROOT/row['preview_team_red']).convert('RGB')
        blue=Image.open(ROOT/row['preview_team_blue']).convert('RGB')
        if ImageChops.difference(red,blue).getbbox() is None:
            raise ValueError(f'{name}: team previews do not differ')
    print(json.dumps({'status':'mounted_source_verified_native_cook_pending',
                      'body_routes':len(rows), 'two_atlas_variants':sum(len(r['albedo_variants']) for r in rows),
                      'packed_blends':len(rows), 'five_view_sets':len(rows),
                      'native_animation':'unverified','native_match':'unverified'},indent=2))


if __name__=='__main__':
    main()
