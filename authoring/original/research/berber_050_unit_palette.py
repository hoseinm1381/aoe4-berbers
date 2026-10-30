"""Prepare the Abbasid archer's non-team-colour cloth palette for review/cook.

The native patternTex is retained; this changes only the tan under-tunic and
sleeves in a private albedoTexture copy. The donor DDS SHA is pinned by the
decoded manifest and can be regenerated from the shared stock cache.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from berber_050_common import ART, sha, write


MANIFEST = Path('output/shared_stock_cache/units_050/46f0c2bba7f6f0abb21eca232d024f466ae94bc028aa8d803732c54c2b003781/decoded/8a58c40f9bdeafad90e1/decoded-static.json')
SOURCE = MANIFEST.parent / 'textures/3cd791ead578_4030391217154354827_packed.dds'
PATTERN = MANIFEST.parent / 'textures/506394ab5485_8334376028064855438_packed.dds'
OUTPUT = ART / 'pilots/abb_archer_age2_pilot/indigo-underrobe-albedo.png'


def main():
    manifest = json.loads(MANIFEST.read_text(encoding='utf8'))
    assert manifest['request']['logical_path'].endswith('abb_ranged_bow_age02.rgm')
    assert SOURCE.is_file()
    image = Image.open(SOURCE).convert('RGBA')
    pattern = Image.open(PATTERN).convert('RGB')
    pixels = image.load()
    masks = pattern.load()
    edited = 0
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]
            mr, mg, mb = masks[x, y]
            if (mr > 100 and mr > mg*1.4 and mr > mb*1.4) or (mg > 100 and mg > mr*1.4 and mg > mb*1.4):
                continue
            # UV atlas: tan jacket body/sleeves and underrobe, excluding the
            # rust leather strap, patterned over-robe, skin, and red quiver.
            region = ((x < 355 and 145 <= y < 287) or
                      (x >= 377 and 140 <= y < 391) or
                      (x < 356 and y >= 454))
            tan = r > 45 and 0.87 < r/max(g,1) < 1.85 and 1.08 < g/max(b,1) < 1.9
            if not region or not tan:
                continue
            luminance = 0.2126*r + 0.7152*g + 0.0722*b
            if x < 356 and 466 <= y <= 472:
                # A slim unmasked woven-ochre hem above the stock white edge.
                pixels[x,y] = (round(min(255,luminance*1.1)),
                               round(min(255,luminance*0.86)),
                               round(min(255,luminance*0.51)),a)
            else:
                pixels[x,y] = (round(min(255, luminance*0.52)),
                               round(min(255, luminance*0.72)),
                               round(min(255, luminance*0.93)), a)
            edited += 1
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT)
    write(OUTPUT.with_suffix('.json'), {'status':'palette_prepared_no_cook',
        'source':str(SOURCE),'source_sha256':sha(SOURCE),
        'native_pattern':str(PATTERN),'native_pattern_sha256':sha(PATTERN),
        'output':str(OUTPUT),'output_sha256':sha(OUTPUT),
        'edited_pixels':edited,'patternTex':'untouched native source',
        'skinTintLUT':'untouched native source',
        'slot':'albedoTexture','runtime_owner_colour':'unverified'})
    print(OUTPUT, edited)


if __name__ == '__main__':
    main()
