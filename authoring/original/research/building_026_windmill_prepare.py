"""Native Malian gristmill surface remix; isolated variant carriers."""
import os,sys,json,hashlib,subprocess,math
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]; ART=ROOT/'art/building_remix_0_2_6/windmill'
OUT=ROOT/'output/berber_update_0_2_6/authors/windmill'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
CORE=EXT/'bin/core/garrison-core.exe'; PROJECT=OUT/'l/Mods/bw026'
def run(name,args):
 p=subprocess.run([str(CORE),*map(str,args)],capture_output=True,text=True,encoding='utf8');(OUT/(name+'.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
decode=next((OUT/'stock').glob('*/decoded-static.json')); d=json.loads(decode.read_text()); materials=[]
for mat in d['material']['materials']:
 if mat['name'].endswith('_collection'):continue
 edits=[];params={};team=[];names={p['name'] for b in mat['blocks'] for p in b.get('parameters',[])}
 for block in mat['blocks']:
  for t in block.get('textures',[]):
   slot=t['name'];path=t.get('texture_name','').lower()
   if not slot.startswith('albedoTex') or slot=='albedoTexCharred':continue
   if 'team' in path:team.append(slot);continue
   role=next((r for r in ['wood','plaster','brick','fabric','shingle','building_kits'] if '/'+r+'/' in path),None)
   if role is None:continue
   q=next(q for q in d['textures'] if q.get('texture_name')==t.get('texture_name'))
   source=Path(q['projection']['path']);dest=ART/'textures'/f'{mat["name"]}_{slot}_{role}.png';dest.parent.mkdir(exist_ok=True)
   im=Image.open(source).convert('RGBA');p=im.load()
   base={'wood':(99,62,34),'plaster':(177,126,83),'brick':(159,104,63),'fabric':(180,145,103),'shingle':(174,117,73),'building_kits':(179,126,80)}[role]
   for y in range(im.height):
    for x in range(im.width):
     r,g,b,a=p[x,y];lum=(.2126*r+.7152*g+.0722*b)/255;detail=.65+.45*lum
     if mat['name']=='windmill' and slot in ('albedoTex2','albedoTex4'):base=(188,143,97);detail=.85+.18*lum
     if mat['name']=='windmill' and slot=='albedoTex':base=(75,45,24)
     p[x,y]=tuple(max(0,min(255,round(c*detail))) for c in base)+(a,)
   im.save(dest);layer=1 if slot=='albedoTex' else int(slot[9:])
   for label,c in [('highlight',1),('midtone',.84),('shadow',.60)]:
    pname=f'{label}Color{layer}'
    if pname in names:params[pname]=[c,c,c,1]
   edits.append({'slot':slot,'role':role,'image':str(dest),'source_logical_path':t['logical_path'],'source_sha256':sha(source),'sha256':sha(dest)})
 name='mill' if mat['name']=='main' else 'mill_'+mat['name']
 if name not in {v['name'] for v in json.loads((PROJECT/'mod-project.json').read_text()).get('model_variants',[])}:run('variant-'+name,['mod-project','variant','--project',PROJECT,'--source',d['request']['logical_path'][:-4],'--name',name])
 for e in edits:run(name+'-'+e['slot'],['mod-project','variant-set','--project',PROJECT,'--name',name,'--slot',e['slot'],'--image',e['image']])
 materials.append({'name':mat['name'],'carrier':name,'textures':edits,'parameters':params,'team_slots_preserved':team})
report={'schema':'berber.economy-native-remix/v1','building':'windmill','key':'bw026','project':str(PROJECT),'source':d['request']['logical_path'],'decode':str(decode),'scale':1.0,'materials':materials,'source_hashes':{k:v['sha256'] for k,v in d['resources'].items() if isinstance(v,dict) and 'sha256' in v},'state_policy':'Native common windmill age01 healthy family shared Ages I-IV. Native selectors, sail axle skeleton and motion RGO preserved; root retains stock auxiliary construction/wreck machinery.'}
(ART/'recipe.json').write_text(json.dumps(report,indent=2)+'\n');print('MILL_READY',len(materials),sum(len(m['textures']) for m in materials))
