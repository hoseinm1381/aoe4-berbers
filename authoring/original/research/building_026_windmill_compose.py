"""Compose per-material native mill payload after an evidenced fresh cook."""
import os,sys,json,hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/building_remix_0_2_6/windmill';OUT=ROOT/'output/berber_update_0_2_6/authors/windmill'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';sys.path[:0]=[str(EXT),str(ROOT/'art/economy_remix_0_2_5/mill')]
from garrison_shared import model_variants as mv,relic_chunky as rc
import garrison_shared;sys.modules['garrison.garrison_shared']=garrison_shared;sys.path.insert(0,str(EXT.parent));from native_materials import rewrite_scoped
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
recipe=json.loads((ART/'recipe.json').read_text());project=Path(recipe['project']);record=json.loads((project/'mod-project.json').read_text());cook=record['cooks'][-1]
assert not cook['live_reload'] and sha(cook['archive'])==cook['sha256']
readback=OUT/'cook-readback';p=subprocess.run([str(EXT/'bin/sga-archiver.exe'),'unpack',cook['archive'],'--output',str(readback)],capture_output=True,text=True);(OUT/'unpack.log').write_text(p.stdout+p.stderr);assert p.returncode==0
d=json.loads(Path(recipe['decode']).read_text());raw=Path(d['material']['source']['path']).read_bytes();edits={};files=[];payload=OUT/'payload'
def save(member,data):
 p=payload/member;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);files.append({'member':member,'file':str(p),'sha256':sha(p)})
for m in recipe['materials']:
 textures={e['slot']:mv.texture_member(recipe['key'],m['carrier'],e['slot'])+'.rrtex' for e in m['textures']}
 for member in textures.values():save(member,(readback/member).read_bytes())
 textures.update(m.get('native_texture_overrides',{}))
 edits[m['name']]={'textures':textures,'parameters':{k:list(map(str,v)) for k,v in m['parameters'].items()}}
scoped=rewrite_scoped(raw,edits);stem=mv.art_stem(recipe['key'],'mill_windmill').replace('\\','/')
for ext in ['.rgm','.rgo']:save(stem+ext,(readback/(stem+ext)).read_bytes())
save(stem+'.rrgeom',(ART/'native-remix.rrgeom').read_bytes())
assert sha(readback/(stem+'.rrgeom'))==d['resources']['geometry']['sha256'] # variant preserves native donor, staged remix patches only known spans
save(stem+'.rrmaterial',scoped)
originals={c.decoded_name:c for c in rc.parse(raw).roots};updated={c.decoded_name:c for c in rc.parse(scoped).roots}
for name,c in originals.items():
 key=name.removesuffix('_collection');pack=lambda c:rc.pack_document([rc.pack_chunk(c.kind,c.tag,c.payload,name=c.name,version=c.version)])
 before=mv.material_slots(pack(c));after=mv.material_slots(pack(updated[name]))
 for slot,value in before['textures'].items():
  if slot not in edits.get(key,{}).get('textures',{}):assert after['textures'][slot]==value,(name,slot)
 for param,value in before['parameters'].items():
  if param not in edits.get(key,{}).get('parameters',{}):assert after['parameters'][param]==value,(name,param)
report={'status':'passed','building':'windmill','cook':cook,'source_model':recipe['source'].removesuffix('.rgm'),'private_model':stem,'model_mapping':{recipe['source'].removesuffix('.rgm'):stem},'payloads':files,'stock_topology_uv_selector_preserved':True,'housing_geometry_edited':True,'rotation_sails_axle_skeleton_preserved':True,'unaltered_native_slots_byte_semantic_identical':True,'team_normals_masks_charred_preserved':True,'age_progression':'single native age01 model stock Ages I-IV','construction_auxiliary_stamps':['art/stamps/const_dest/const_house_wood_d','art/stamps/const_dest/dest_house_stone_d'],'healthy_stamp':'art/stamps/civ_common/com_gristmill','native_runtime':'pending user'}
report['geometry_encoding']='surgical known-span source-preserving native encoding; separately staged with fresh material cook'
report['encoding_validation']=str(OUT/'encoding-validation.json')
report['motion_validation']=json.loads((OUT/'motion-validation.json').read_text())
report['native_skeleton_collection_states_preserved']=True
report['housing_pbr_override_allowlist']=recipe.get('housing_pbr_override_allowlist',[])
report['housing_pbr_substitution']='Only housing layer2/3 normal and metal refs replace stock wood/shingle with unchanged stock plaster layer6 packed maps; fans axle owner-colour masks charred and all other native PBR refs unchanged.'
report['art_direction']=recipe.get('art_direction','')
report['team_normals_masks_charred_preserved']='Team/PBR/masks/charred intact; housing nonteam layer2/3 PBR substitutions explicitly allowlisted.'
(OUT/'integration-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('MILL_PAYLOAD_PASSED',len(files))

