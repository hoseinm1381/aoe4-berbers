import os,sys,json,subprocess,hashlib
from pathlib import Path
R=Path.cwd();O=R/'output/berber_update_0_2_5/authors/lumber';ART=R/'art/economy_remix_0_2_5/lumber';G=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';sys.path.insert(0,str(G));sys.path.insert(0,str(R/'art/house_remix_0_2_2'))
from garrison_shared import model_variants as mv,relic_chunky as rc
from native_materials import rewrite_scoped
recipe=json.loads((ART/'recipe.json').read_text());P=Path(recipe['project']);rec=json.loads((P/'mod-project.json').read_text());cook=rec['cooks'][-1];assert not cook['live_reload'];archive=Path(cook['archive']);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(archive)==cook['sha256'];unpack=O/'cook-readback'/sha(archive)[:16]
subprocess.run([str(G/'bin/sga-archiver.exe'),'unpack',str(archive),'--output',str(unpack)],check=True,capture_output=True)
report={'status':'passed','building':'lumber','cook':cook,'models':[],'payloads':[],'geometry_policy':'native model buffers preserved; materials only','native_acceptance':'pending user'}
def save(member,raw):
 p=O/'payload'/member;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);report['payloads'].append({'member':member,'file':str(p),'sha256':sha(p)})
for row in recipe['models']:
 d=json.loads(Path(row['decode']).read_text());stock=Path(d['material']['source']['path']).read_bytes();edits={}
 for m in row['materials']:
  paths={e['slot']:mv.texture_member(recipe['key'],m['carrier'],e['slot'])+'.rrtex' for e in m['textures']};edits[m['name']]={'textures':paths,'parameters':{k:list(map(str,v)) for k,v in m['parameters'].items()}}
  for member in paths.values():save(member,(unpack/member).read_bytes())
 scoped=rewrite_scoped(stock,edits);stem=mv.art_stem(recipe['key'],row['name']).replace('\\','/')
 for ext in ['.rgm','.rgo','.rrgeom']:save(stem+ext,(unpack/(stem+ext)).read_bytes())
 assert sha(unpack/(stem+'.rrgeom'))==d['resources']['geometry']['sha256'];save(stem+'.rrmaterial',scoped)
 orig={c.decoded_name:c for c in rc.parse(stock).roots};after={c.decoded_name:c for c in rc.parse(scoped).roots}
 one=lambda c:rc.pack_document([rc.pack_chunk(c.kind,c.tag,c.payload,version=c.version,name=c.name)])
 for m in row['materials']:
  for n in [m['name'],m['name']+'_collection']:
   if n not in orig:continue
   a=mv.material_slots(one(orig[n]));b=mv.material_slots(one(after[n]));changed=edits[m['name']]['textures'];params=edits[m['name']]['parameters']
   for slot,v in a['textures'].items():assert slot in changed or b['textures'][slot]==v,(n,slot)
   for slot,v in a['parameters'].items():assert slot in params or b['parameters'][slot]==v,(n,slot)
 report['models'].append({'source':row['source'].removesuffix('.rgm'),'private':stem,'geometry_sha256':sha(unpack/(stem+'.rrgeom')),'unchanged_geometry':True,'unchanged_masks_normals_team_and_charred':True})
(O/'delivery.json').write_text(json.dumps(report,indent=2));print('LUMBER_NATIVE_PAYLOAD_READY',len(report['payloads']))
