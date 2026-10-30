from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw
from berber_050_model_payloads import atlas_jobs
R=Path(__file__).resolve().parents[1];O=R/'art/unit_skin_0_5_1/mounted/zenata_age04'; S=R/'art/unit_remix_0_5_0/mounted/zenata_age04/rider-albedo.png'
a=np.array(Image.open(S).convert('RGBA')); region=Image.new('L',(512,512));p=ImageDraw.Draw(region)
p.polygon([(9,7),(126,7),(125,55),(110,76),(99,62),(79,61),(65,64),(46,63),(32,71),(15,65)],fill=255)
p.polygon([(13,175),(124,174),(132,196),(109,212),(34,211),(9,198)],fill=255)
p.polygon([(333,163),(350,151),(367,156),(373,168),(392,153),(408,165),(425,155),(443,167),(461,154),(474,177),(477,222),(334,223)],fill=255)
r,g,b=[a[:,:,i].astype(float) for i in range(3)];m=(np.array(region)>0)&(r>90)&(g>62)&(b>43)&(r>g*1.12)&(g>b*1.05)
e=next(x for x in json.loads((R/'art/unit_remix_0_5_0/mounted/mounted-manifest.json').read_text())['variants'] if x['private_variant_name']=='zenata_age04');d=json.loads((R/e['decoded_manifest']).read_text());mat=next(x for x in d['material']['materials'] if any(t.get('logical_path')==e['albedo_variants'][0]['source_texture'] for t in x['textures']));pt=next(t for t in mat['textures'] if t['name']=='patternTex');pat=np.array(Image.open(pt['projection_path']).convert('RGBA'));owner=pat[:,:,0]>127;hair=pat[:,:,2]>127;m &= ~owner & ~hair
out=a.copy();shade=np.clip((.299*r+.587*g+.114*b)/125,.42,1.18)
for i,v in enumerate((225,188,163)):out[:,:,i][m]=np.clip(v*shade[m],0,255).astype('uint8')
O.mkdir(parents=True,exist_ok=True);Image.fromarray(out).save(O/'rider-albedo.png');Image.fromarray((m*255).astype('uint8')).save(O/'skin-mask.png')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest(); changed=np.any(a!=out,axis=2)
row={'family':'zenata','age':4,'target_texture':next(x for x in atlas_jobs(e) if x['image'].resolve()==S.resolve())['private_texture'],'source_png':str(S.relative_to(R)),'source_png_sha256':sha(S),'authored_png':str((O/'rider-albedo.png').relative_to(R)),'sha256':sha(O/'rider-albedo.png'),'mask_png':str((O/'skin-mask.png').relative_to(R)),'mask_sha256':sha(O/'skin-mask.png'),'source_owner_pattern':pt['projection_path'],'source_owner_pattern_sha256':sha(pt['projection_path']),'changed_pixels':int(changed.sum()),'changes_outside_skin_mask':int((changed&~m).sum()),'changed_owner_pixels':int((changed&owner).sum()),'changed_alpha_pixels':int((a[:,:,3]!=out[:,:,3]).sum()),'target_base_rgb':[225,188,163],'shade_rule':'native luminance / 125 clamped .42..1.18; UV-bounded warm skin pixels only; native owner red and hair blue excluded'}
(O.parent/'zenata-skin-manifest.json').write_text(json.dumps({'textures':[row]},indent=2)); print(json.dumps(row,indent=2))
