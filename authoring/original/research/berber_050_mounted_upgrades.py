"""Prepare hash-pinned camel upgrade art recipes from exact consumed native routes.

This creates authoring recipes only. Run the shared unit pipeline and inspect a
textured pilot before batching; native cook and gameplay tests are separate.
"""
from __future__ import annotations

import argparse
import json
import math
import struct
from pathlib import Path
from PIL import Image, ImageChops

from berber_050_common import ART, OUT, ROOT, read, sha, write

DEST = ART / 'mounted_upgrades'
ROUTES = OUT / 'bindings/model-routes.json'


def source_record(logical_path: str) -> dict:
    donors = read(OUT / 'donors.json')
    for grouping in donors['families'].values():
        for donor in grouping.get('donors', []):
            if donor.get('logical_path') == logical_path:
                return donor
    raise ValueError(f'Exact upgrade donor has no decoded manifest: {logical_path}')


def feature(kind: str, metres: float, z_window: list[float], abs_x_window: list[float],
            y_window: list[float] | None = None) -> dict:
    value = {'kind': kind, 'metres': metres, 'z_window': z_window,
             'abs_x_window': abs_x_window, 'center_xy': [0, 0],
             'radius_xy': [1, 1], 'radial_window': [0, .01, .9, 2]}
    if y_window:
        value['y_window'] = y_window
    return value


def make(name: str) -> Path:
    routes = read(ROUTES)['models']
    matches = [row for row in routes if row['private_variant_name'] == name and row['state'] == 'upgrade']
    if len(matches) != 1:
        raise ValueError(f'Expected one exact consumed upgrade route for {name}; found {len(matches)}')
    route = matches[0]
    if route['family'] not in ('mehari', 'sanhaja'):
        raise ValueError(f'Not a camel upgrade: {name}')
    logical = route['source_model'] + '.rgm'
    donor = source_record(logical)
    manifest_path = ROOT / donor['decoded_manifest']
    manifest = read(manifest_path)
    if manifest['request']['logical_path'] != logical:
        raise ValueError('Decoded donor does not match exact consumed source')
    if manifest['rig_palette_binding']['status'] != 'complete':
        raise ValueError(f'Skin binding incomplete: {name}')
    camel_width = {2:.025,3:.036,4:.044}[route['age']]
    rider_width = {2:.027,3:.037,4:.045}[route['age']]
    wrap_width = {2:.016,3:.024,4:.030}[route['age']]
    groups = []
    for index, group in enumerate(manifest['geometry']['groups']):
        material = str(group.get('material', '')).lower()
        if material.startswith('camel_'):
            shape = [feature('lateral_expand', camel_width, [1.12, 1.32, 1.84, 2.16],
                             [.16, .21, .45, .53], [-.95, -.72, .38, .63])]
        elif material.startswith('rider_'):
            shape = [feature('lateral_expand', rider_width, [.48, .63, 1.08, 1.34],
                             [.10, .15, .38, .48]),
                     feature('radial_expand', wrap_width, [1.57, 1.67, 1.83, 1.94],
                             [0, .01, .18, .23])]
        else:
            continue  # Native companion mesh is retained byte-identical.
        groups.append({'index': index, 'max_displacement_metres': .08,
                       'features': shape, 'contain_within_donor_bounds': True,
                       'max_clipped_fraction': .1})
    if not any(str(manifest['geometry']['groups'][g['index']]['material']).startswith('camel_') for g in groups):
        raise ValueError('No camel LOD selected')
    if not any(str(manifest['geometry']['groups'][g['index']]['material']).startswith('rider_') for g in groups):
        raise ValueError('No rider LOD selected')
    folder = DEST / name
    folder.mkdir(parents=True, exist_ok=True)
    recipe = {
        'schema': 'berber-050-unit-geometry/v1',
        'name': name,
        'output_dir': str(folder.relative_to(ROOT)),
        'manifest': donor['decoded_manifest'],
        'manifest_sha256': sha(manifest_path),
        'logical_path': logical,
        'geometry_sha256': manifest['geometry']['source']['sha256'],
        'design': ('Native gold/cream camel armour; controlled sand-to-indigo rider '
                   'cloth or gunmetal lamellar according to the exact native atlas. '
                   'Native seat, skin, topology, sockets and LOD structure retained.'),
        'groups': groups,
    }
    path = folder / 'recipe.json'
    if path.exists() and read(path) != recipe:
        raise FileExistsError(f'Existing upgrade recipe differs: {path}')
    path.write_text(json.dumps(recipe, indent=2) + '\n', encoding='utf8')
    return path


def palette(name: str) -> None:
    path = DEST / name / 'recipe.json'
    recipe = read(path)
    manifest = read(ROOT / recipe['manifest'])
    route = next(row for row in read(ROUTES)['models'] if row['private_variant_name'] == name)
    family, age = route['family'], route['age']
    factors = {
        ('mehari', 2): {'cuff': (.76,.66,.50), 'lamellar': (.83,.69,.51)},
        ('mehari', 3): {'cuff': (.37,.47,.67), 'lamellar': (.56,.63,.72)},
        ('mehari', 4): {'cuff': (.28,.38,.57), 'lamellar': (.42,.51,.67)},
        ('sanhaja', 2): {'cuff': (.60,.68,.76), 'lamellar': (.55,.62,.73)},
        ('sanhaja', 3): {'cuff': (.34,.46,.67), 'lamellar': (.46,.55,.72)},
        ('sanhaja', 4): {'cuff': (.26,.38,.59), 'lamellar': (.37,.46,.66)},
    }[(family, age)]
    material = {row['name']: row for row in manifest['material']['materials']}
    authored = []
    preview = {}
    # The armored camel and its blanket retain native gold/cream material.
    # Tailor the skinned rider's garment and keep every player-colour texel.
    for role in ('rider',):
        native = material[f'{role}_lod1']
        textures = {row['name']: row for row in native['textures']}
        alb, mask = textures['albedoTexture'], textures['patternTex']
        source = Path(alb['projection_path'])
        mask_path = Path(mask['projection_path'])
        image = Image.open(source).convert('RGBA')
        original = image.copy()
        pattern = Image.open(mask_path).convert('RGB')
        if image.size != pattern.size:
            raise ValueError(f'Pattern dimensions differ: {name}:{role}')
        source_pixels = image.load()
        mask_pixels = pattern.load()
        changed = 0
        protected = 0
        atlas_id = Path(alb['logical_path']).stem.split('_')[0]
        for y in range(image.height):
            for x in range(image.width):
                mr, mg, mb = mask_pixels[x, y]
                if (mr > 100 and mr > 1.4 * mg and mr > 1.4 * mb) or (mg > 100 and mg > 1.4 * mr and mg > 1.4 * mb):
                    protected += 1
                    continue
                r, g, b, a = source_pixels[x, y]
                # Gray cuff and darkened lamellar plates form a coherent
                # indigo/gunmetal rider kit. The silver chainmail, turban,
                # leather, skin and native owner hem retain their contracts.
                if atlas_id == '1649538409555299477':
                    cuff = 190 <= x < 326 and 0 <= y < 66
                    lamellar = 65 <= x < 380 and 174 <= y < 377
                    eligible = ((cuff or lamellar) and min(r,g,b) > (80 if cuff else 110)
                                and max(r,g,b)-min(r,g,b) < 55)
                    channels = factors['cuff' if cuff else 'lamellar']
                elif atlas_id == '8817396932111397643':
                    # Native Age IV plate armour islands, excluding gold trim,
                    # face, gloves, wrap, straps and owner-colour cloth.
                    region = (x < 430 and 174 <= y < 424) or (390 <= x and y < 112)
                    eligible = region and min(r,g,b)>105 and max(r,g,b)-min(r,g,b)<55
                    channels = factors['lamellar']
                elif atlas_id == '4030391217154354827':
                    # Native Archer II jacket, sleeves and lower underrobe.
                    # Same atlas-qualified garment regions as the approved
                    # infantry pilot; preserve its white overrobe and turban.
                    region = ((x < 355 and 145 <= y < 287) or
                              (x >= 377 and 140 <= y < 391) or
                              (x < 356 and y >= 454))
                    eligible = region and r>45 and .87<r/max(g,1)<1.85 and 1.08<g/max(b,1)<1.9
                    channels = (.45,.61,.82) if age>=3 else (.58,.72,.86)
                elif atlas_id == '15466671798196334295':
                    # Native ranged IV warm sleeves and underrobe. Do not
                    # recolour white overrobe, mail, skin, quiver or headwrap.
                    region = ((x>=357 and y<245) or (x<352 and 245<=y<333))
                    eligible = region and r>45 and .87<r/max(g,1)<1.85 and 1.08<g/max(b,1)<1.9
                    channels = (.37,.53,.76)
                else:
                    raise ValueError(f'Unqualified rider atlas: {atlas_id}')
                if not eligible:
                    continue
                lum = .2126 * r + .7152 * g + .0722 * b
                target = tuple(round(lum * factor) for factor in channels) + (a,)
                if target == (r, g, b, a):
                    continue
                source_pixels[x, y] = target
                changed += 1
        if not changed:
            raise ValueError(f'No visible {role} palette pixels changed: {name}')
        dest = path.parent / f'{role}-albedo.png'
        image.save(dest)
        authored.append({'source_texture': alb['logical_path'],
                         'source_texture_sha256': sha(source),
                         'native_pattern_texture': mask['logical_path'],
                         'native_pattern_sha256': sha(mask_path),
                         'authored_png': str(dest.relative_to(ROOT)),
                         'sha256': sha(dest), 'edited_pixels': changed,
                         'changed_owner_mask_pixels': 0,
                         'owner_mask_selected_pixels_preserved': protected,
                         'owner_mask_byte_equal': True,
                         'native_team_colour': 'unverified'})
        preview[Path(alb['logical_path']).stem.split('_')[0]] = dest.name
    recipe['preview_albedos'] = preview
    recipe['design'] = ('Native gold/cream camel armour retained; exact-atlas tailored '
                        'sand/indigo rider cloth and gunmetal lamellar. Lower garment '
                        'and headwrap profiles broadened within native bounds on all '
                        'rider LODs, with restrained wider camel tack. Native seat, '
                        'skin, topology, sockets and LOD structure retained.')
    path.write_text(json.dumps(recipe, indent=2) + '\n', encoding='utf8')
    (path.parent / 'albedo-variants.json').write_text(json.dumps(authored, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'name': name, 'albedo_variants': authored}, indent=2))


def ledger() -> dict:
    """Verify exact route closure and fresh source evidence before handoff."""
    from berber_050_unit_pipeline import _matches, _vertex_chunks, project, rc, source_geometry
    routes = [r for r in read(ROUTES)['models'] if r['state']=='upgrade'
              and r['family'] in ('mehari','sanhaja')]
    rows = []
    for route in routes:
        name = route['private_variant_name']
        folder = DEST / name
        recipe_path = folder / 'recipe.json'
        recipe = read(recipe_path)
        manifest_path = ROOT / recipe['manifest']
        manifest = read(manifest_path)
        source = source_geometry(manifest_path, manifest)
        donor = source_record(recipe['logical_path'])
        report_path = folder / 'geometry-report.json'
        report = read(report_path)
        rrgeom = folder / f'{name}.rrgeom'
        assert recipe['logical_path'] == route['source_model']+'.rgm'
        assert sha(manifest_path) == recipe['manifest_sha256']
        assert sha(source) == recipe['geometry_sha256'] == report['source_sha256']
        assert sha(source.with_suffix('.rgm')) == donor['native_resource_sha256']
        assert sha(recipe_path) == report['recipe_sha256']
        assert sha(rrgeom) == report['output_sha256']
        assert len(report['groups'])>=6
        assert all(g['edited_vertices']>0 and g['within_original_native_bounds'] for g in report['groups'])
        before = rc.parse(source.read_bytes())
        after = rc.parse(rrgeom.read_bytes())
        old_chunks = list(rc.walk(before.roots))
        new_chunks = list(rc.walk(after.roots))
        assert len(old_chunks)==len(new_chunks)
        stream_offsets = {c.offset for c in _vertex_chunks(before)}
        for old,new in zip(old_chunks,new_chunks):
            assert (old.tag,old.name,old.version)==(new.tag,new.name,new.version)
            if old.children:
                continue
            if old.offset not in stream_offsets:
                assert old.payload==new.payload
            else:
                assert old.payload[:16]==new.payload[:16]
                for offset in range(16,len(old.payload),28):
                    assert old.payload[offset+11:offset+12]==new.payload[offset+11:offset+12]
                    assert old.payload[offset+15:offset+28]==new.payload[offset+15:offset+28]
        new_by_offset = {c.offset:c for c in _vertex_chunks(after)}
        old_streams = _vertex_chunks(before)
        checked = 0
        for group in manifest['geometry']['groups']:
            if group['stream']!='UnitDataStream':
                continue
            matching = [c for c in old_streams if _matches(c,group)]
            assert len(matching)==1
            new = new_by_offset[matching[0].offset]
            for i in range(len(group['positions'])):
                p = project(struct.unpack_from('<4e',new.payload,16+i*28))
                assert all(math.isfinite(v) for v in p)
                assert all(group['bounds']['minimum'][a]-.00001<=p[a]<=group['bounds']['maximum'][a]+.00001 for a in range(3))
                checked += 1
        albedos = read(folder/'albedo-variants.json')
        assert len(albedos)==1
        atlas = albedos[0]
        native_mat = next(m for m in manifest['material']['materials'] if m['name']=='rider_lod1')
        ts = {t['name']:t for t in native_mat['textures']}
        original = Image.open(ts['albedoTexture']['projection_path']).convert('RGBA')
        authored = Image.open(ROOT/atlas['authored_png']).convert('RGBA')
        mask = Image.open(ts['patternTex']['projection_path']).convert('RGB')
        assert original.size==authored.size==mask.size
        protected = changed_owner = edited = 0
        for src,dst,(r,g,b) in zip(original.getdata(),authored.getdata(),mask.getdata()):
            owned = (r>100 and r>1.4*g and r>1.4*b) or (g>100 and g>1.4*r and g>1.4*b)
            protected += owned
            changed_owner += owned and src!=dst
            edited += src!=dst
        assert changed_owner==0 and protected==atlas['owner_mask_selected_pixels_preserved']
        assert edited==atlas['edited_pixels'] and edited>0
        assert sha(ROOT/atlas['authored_png'])==atlas['sha256']
        row = {k:route[k] for k in ('family','age','private_variant_name','state','private_stem','consumers')}
        row.update(official_donor_rgm=recipe['logical_path'],
                   official_donor_rgm_sha256=donor['native_resource_sha256'],
                   decoded_manifest=recipe['manifest'], decoded_manifest_sha256=sha(manifest_path),
                   native_source_rrgeom_sha256=sha(source),
                   albedos=albedos,
                   albedo_variants=[{k:atlas[k] for k in ('source_texture','authored_png','sha256')}],
                   authored_albedo=atlas['authored_png'], authored_albedo_sha256=atlas['sha256'],
                   native_cook='pending root serial integration',native_animation='unverified',
                   native_team_colour='unverified',native_match='unverified',
                   design=recipe['design'], visual_change='Intentional garment/armour and silhouette changes; visual review against exact donor. Vertex fraction is diagnostic only.')
        files = {'geometry_recipe':recipe_path,'geometry_report':report_path,'authored_rrgeom':rrgeom,
                 'editable_blend':folder/f'{name}.blend','source_review_report':folder/'blender-review.json',
                 'native_lod_selection':folder/'native-lod-selection.json',
                 'preview_donor_lod1':folder/'textured-donor.png',
                 'preview_candidate_lod1':folder/'textured-candidate.png',
                 'preview_donor_rider_only':folder/'textured-donor-rider.png',
                 'preview_candidate_rider_only':folder/'textured-candidate-rider.png',
                 'preview_rider_close':folder/'textured-candidate-rider.png',
                 'preview_team_red':folder/'textured-team-red.png',
                 'preview_team_blue':folder/'textured-team-blue.png',
                 'preview_team_red_rider':folder/'textured-team-red-rider.png',
                 'preview_team_blue_rider':folder/'textured-team-blue-rider.png'}
        for lod in (2,3):
            for label in ('donor','candidate'):
                files[f'preview_{label}_lod{lod}']=folder/f'textured-{label}-lod{lod}.png'
                files[f'preview_{label}_lod{lod}_rider']=folder/f'textured-{label}-lod{lod}-rider.png'
        for key,path in files.items():
            assert path.is_file() and path.stat().st_size>100
            row[key]=str(path.relative_to(ROOT))
            row[key+'_sha256']=sha(path)
        assert read(files['source_review_report'])['textures']=='packed'
        selected=read(files['native_lod_selection'])['lods']
        expected_groups={(g['mesh_index'],g['group_index'],len(g['positions'])) for g in manifest['geometry']['groups']}
        selected_groups=[(g['mesh_index'],g['group_index'],g['vertices']) for groups in selected.values() for g in groups]
        assert len(selected_groups)==len(expected_groups) and set(selected_groups)==expected_groups
        assert all(any(g['material'].startswith('camel_') for g in selected[str(lod)]) for lod in (1,2,3))
        for red_key,blue_key in [('preview_team_red','preview_team_blue'),('preview_team_red_rider','preview_team_blue_rider')]:
            red=Image.open(files[red_key]).convert('RGB');blue=Image.open(files[blue_key]).convert('RGB')
            assert ImageChops.difference(red,blue).getbbox() is not None
        row['source_checks']={'all_lod_finite_bound_vertices':checked,'all_opaque_native_chunks_equal':True,
                              'native_uv_weights_topology_equal':True,'owner_mask_preserved_texels':protected,
                              'changed_owner_mask_pixels':changed_owner,'camel_atlas':'native unchanged',
                              'rider_lod1_lod2_lod3_palette':'visually consistent in matched isolated native-rest renders',
                              'render_lod_selection':'native garrison_lod_level property; every native group represented once, camel present at all three LODs',
                              'palette_scope':'qualified native atlas regions independent of LOD1 triangle UV selection'}
        rows.append(row)
    assert len(rows)==8 and len({r['private_variant_name'] for r in rows})==8
    lod_receipt={'schema':'berber-050-upgrade-lod-review/v1',
                 'status':'source_lod_consistency_reviewed_runtime_unverified',
                 'review':'All eight isolated rider LOD1/2/3 comparisons inspected. Indigo/gunmetal or sand lamellar and cloth persist across lower LODs. No lower-LOD palette defect reproduced; no albedo or geometry bytes changed for this additional QA.',
                 'native_camel_atlas':'unchanged',
                 'variants':[{k:r[k] for k in ('private_variant_name','authored_rrgeom_sha256','authored_albedo_sha256','editable_blend_sha256',
                    'preview_candidate_lod1_sha256','preview_candidate_lod2_sha256','preview_candidate_lod3_sha256',
                    'preview_candidate_rider_only_sha256','preview_candidate_lod2_rider_sha256','preview_candidate_lod3_rider_sha256')}
                    for r in rows],
                 'contact_sheets':[]}
    for name in ('lod-rider-inspection.png','lod2-rider-review-sheet.png','lod3-rider-review-sheet.png',
                 'lod2-full-review-sheet.png','lod3-full-review-sheet.png'):
        p=DEST/name
        assert p.is_file()
        lod_receipt['contact_sheets'].append({'path':str(p.relative_to(ROOT)),'sha256':sha(p)})
    write(DEST/'lod-review-receipt.json',lod_receipt)
    doc={'schema':'berber-050-mounted-upgrades-art/v1',
         'lod_review_receipt':str((DEST/'lod-review-receipt.json').relative_to(ROOT)),
         'lod_review_receipt_sha256':sha(DEST/'lod-review-receipt.json'),
         'status':'source_geometry_and_palette_prepared_no_cook','variants':rows}
    write(DEST/'upgrades-manifest.json',doc)
    print(json.dumps({'manifest':str((DEST/'upgrades-manifest.json').relative_to(ROOT)),
                      'sha256':sha(DEST/'upgrades-manifest.json'),'variants':len(rows)},indent=2))
    return doc


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name', nargs='?', help='Exact private variant name in bindings/model-routes.json')
    parser.add_argument('--palette', action='store_true', help='Author native-mask-protected camel and rider PNGs')
    parser.add_argument('--manifest', action='store_true', help='Verify sources and write fresh hash-pinned handoff')
    args = parser.parse_args()
    if args.manifest:
        ledger()
    elif args.palette:
        palette(args.name)
    else:
        print(make(args.name))
