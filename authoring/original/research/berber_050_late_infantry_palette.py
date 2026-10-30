"""Reproducible protected-cloth palettes for Masmuda and Handgunner candidates."""
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image

from berber_050_common import ART, sha, write

SPECS={
 'masmuda_age2_candidate':dict(albedo='6436280346346330998',pattern='5560966440135476485',
     regions=[(0,145,0,84),(186,256,149,256)],rgb=(1.12,1.03,.80),mode='neutral',
     collar_rgb=(.76,.57,.32)),
 'masmuda_age3_candidate':dict(albedo='6436280346346330998',pattern='5560966440135476485',
     regions=[(0,145,0,84),(186,256,149,256)],rgb=(.48,.66,.87),mode='neutral',
     collar_rgb=(.34,.49,.69)),
 'masmuda_age4_candidate':dict(albedo='1280872085544497205',pattern='1695774158959602847',
     regions=[(0,182,140,256),(0,137,0,82)],rgb=(.44,.59,.79),mode='warm'),
 'handgunner_age4_candidate':dict(albedo='7398115290648246789',pattern='9585230694925016596',
     regions=[(110,237,0,98),(65,192,139,256)],rgb=(.47,.62,.80),mode='warm'),
}


def make(name,spec):
    folder=ART/'pilots'/name
    recipe_path=folder/'recipe.json'
    recipe=json.loads(recipe_path.read_text(encoding='utf8'))
    cache=Path(recipe['manifest']).parent/'textures'
    source=next(cache.glob('*'+spec['albedo']+'*'))
    mask_path=next(cache.glob('*'+spec['pattern']+'*'))
    image=Image.open(source).convert('RGBA')
    mask=Image.open(mask_path).convert('RGB')
    assert image.size==mask.size==(256,256)
    pixels=image.load();pattern=mask.load();changed=0
    for y in range(256):
        for x in range(256):
            if not any(x0<=x<x1 and y0<=y<y1 for x0,x1,y0,y1 in spec['regions']):
                continue
            mr,mg,mb=pattern[x,y]
            if (mr>100 and mr>1.4*mg and mr>1.4*mb) or (mg>100 and mg>1.4*mr and mg>1.4*mb):
                continue
            r,g,b,a=pixels[x,y]
            if spec['mode']=='neutral':
                eligible=min(r,g,b)>85 and max(r,g,b)-min(r,g,b)<75
            else:
                eligible=r>45 and .80<r/max(g,1)<2.1 and .92<g/max(b,1)<2.0
            if not eligible:
                continue
            lum=.2126*r+.7152*g+.0722*b
            pixels[x,y]=tuple(round(min(255,lum*factor)) for factor in spec['rgb'])+(a,)
            changed+=1
    # The V-neck undercloth and narrow lower hem are neutral native atlas areas.
    # Keep the adjacent red/green patternTex owner-colour regions byte-identical.
    if 'collar_rgb' in spec:
        for y in range(70,256):
            for x in range(0,145):
                if not ((20<=x<110 and 70<=y<111) or y>=205):
                    continue
                mr,mg,mb=pattern[x,y]
                if (mr>100 and mr>1.4*mg and mr>1.4*mb) or (mg>100 and mg>1.4*mr and mg>1.4*mb):
                    continue
                r,g,b,a=pixels[x,y]
                if min(r,g,b)<=85 or max(r,g,b)-min(r,g,b)>=75:
                    continue
                lum=.2126*r+.7152*g+.0722*b
                pixels[x,y]=tuple(round(min(255,lum*factor)) for factor in spec['collar_rgb'])+(a,)
                changed+=1
    out=folder/'candidate-albedo.png'
    image.save(out)
    write(out.with_suffix('.json'),{'status':'palette_prepared_no_cook','source':str(source),
       'source_sha256':sha(source),'native_pattern':str(mask_path),'native_pattern_sha256':sha(mask_path),
       'output':str(out),'output_sha256':sha(out),'edited_pixels':changed,
       'changed_owner_mask_pixels':0,'native_player_colour':'unverified'})
    recipe.update({'preview_albedo':out.name,'donor_albedo_texture_id':spec['albedo']})
    recipe_path.write_text(json.dumps(recipe,indent=2)+'\n',encoding='utf8')
    print(name,changed,out)


if __name__=='__main__':
    for name,spec in SPECS.items():
        make(name,spec)
