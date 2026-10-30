"""Scoped native roof albedo recolour; retains donor tile grain and no owner masks."""
from pathlib import Path
import json,hashlib
from PIL import Image
from berber_040_integrate_cache import read_cached_json
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/building_remix_0_4_0/university';manifest=Path('F:/aoe_4_temp/berber_040_university_donors/c6fd053d393b6861f2d8/decoded-static.json');d=read_cached_json(manifest);rows=[]
for m in d['material']['materials']:
 if m['name']!='extra':continue
 for t in m['textures']:
  if t['name'] not in ('albedoTex2','albedoTex3'):continue
  p=Path(t['projection_path']);im=Image.open(p).convert('RGBA');pixels=[]
  for r,g,b,a in im.getdata():
   lum=(.2126*r+.7152*g+.0722*b)/255
   pixels.append((round(16+lum*50),round(38+lum*100),round(31+lum*62),a))
  im.putdata(pixels);dest=ART/f'green_tile_{t["name"]}.png';im.save(dest)
  rows.append({'material':'extra','slot':t['name'],'source_texture':t['logical_path'],'source_image_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'png':str(dest),'png_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'carrier':'university_green_'+t['name'].lower(),'preserve':'native tile grain, UV, normal/PBR, mask/owner and charred fields'})
(ART/'material-repaint.json').write_text(json.dumps(rows,indent=2))
