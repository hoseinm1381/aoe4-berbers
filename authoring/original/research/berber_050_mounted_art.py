"""Author exact-donor, combined mounted Berber body variants for source review.

The input route table and Luna's immutable donor cache determine identities.
Native geometry edits are delegated to the bounded skinned RRGeom writer. This
module writes only task-owned source art; it does not cook or bind resources.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from berber_050_common import ROOT, ART, sha, write
from berber_050_unit_pipeline import remix, source_geometry

OUT = ART / 'mounted'
ROUTES = ROOT / 'output/berber_update_0_5_0/bindings/model-routes.json'
DONORS = ROOT / 'output/berber_update_0_5_0/donors.json'
FAMILIES = {'scout', 'mehari', 'sanhaja', 'zenata', 'lancer'}
COLORS = {
    'scout': {'rider': (0.23, 0.37, 0.53), 'tack': (0.63, 0.45, 0.24)},
    'mehari': {'rider': (0.24, 0.37, 0.52), 'tack': (0.67, 0.49, 0.27)},
    'sanhaja': {'rider': (0.20, 0.31, 0.51), 'tack': (0.62, 0.44, 0.23)},
    'zenata': {'rider': (0.52, 0.31, 0.24), 'tack': (0.67, 0.51, 0.28)},
    'lancer': {'rider': (0.22, 0.34, 0.51), 'tack': (0.67, 0.50, 0.30)},
}


def _is_owned(group):
    return (group['stream'] == 'UnitDataStream' and
            (group.get('rig_projection') or {}).get('status') == 'decoded' and
            (group.get('skin_projection') or {}).get('status') == 'palette_indices_and_weights_decoded')


def group_role(group):
    if not _is_owned(group):
        return None
    bounds = group['bounds']
    span_y = bounds['extent'][1]
    material = group['material'].lower()
    if span_y > 1.5 and len(group['positions']) >= 200:
        return 'tack'
    if span_y < 0.85 and len(group['positions']) >= 150 and ('rider' in material or 'lod' in material):
        return 'rider'
    return None


def shape_features(group, role, family):
    low = group['bounds']['minimum']
    high = group['bounds']['maximum']
    cx = (low[0] + high[0]) / 2
    cy = (low[1] + high[1]) / 2
    common = {'center_xy': [cx, cy], 'radius_xy': [1.0, 1.0],
              'radial_window': [0, .01, .9, 2]}
    if role == 'rider':
        crown = high[2]
        lower = {'kind': 'lateral_expand', 'z_window': [.53, .70, 1.18, 1.43],
                 'metres': .038 if family in ('scout', 'mehari', 'sanhaja') else .026,
                 'abs_x_window': [.10, .17, .37, .51]}
        sleeve = {'kind': 'lateral_expand', 'z_window': [1.13, 1.25, 1.53, 1.75],
                  'metres': .020, 'abs_x_window': [.24, .32, .54, .62]}
        head = {'kind': 'radial_expand',
                'z_window': [crown-.37, crown-.26, crown-.12, crown-.025],
                'metres': .022 if family not in ('lancer',) else .012,
                'abs_x_window': [0, .01, .16, .23]}
        return [dict(common, **feature) for feature in (lower, sleeve, head)]
    # The saddle/tack is near the animal's spine; the narrow Y window keeps
    # the head, neck, lower legs and tail outside the deformation field.
    camel = family in ('mehari', 'sanhaja')
    saddle = {'kind': 'lateral_expand',
              'z_window': [1.0, 1.24, 1.65 if not camel else 2.0, 1.85 if not camel else 2.3],
              'metres': .018, 'abs_x_window': [.16, .23, .43, .58],
              'y_window': [-.86, -.63, .45, .69]}
    return [dict(common, **saddle)]


def material_texture(material, slot):
    matches = [t for t in material['textures'] if t['name'] == slot and t.get('projection_path')]
    if len(matches) != 1:
        return None
    return matches[0]


def uv_mask(groups, role, width, height, family):
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    # Union every native LOD that shares this albedo atlas. Lower LODs can
    # remap the same garment into different UV islands of that atlas.
    for group in groups:
        if group_role(group) != role:
            continue
        uv = group['uv_layers'].get('UVMap')
        if not uv or len(uv) != len(group['positions']):
            continue
        for tri in group['triangles']:
            points = [group['positions'][i] for i in tri]
            centroid = [sum(p[k] for p in points)/3 for k in range(3)]
            if role == 'rider':
                lower_limit = 1.08 if family == 'sanhaja' else .48
                selected = (lower_limit <= centroid[2] <= 1.75 and abs(centroid[0]) < .58)
            else:
                selected = (1.05 <= centroid[2] <= 2.14 and -.23 <= centroid[1] <= .63)
            if not selected:
                continue
            poly = [(uv[i][0]*width, (1-uv[i][1])*height) for i in tri]
            if all(-.05*width <= x <= 1.05*width and -.05*height <= y <= 1.05*height for x,y in poly):
                draw.polygon(poly, fill=255)
    return mask.filter(ImageFilter.MaxFilter(3))


def paint_albedos(manifest, folder, family, age):
    groups = manifest['geometry']['groups']
    first_material = {}
    for group in groups:
        role = group_role(group)
        if role and 'lod1' in group['material'].lower():
            first_material.setdefault(role, group['material'])
    if set(first_material) != {'rider', 'tack'}:
        raise ValueError(f'Expected complete combined rider/mount LOD1, got {first_material}')
    materials = {m['name']: m for m in manifest['material']['materials']}
    previews = {}
    receipts = []
    for role, material_name in first_material.items():
        material = materials[material_name]
        albedo = material_texture(material, 'albedoTexture')
        pattern = material_texture(material, 'patternTex')
        if not albedo or not pattern:
            raise ValueError(f'{material_name}: missing native albedo/pattern')
        source_path = Path(albedo['projection_path'])
        mask_path = Path(pattern['projection_path'])
        image = Image.open(source_path).convert('RGBA')
        source = image.copy()
        mask = Image.open(mask_path).convert('RGB')
        if mask.size != image.size:
            raise ValueError(f'{material_name}: native pattern size mismatch')
        atlas_groups = []
        for group in groups:
            if group_role(group) != role:
                continue
            group_material = materials.get(group['material'])
            group_albedo = material_texture(group_material, 'albedoTexture') if group_material else None
            if group_albedo and group_albedo['logical_path'] == albedo['logical_path']:
                atlas_groups.append(group)
        selected = uv_mask(atlas_groups, role, *image.size, family)
        pixels, source_pixels, pattern_pixels, chosen = image.load(), source.load(), mask.load(), selected.load()
        near_owner = None
        if role == 'tack' and family in ('mehari','sanhaja'):
            owner_bitmap = Image.new('L', image.size, 0)
            owner_pixels = owner_bitmap.load()
            for oy in range(image.height):
                for ox in range(image.width):
                    cr,cg,cb = pattern_pixels[ox,oy]
                    if (cr > 100 and cr > 1.4*cg and cr > 1.4*cb) or (cg > 100 and cg > 1.4*cr and cg > 1.4*cb):
                        owner_pixels[ox,oy] = 255
            near_owner = owner_bitmap.filter(ImageFilter.MaxFilter(13)).load()
        edited = 0
        protected = 0
        # Age II Mehari shares the Age III combined native donor. Give its
        # rider a sand lamellar treatment to establish the age progression;
        # the camel/tack atlas and all other age palettes stay as authored.
        mehari_two_rider = family == 'mehari' and age == 2 and role == 'rider'
        if mehari_two_rider and not albedo['logical_path'].lower().endswith('/3737955105979851120_packed.rrtex'):
            raise ValueError('Mehari II sand paint region is qualified only for the native rider atlas')
        target = (.55, .45, .335) if mehari_two_rider else COLORS[family][role]
        # Progressive trim: later ages receive a brighter muted cloth tone.
        age_factor = 1.0 + .045*(age-2)
        for y in range(image.height):
            for x in range(image.width):
                if not chosen[x,y]:
                    continue
                if near_owner is not None and not near_owner[x,y]:
                    continue
                mr, mg, mb = pattern_pixels[x,y]
                owner = (mr > 100 and mr > 1.4*mg and mr > 1.4*mb) or (mg > 100 and mg > 1.4*mr and mg > 1.4*mb)
                if owner:
                    protected += 1
                    continue
                r,g,b,a = pixels[x,y]
                if a < 8:
                    continue
                # Restrict alteration to cloth/leather/blanket color families.
                # Bright white metalwork, black linework and warm skin survive.
                lum = .2126*r + .7152*g + .0722*b
                if lum < 35 or lum > 235 or (role == 'rider' and r > g*1.22 and g > b*1.23 and lum > 80):
                    continue
                if mehari_two_rider:
                    # This exact native atlas places neutral lamellar and
                    # adjacent padded cloth below y=138. Chainmail fills the
                    # bottom and far-right islands; preserve its metal gray.
                    plate_or_cuff = (x < 390 and 138 <= y < 380) or (190 <= x < 255 and 115 <= y < 190)
                    if not plate_or_cuff or min(r,g,b) < 90 or max(r,g,b)-min(r,g,b) >= 65:
                        continue
                # The animal coat and saddle share an atlas. The native tack is
                # darker than the coat; keep the coat's broad middle values.
                if role == 'tack' and family not in ('mehari','sanhaja') and (lum > 82 or r/max(g,1) < 1.48):
                    continue
                if role == 'tack' and family in ('mehari','sanhaja') and lum > 112:
                    continue
                factor = 1.52 if role == 'rider' else 1.42
                rgb = tuple(round(min(255, max(0, lum * factor * c * age_factor))) for c in target)
                if max(abs(rgb[i]-(r,g,b)[i]) for i in range(3)) < 8:
                    continue
                pixels[x,y] = (*rgb,a)
                edited += 1
        if edited < image.width * image.height * (.0015 if role == 'tack' else .004):
            raise ValueError(f'{material_name}: too few painted source texels ({edited})')
        # Exhaustive owner-mask equality, beyond the selected triangles.
        for y in range(image.height):
            for x in range(image.width):
                mr,mg,mb = pattern_pixels[x,y]
                owner = (mr > 100 and mr > 1.4*mg and mr > 1.4*mb) or (mg > 100 and mg > 1.4*mr and mg > 1.4*mb)
                if owner and pixels[x,y] != source_pixels[x,y]:
                    raise ValueError(f'{material_name}: owner-color texel altered')
        output = folder / f'{role}-albedo.png'
        image.save(output)
        selected.save(folder / f'{role}-paint-mask.png')
        texture_id = Path(albedo['logical_path']).stem.split('_')[0]
        previews[texture_id] = output.name
        receipts.append({'role':role, 'material':material_name,
                         'source_texture':albedo['logical_path'],
                         'authored_png':str(output.relative_to(ROOT)),
                         'sha256':sha(output),
                         'donor_albedo':str(source_path),
                         'donor_albedo_sha256':sha(source_path), 'native_pattern':str(mask_path),
                         'native_pattern_sha256':sha(mask_path), 'authored_albedo':str(output),
                         'authored_albedo_sha256':sha(output), 'edited_pixels':edited,
                         'owner_mask_selected_pixels_preserved':protected,
                         'owner_mask_byte_equal':True, 'native_pattern':'untouched',
                         'native_team_colour':'unverified'})
    return previews, receipts


def make_row(route, donor):
    name = route['private_variant_name']
    folder = OUT / name
    folder.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / donor['decoded_manifest']
    manifest = json.loads(manifest_path.read_text(encoding='utf8'))
    logical_path = route['source_model'] + '.rgm'
    if manifest['request']['logical_path'].lower() != logical_path.lower():
        raise ValueError(f'{name}: donor identity mismatch')
    native_rgm = next(x for x in donor['source_files'] if x['path'].lower().endswith('.rgm'))
    if donor['native_resource_sha256'] != native_rgm['sha256']:
        raise ValueError(f'{name}: donor RGM hash mismatch')
    rrgeom = source_geometry(manifest_path, manifest)
    original_groups = manifest['geometry']['groups']
    group_specs = []
    for index, group in enumerate(original_groups):
        role = group_role(group)
        if role is None:
            continue
        features = shape_features(group, role, route['family'])
        group_specs.append({'index':index, 'max_displacement_metres':.075,
                            'features':features, 'contain_within_donor_bounds':True,
                            'max_clipped_fraction':.11})
    if len([g for g in group_specs if group_role(original_groups[g['index']]) == 'rider']) < 3:
        raise ValueError(f'{name}: lacks three skinned rider LODs')
    if len([g for g in group_specs if group_role(original_groups[g['index']]) == 'tack']) < 3:
        raise ValueError(f'{name}: lacks three skinned mount LODs')
    age = route['age']
    previews, materials = paint_albedos(manifest, folder, route['family'], age)
    recipe = {'schema':'berber-050-unit-geometry/v1', 'name':name,
              'manifest':donor['decoded_manifest'], 'manifest_sha256':sha(manifest_path),
              'logical_path':logical_path, 'geometry_sha256':sha(rrgeom),
              'output_dir':str(folder), 'design':f"{route['family']} age {age}: regionally tailored rider garment and native combined-mount tack, donor rig and team masks retained",
              'groups':group_specs, 'preview_albedos':previews}
    recipe_path = folder / 'recipe.json'
    write(recipe_path, recipe)
    report = remix(recipe_path)
    row = {'family':route['family'], 'age':age, 'private_variant_name':name,
           'state':route['state'], 'private_stem':route['private_stem'],
           'official_donor_rgm':logical_path, 'official_donor_rgm_sha256':donor['native_resource_sha256'],
           'decoded_manifest':donor['decoded_manifest'], 'decoded_manifest_sha256':sha(manifest_path),
           'native_source_rrgeom_sha256':sha(rrgeom), 'geometry_recipe':str(recipe_path.relative_to(ROOT)),
           'geometry_recipe_sha256':sha(recipe_path),
           'authored_rrgeom':str(Path(report['output']).relative_to(ROOT)),
           'authored_rrgeom_sha256':report['output_sha256'],
           'geometry_report':str((folder/'geometry-report.json').relative_to(ROOT)),
           'geometry_report_sha256':sha(folder/'geometry-report.json'),
           'albedos':materials, 'albedo_variants':[
               {'source_texture':m['source_texture'], 'authored_png':m['authored_png'],
                'sha256':m['sha256'], 'role':m['role']} for m in materials],
           'authored_albedo':materials[0]['authored_png'],
           'authored_albedo_sha256':materials[0]['sha256'],
           'consumers':route['consumers'],
           'native_cook':'pending root serial integration', 'native_animation':'unverified'}
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--names', nargs='*', help='Only these private variant names')
    args = parser.parse_args()
    routes = json.loads(ROUTES.read_text(encoding='utf8'))['models']
    donor_data = json.loads(DONORS.read_text(encoding='utf8'))
    donors = {d['logical_path'].lower():d for family in donor_data['families'].values()
              for d in family.get('donors',[])}
    target = [r for r in routes if r['family'] in FAMILIES and r['state'] == 'body' and
              (args.names is None or r['private_variant_name'] in args.names)]
    allowed = {r['private_variant_name'] for r in routes if r['family'] in FAMILIES and r['state'] == 'body'}
    manifest_file = OUT / 'mounted-manifest.json'
    existing = json.loads(manifest_file.read_text(encoding='utf8')) if manifest_file.is_file() else {'schema':'berber-050-mounted-art/v1', 'variants':[]}
    rows = {r['private_variant_name']:r for r in existing['variants']
            if r['private_variant_name'] in allowed}
    for route in target:
        print('AUTHORING', route['private_variant_name'], flush=True)
        donor = donors.get((route['source_model']+'.rgm').lower())
        if donor is None:
            raise FileNotFoundError(f"Exact native donor missing: {route['source_model']}")
        row = make_row(route, donor)
        rows[route['private_variant_name']] = row
        write(manifest_file, {'schema':'berber-050-mounted-art/v1',
              'status':'source_geometry_and_palette_prepared_no_cook',
              'excluded_probes':existing.get('excluded_probes',[]),
              'variants':[rows[k] for k in sorted(rows)]})
        print('AUTHORED', route['private_variant_name'], row['authored_rrgeom_sha256'], flush=True)


if __name__ == '__main__':
    main()
