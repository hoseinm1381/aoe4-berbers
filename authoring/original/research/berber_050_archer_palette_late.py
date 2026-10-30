"""Age-specific non-owner-cloth albedo edits for Abbasid Archer III and IV."""
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image

from berber_050_common import ART, OUT, sha, write

SLOTS = {
    3: {'albedo':'8252009409485253944','pattern':'12218805086250933380',
        'regions':[(0,320,42,119),(414,512,0,215)], 'rgb':(.54,.70,.47),
        'name':'abb_archer_age3_candidate'},
    4: {'albedo':'14462100637664812810','pattern':'6898269205743828884',
        'regions':[(0,355,225,356),(0,255,370,512)], 'rgb':(.44,.57,.76),
        'name':'abb_archer_age4_candidate'},
}


def make(age):
    slot=SLOTS[age]
    donors=json.loads((OUT/'donors.json').read_text(encoding='utf8'))
    donor=next(item for item in donors['families']['archer_abbasid_alternatives']['donors'] if item['age']==age)
    folder=Path(donor['decoded_manifest']).parent/'textures'
    source=next(folder.glob('*'+slot['albedo']+'*'))
    pattern_path=next(folder.glob('*'+slot['pattern']+'*'))
    image=Image.open(source).convert('RGBA')
    mask=Image.open(pattern_path).convert('RGB')
    assert image.size==mask.size==(512,512)
    src=image.load();owner=mask.load();changed=0
    for y in range(512):
        for x in range(512):
            if not any(x0<=x<x1 and y0<=y<y1 for x0,x1,y0,y1 in slot['regions']):
                continue
            mr,mg,mb=owner[x,y]
            if (mr>100 and mr>1.4*mg and mr>1.4*mb) or (mg>100 and mg>1.4*mr and mg>1.4*mb):
                continue
            r,g,b,a=src[x,y]
            if not (r>45 and .87<r/max(g,1)<1.85 and 1.08<g/max(b,1)<1.9):
                continue
            lum=.2126*r+.7152*g+.0722*b
            src[x,y]=tuple(round(min(255,lum*factor)) for factor in slot['rgb'])+(a,)
            changed+=1
    out=ART/'pilots'/slot['name']/'candidate-albedo.png'
    out.parent.mkdir(parents=True,exist_ok=True)
    image.save(out)
    write(out.with_suffix('.json'),{'status':'palette_prepared_no_cook',
        'source':str(source),'source_sha256':sha(source),'native_pattern':str(pattern_path),
        'native_pattern_sha256':sha(pattern_path),'output':str(out),'output_sha256':sha(out),
        'edited_pixels':changed,'changed_owner_mask_pixels':0,'slot':'albedoTexture',
        'native_player_colour':'unverified'})
    recipe_path=out.parent/'recipe.json';recipe=json.loads(recipe_path.read_text(encoding='utf8'))
    recipe.update({'preview_albedo':out.name,'donor_albedo_texture_id':slot['albedo']})
    recipe_path.write_text(json.dumps(recipe,indent=2)+'\n',encoding='utf8')
    print(age,out,changed)


if __name__=='__main__':
    for age in (3,4):make(age)
