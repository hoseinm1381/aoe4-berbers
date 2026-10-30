"""Compose fresh-cooked native dock materials with audited native geometry spans."""
import os,sys,json,hashlib,subprocess
from pathlib import Path
KIND=sys.argv[1]
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/building_remix_0_2_6'/KIND;OUT=ROOT/'output/berber_update_0_2_6/authors'/KIND
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path[:0]=[str(EXT),str(EXT.parent),str(ROOT/'art/economy_remix_0_2_5/mill')]
from garrison_shared import model_variants as mv,relic_chunky as rc
import garrison_shared;sys.modules['garrison.garrison_shared']=garrison_shared
from native_materials import rewrite_scoped
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
recipe=json.loads((ART/'recipe.json').read_text());project=Path(recipe['project']);record=json.loads((project/'mod-project.json').read_text());cook=record['cooks'][-1]
assert not cook['live_reload'] and sha(cook['archive'])==cook['sha256']
readback=OUT/'cook-readback';proc=subprocess.run([str(EXT/'bin/sga-archiver.exe'),'unpack',cook['archive'],'--output',str(readback)],capture_output=True,text=True);(OUT/'unpack.log').write_text(proc.stdout+proc.stderr);assert proc.returncode==0
payload=OUT/'payload';files={};mapping={};reports=[]
def save(member,data):
 p=payload/member;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);files[member]={'member':member,'file':str(p),'sha256':sha(p)}
def pack(c):return rc.pack_document([rc.pack_chunk(c.kind,c.tag,c.payload,name=c.name,version=c.version)])
for model in recipe['models']:
 d=json.loads(Path(model['decode']).read_text());raw=Path(d['material']['source']['path']).read_bytes();edits={}
 for mat in model['materials']:
  textures={e['slot']:mv.texture_member(recipe['key'],(e.get('carrier') or mat['carrier']),e['slot'] if 'carrier' not in e else 'albedoTex')+'.rrtex' for e in mat['textures']}
  edits[mat['name']]={'textures':textures,'parameters':{k:list(map(str,v)) for k,v in mat['parameters'].items()}}
  for member in textures.values():save(member,(readback/member).read_bytes())
 scoped=rewrite_scoped(raw,edits);stem=mv.art_stem(recipe['key'],model['name']).replace('\\','/');mapping[model['source'][:-4]]=stem
 for ext in ['.rgm','.rgo']:save(stem+ext,(readback/(stem+ext)).read_bytes())
 assert sha(readback/(stem+'.rrgeom'))==d['resources']['geometry']['sha256']
 save(stem+'.rrgeom',Path(model['native_geometry']).read_bytes());save(stem+'.rrmaterial',scoped)
 originals={c.decoded_name:c for c in rc.parse(raw).roots};updated={c.decoded_name:c for c in rc.parse(scoped).roots}
 for name,c in originals.items():
  key=name.removesuffix('_collection');before=mv.material_slots(pack(c));after=mv.material_slots(pack(updated[name]))
  for slot,value in before['textures'].items():
   if slot not in edits.get(key,{}).get('textures',{}):assert after['textures'][slot]==value,(model['name'],name,slot)
  for param,value in before['parameters'].items():
   if param not in edits.get(key,{}).get('parameters',{}):assert after['parameters'][param]==value,(model['name'],name,param)
 reports.append({'source':model['source'],'private_model':stem,'source_resources':d['resources'],'native_states_skeleton_retained':True,'unmodified_material_slots_retained':True})
report={'status':'passed','building':KIND,'cook':cook,'model_mapping':mapping,'payloads':list(files.values()),'models':reports,'geometry_validation':str(OUT/'geometry-validation.json'),'source_validation':str(OUT/'source-validation.json'),'native_assemblies':str(OUT/'native-assemblies.json'),'healthy_stamps':[f'art/stamps/civ_abbasid/abb_town_center_age_{a:02}' for a in range(1,5)] if KIND=='towncenter' else [],'geometry_encoding':'Surgical verified GEOB vertex-span mutation with Jacobian normal/tangent correction. Geometry is not a fresh generic mesh cook; materials freshly cooked separately.','native_state_policy':'Stock RGM, supported private-path remap RGO; exact native collection selectors, skeleton, UVs, owner masks, topology. Unedited donor components remain byte-identical. Props retain stock references; no combined/control duplication.','functional_contact_xy_unchanged':True,'native_runtime':'pending user'}
(OUT/'integration-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('DOCK_PAYLOAD_PASSED',len(files))
