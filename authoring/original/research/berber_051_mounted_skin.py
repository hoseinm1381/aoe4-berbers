"""Inspect native mounted rider UV anatomy for separate 0.5.1 skin overlays.

This script reads the immutable 0.5.0 source art and decoded native geometry.
It never modifies those inputs or cooks game resources.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

from berber_050_common import ROOT, ART

OUT = ART.parent / 'unit_skin_0_5_1' / 'mounted'
BODY = ART / 'mounted/mounted-manifest.json'
UPGRADE = ART / 'mounted_upgrades/upgrades-manifest.json'


def entries():
    for manifest, kind in ((BODY, 'body'), (UPGRADE, 'upgrade')):
        for row in json.loads(manifest.read_text(encoding='utf8'))['variants']:
            rider = next((a for a in row['albedo_variants'] if a.get('role') == 'rider'),
                         row['albedo_variants'][0] if kind == 'upgrade' else None)
            if rider is None or '/humans/' not in rider['source_texture']:
                raise ValueError(f"No native human rider atlas: {row['private_variant_name']}")
            yield kind, row, rider


def mesh_masks(decoded, source_texture, size):
    materials = {m['name']: m for m in decoded['material']['materials']}
    groups = []
    for group in decoded['geometry']['groups']:
        material = materials.get(group['material'])
        if not material:
            continue
        albedo = next((t for t in material['textures'] if t['name'] == 'albedoTexture'), None)
        if albedo and albedo.get('logical_path') == source_texture:
            groups.append(group)
    if len(groups) < 3:
        raise ValueError(f'Rider atlas should bind three native LODs: {source_texture}, got {len(groups)}')
    width, height = size
    masks = {part: Image.new('L', size, 0) for part in ('head', 'hands')}
    draws = {part: ImageDraw.Draw(mask) for part, mask in masks.items()}
    counts = {'head': 0, 'hands': 0}
    for group in groups:
        positions = group['positions']
        uv = group['uv_layers'].get('UVMap')
        if not uv or len(uv) != len(positions):
            raise ValueError(f"Native rider UV mismatch: {group['material']}")
        z_top = group['bounds']['maximum'][2]
        y_mid = sum((group['bounds']['minimum'][1], group['bounds']['maximum'][1])) / 2
        for tri in group['triangles']:
            x, y, z = (sum(positions[i][axis] for i in tri)/3 for axis in range(3))
            part = None
            if abs(x) < .22 and z_top - .37 < z < z_top - .035 and y < y_mid:
                part = 'head'
            elif abs(x) > .39 and .79 < z < 1.23:
                part = 'hands'
            if part is None:
                continue
            polygon = [(uv[i][0]*width, (1-uv[i][1])*height) for i in tri]
            if any(not (-.02*width <= px <= 1.02*width and -.02*height <= py <= 1.02*height)
                   for px, py in polygon):
                continue
            draws[part].polygon(polygon, fill=255)
            counts[part] += 1
    return masks, counts


def contacts():
    OUT.mkdir(parents=True, exist_ok=True)
    roster = []
    for kind, row, rider in entries():
        name = row['private_variant_name']
        image = Image.open(ROOT / rider['authored_png']).convert('RGBA')
        decoded = json.loads((ROOT / row['decoded_manifest']).read_text(encoding='utf8'))
        masks, counts = mesh_masks(decoded, rider['source_texture'], image.size)
        overlay = image.convert('RGB').copy()
        paint = Image.new('RGB', image.size, (243, 90, 220))
        green = Image.new('RGB', image.size, (61, 229, 125))
        overlay.paste(paint, (0, 0), masks['head'].point(lambda x: 115 if x else 0))
        overlay.paste(green, (0, 0), masks['hands'].point(lambda x: 115 if x else 0))
        folder = OUT / name
        folder.mkdir(exist_ok=True)
        masks['head'].save(folder / 'head-uv-probe.png')
        masks['hands'].save(folder / 'hands-uv-probe.png')
        overlay.save(folder / 'uv-anatomy-probe.png')
        roster.append((name, kind, rider['source_texture'], image, overlay, counts))
    columns = 4
    card_w, card_h = 522, 300
    canvas = Image.new('RGB', (columns*card_w, math.ceil(len(roster)/columns)*card_h), '#e4e4e4')
    draw = ImageDraw.Draw(canvas)
    for index, (name, kind, source, original, overlay, counts) in enumerate(roster):
        x, y = index % columns * card_w, index // columns * card_h
        draw.text((x+5,y+4), f'{name} ({kind})', fill='#111')
        draw.text((x+5,y+19), Path(source).stem[:22] + f'  head={counts["head"]} hand={counts["hands"]}', fill='#333')
        for j, image in enumerate((original, overlay)):
            thumb = image.convert('RGB')
            thumb.thumbnail((255,255))
            canvas.paste(thumb, (x+j*260+(260-thumb.width)//2, y+40))
    target = OUT / 'mounted-skin-uv-atlas-contact.png'
    canvas.save(target)
    print('MOUNTED_SKIN_CONTACT', target, len(roster), flush=True)


if __name__ == '__main__':
    contacts()
