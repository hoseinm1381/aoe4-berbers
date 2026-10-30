"""Independently compare repair scope against the original native material roots."""
import os,sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/building_remix_0_2_6/windmill';OUT=ROOT/'output/berber_update_0_2_6/authors/windmill';EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';sys.path[:0]=[str(EXT),str(ROOT/'art/economy_remix_0_2_5/mill')]
from garrison_shared import model_variants as mv,relic_chunky as rc
import garrison_shared;sys.modules['garrison.garrison_shared']=garrison_shared;sys.path.insert(0,str(EXT.parent));from native_materials import rewrite_scoped
r=json.loads((ART/'recipe.json').read_text());d=json.loads(Path(r['decode']).read_text());raw=Path(d['material']['source']['path']).read_bytes();edits={}
for m in r['materials']:
 textures={e['slot']:mv.texture_member(r['key'],m['carrier'],e['slot'])+'.rrtex' for e in m['textures']};textures.update(m.get('native_texture_overrides',{}));edits[m['name']]={'textures':textures,'parameters':{k:list(map(str,v)) for k,v in m['parameters'].items()}}
expected=rewrite_scoped(raw,edits);a=rc.parse(raw);b=rc.parse(expected);rows=[]
for old,new in zip(a.roots,b.roots):
 assert (old.tag,old.name,old.version)==(new.tag,new.name,new.version);key=old.decoded_name.removesuffix('_collection');pack=lambda c:rc.pack_document([rc.pack_chunk(c.kind,c.tag,c.payload,name=c.name,version=c.version)]);x=mv.material_slots(pack(old));y=mv.material_slots(pack(new));spec=edits.get(key,{})
 assert set(x['textures'])==set(y['textures']) and set(x['parameters'])==set(y['parameters'])
 for slot,value in x['textures'].items():
  if slot in spec.get('textures',{}):assert y['textures'][slot].replace('\\','/')==spec['textures'][slot].replace('\\','/')
  else:assert value==y['textures'][slot]
 for p,value in x['parameters'].items():
  if p not in spec.get('parameters',{}):assert y['parameters'][p]==value
 restored=mv.rewrite_material(pack(new),{k:x['textures'][k] for k in spec.get('textures',{})},{k:x['parameters'][k]['values'] for k in spec.get('parameters',{})});assert rc.parse(restored).roots[0].payload==old.payload
 rows.append({'root':old.decoded_name,'all_nonallowlisted_native_bytes_restored_exact':True,'protected_owner_layer5_normal_metal_and_masks':key!='windmill' or all(x['textures'][k]==y['textures'][k] for k in ['albedoTex5','normalMap5','metalTex5','maskTex2','maskTex5','normalMapCharred','metalTexCharred','albedoTexCharred'])})
note={'status':'source_passed_fresh_cook_pending','expected_scoped_material_sha256':hashlib.sha256(expected).hexdigest(),'native_roots':rows,'housing_normal_metal_allowlist':r['housing_pbr_override_allowlist'],'protected_native_geometry_sha256':hashlib.sha256((ART/'native-remix.rrgeom').read_bytes()).hexdigest(),'scope':'Source-bound scoped material proof only; no fresh cook claim.'};(OUT/'art-repair-native-check.json').write_text(json.dumps(note,indent=2)+'\n');print(json.dumps(note))
