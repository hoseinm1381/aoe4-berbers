"""Compose per-material native mill payload after an evidenced fresh cook."""
import os,sys,json,hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];ART=Path(__file__).parent;OUT=ROOT/'output/berber_update_0_2_5/authors/mill'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';sys.path[:0]=[str(EXT.parent),str(ART)]
from garrison.garrison_shared import model_variants as mv,relic_chunky as rc
from native_materials import rewrite_scoped
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
recipe=json.loads((ART/'recipe.json').read_text());project=Path(recipe['project']);record=json.loads((project/'mod-project.json').read_text());cook=record['cooks'][-1]
assert not cook['live_reload'] and sha(cook['archive'])==cook['sha256']
readback=OUT/'cook-readback';p=subprocess.run([str(EXT/'bin/sga-archiver.exe'),'unpack',cook['archive'],'--output',str(readback)],capture_output=True,text=True);(OUT/'unpack.log').write_text(p.stdout+p.stderr);assert p.returncode==0
d=json.loads(Path(recipe['decode']).read_text());raw=Path(d['material']['source']['path']).read_bytes();edits={};files=[];payload=OUT/'payload'
def save(member,data):
 p=payload/member;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);files.append({'member':member,'file':str(p),'sha256':sha(p)})
for m in recipe['materials']:
 textures={e['slot']:mv.texture_member(recipe['key'],m['carrier'],e['slot'])+'.rrtex' for e in m['textures']}
 edits[m['name']]={'textures':textures,'parameters':{k:list(map(str,v)) for k,v in m['parameters'].items()}}
 for member in textures.values():save(member,(readback/member).read_bytes())
scoped=rewrite_scoped(raw,edits);stem=mv.art_stem(recipe['key'],'mill').replace('\\','/')
for ext in ['.rgm','.rgo','.rrgeom']:save(stem+ext,(readback/(stem+ext)).read_bytes())
assert sha(readback/(stem+'.rrgeom'))==d['resources']['geometry']['sha256']
save(stem+'.rrmaterial',scoped)
originals={c.decoded_name:c for c in rc.parse(raw).roots};updated={c.decoded_name:c for c in rc.parse(scoped).roots}
for name,c in originals.items():
 key=name.removesuffix('_collection');pack=lambda c:rc.pack_document([rc.pack_chunk(c.kind,c.tag,c.payload,name=c.name,version=c.version)])
 before=mv.material_slots(pack(c));after=mv.material_slots(pack(updated[name]))
 for slot,value in before['textures'].items():
  if slot not in edits.get(key,{}).get('textures',{}):assert after['textures'][slot]==value,(name,slot)
 for param,value in before['parameters'].items():
  if param not in edits.get(key,{}).get('parameters',{}):assert after['parameters'][param]==value,(name,param)
report={'status':'passed','building':'mill','cook':cook,'source_model':recipe['source'].removesuffix('.rgm'),'private_model':stem,'model_mapping':{recipe['source'].removesuffix('.rgm'):stem},'payloads':files,'geometry_buffers_byte_identical':True,'unaltered_native_slots_byte_semantic_identical':True,'team_normals_masks_charred_preserved':True,'age_progression':'single native age01 model stock Ages I-IV','construction_auxiliary_stamps':['art/stamps/const_dest/const_house_wood_d','art/stamps/const_dest/dest_house_stone_d'],'healthy_stamp':'art/stamps/civ_mal/mal_gristmill','native_runtime':'pending user'}
(OUT/'integration-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('MILL_PAYLOAD_PASSED',len(files))

