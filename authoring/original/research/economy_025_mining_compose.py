"""Selective media payload from a fresh Garrison cook; root owns bindings/package."""
import os,sys,json,hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/economy_remix_0_2_5/mining';OUT=ROOT/'output/berber_update_0_2_5/authors/mining'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';sys.path.insert(0,str(EXT.parent));sys.path.insert(0,str(ROOT/'art/house_remix_0_2_2'))
from garrison import garrison_shared as shared
sys.modules['garrison_shared']=shared
from garrison.garrison_shared import model_variants as mv,relic_chunky as rc
from native_materials import rewrite_scoped
r=json.loads((ART/'recipe.json').read_text());proj=Path(r['project']);record=json.loads((proj/'mod-project.json').read_text());cook=record['cooks'][-1];archive=Path(cook['archive'])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert cook['sha256']==sha(archive) and not cook['live_reload'];donor=OUT/'cook-readback'/sha(archive)[:16]
if not donor.exists():subprocess.run([str(EXT/'bin/sga-archiver.exe'),'unpack',str(archive),'--output',str(donor)],check=True,capture_output=True)
payload=OUT/'payload';report={'status':'running','building':'mining','cook':cook,'models':[],'mapping':{},'payloads':[]}
def save(member,data):
 p=payload/member;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);report['payloads'].append({'member':member,'file':str(p),'sha256':sha(p)})
for row in r['models']:
 if row['name']!='combined':continue # Exact stock stamp closure: standalone parts would duplicate equipment.
 d=json.loads(Path(row['decode']).read_text());raw=Path(d['material']['source']['path']).read_bytes();edits={}
 for m in row['materials']:
  textures={e['slot']:mv.texture_member(r['key'],m['carrier'],e['slot'])+'.rrtex' for e in m['textures']};edits[m['name']]={'textures':textures,'parameters':{k:list(map(str,v)) for k,v in m['parameters'].items()}}
  for member in textures.values():save(member,(donor/member).read_bytes())
 scoped=rewrite_scoped(raw,edits);stem=mv.art_stem(r['key'],row['name']).replace('\\','/')
 for ext in ['.rgm','.rgo','.rrgeom']:save(stem+ext,(donor/(stem+ext)).read_bytes())
 assert sha(donor/(stem+'.rrgeom'))==d['resources']['geometry']['sha256'];save(stem+'.rrmaterial',scoped)
 originals={c.decoded_name:c for c in rc.parse(raw).roots};modified={c.decoded_name:c for c in rc.parse(scoped).roots}
 for m in row['materials']:
  for name in [m['name'],m['name']+'_collection']:
   if name not in originals:continue
   one=lambda c:rc.pack_document([rc.pack_chunk(c.kind,c.tag,c.payload,name=c.name,version=c.version)])
   before=mv.material_slots(one(originals[name]));after=mv.material_slots(one(modified[name]))
   for slot,value in before['textures'].items():
    if slot not in edits[m['name']]['textures']:assert after['textures'][slot]==value,(row['name'],name,slot)
   for param,value in before['parameters'].items():
    if param not in edits[m['name']]['parameters']:assert after['parameters'][param]==value,(row['name'],name,param)
   for slot in m['team_slots_preserved']:
    layer=1 if slot=='albedoTex' else int(slot.removeprefix('albedoTex'))
    for label in ['highlight','midtone','shadow']:
     k=f'{label}Color{layer}'
     if k in before['parameters']:assert after['parameters'][k]==before['parameters'][k]
 report['models'].append({'name':row['name'],'source':row['source'][:-4],'private':stem,'geometry_sha256':sha(donor/(stem+'.rrgeom')),'unchanged_geometry':True,'unchanged_masks_normals_team_and_charred':True,'native_geometry_byte_preserved':True,'masks_normals_team_charred_and_unedited_maps_preserved':True,'materials':row['materials']})
 report['mapping'][row['source'][:-4]]=stem
report['status']='passed';report['model_mapping']=report['mapping'];report['native_acceptance']='pending user'
for filename in ['integration.json','delivery.json','integration-manifest.json']:(OUT/filename).write_text(json.dumps(report,indent=2)+'\n')
print('MINING_PAYLOAD_VALIDATED',len(report['payloads']))
