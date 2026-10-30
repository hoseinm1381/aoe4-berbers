from pathlib import Path
import json
from PIL import Image,ImageDraw
import numpy as np
R=Path(__file__).resolve().parents[1];e=next(x for x in json.loads((R/'art/unit_remix_0_5_0/mounted/mounted-manifest.json').read_text())['variants'] if x['private_variant_name']=='mehari_age02');d=json.loads((R/e['decoded_manifest']).read_text());m=next(m for m in d['material']['materials'] if m['name']=='rider_lod1');ts={t['name']:t for t in m['textures']};a=Image.open(ts['albedoTexture']['projection_path']).convert('RGB');p=Image.open(ts['patternTex']['projection_path']).convert('RGB');canvas=Image.new('RGB',(1024,560),'#ddd');canvas.paste(a,(0,40));canvas.paste(p,(512,40));dr=ImageDraw.Draw(canvas);dr.text((10,10),'Native donor albedo: brown collar continuous with leather vest',fill='black');dr.text((524,10),'Native pattern RGB: green=skin; collar black',fill='black');o=R/'art/unit_skin_0_5_1/mounted/mehari_age02/collar-donor-pattern-audit.png';canvas.save(o)
# Atlas collar on front/back vest around shoulders, outside chainmail and plates.
coords=[(26,145),(45,159),(169,116),(187,148),(286,110),(354,140)];arr=np.array(p);print([(xy,arr[xy[1],xy[0]].tolist()) for xy in coords]);print(o)
