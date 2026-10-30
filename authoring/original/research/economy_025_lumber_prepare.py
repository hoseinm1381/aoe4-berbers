import os,json,hashlib,subprocess,sys
from pathlib import Path
from PIL import Image
import numpy as np
R=Path.cwd(); O=R/'output/berber_update_0_2_5/authors/lumber';ART=R/'art/economy_remix_0_2_5/lumber';ART.mkdir(parents=True,exist_ok=True)
G=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';CORE=G/'bin/core/garrison-core.exe';P=O/'library/Mods/berber_lumber_025'
def run(label,args):
 x=subprocess.run([str(CORE),*map(str,args)],capture_output=True,text=True);(O/(label+'.log')).write_text(x.stdout+x.stderr);assert x.returncode==0,(label,x.stderr)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
report={'schema':'berber.economy-native-remix/v1','building':'lumber','project':str(P),'key':'berber_lumber_025','native_acceptance':'pending user','geometry_policy':'native stock buffers and transform preserved','models':[]}
for manifest in sorted((O/'stock').glob('*/decoded-static.json')):
 d=json.loads(manifest.read_text());name=Path(d['request']['logical_path']).stem;record={'name':name,'source':d['request']['logical_path'],'decode':str(manifest),'source_hashes':{k:v['sha256'] for k,v in d['resources'].items() if isinstance(v,dict) and 'sha256' in v},'materials':[]}
 for mat in d['material']['materials']:
  if mat['name'].endswith('_collection'):continue
  edits=[];team=[];params={};pn={p['name'] for b in mat['blocks'] for p in b.get('parameters',[])}
  for b in mat['blocks']:
   for t in b.get('textures',[]):
    slot=t['name'];tn=t.get('texture_name','').lower()
    if 'team' in tn:team.append(slot);continue
    if not slot.startswith('albedoTex') or slot=='albedoTexCharred':continue
    kind='wood' if '/wood/' in tn else 'fabric' if '/fabric/' in tn else 'earth' if '/grout/' in tn else None
    if not kind:continue
    q=next(q for q in d['textures'] if q.get('texture_name')==t.get('texture_name'))
    src=Path(q.get('projection',{}).get('path',q.get('dds_path','')))
    if not src.is_file():src=next((Path(d['cache_root'])/'textures').glob(q['source']['sha256'][:12]+'*.dds'))
    arr=np.array(Image.open(src).convert('RGBA'));lum=(arr[:,:,:3].astype(float)*np.array([.2126,.7152,.0722])).sum(axis=2)/255
    base=np.array((103,67,36) if kind=='wood' else (185,144,94) if kind=='fabric' else (177,120,72))
    arr[:,:,:3]=np.clip(base[None,None,:]*(.65+.45*lum[:,:,None]),0,255).astype('uint8')
    dest=ART/'textures'/f'{name}_{mat["name"]}_{slot}_{kind}.png';dest.parent.mkdir(exist_ok=True);Image.fromarray(arr).save(dest)
    layer=1 if slot=='albedoTex' else int(slot[9:])
    for label,c in [('highlight',1),('midtone',.84),('shadow',.60)]:
     key=f'{label}Color{layer}'
     if key in pn:params[key]=[c,c,c,1]
    edits.append({'slot':slot,'role':kind,'image':str(dest),'source_logical_path':t['logical_path'],'source_sha256':sha(src),'sha256':sha(dest),'width':arr.shape[1],'height':arr.shape[0]})
  carrier=name if not record['materials'] else name+'_'+mat['name']
  run('variant-'+carrier,['mod-project','variant','--project',P,'--source',record['source'].removesuffix('.rgm'),'--name',carrier])
  for e in edits:run(carrier+'-'+e['slot'],['mod-project','variant-set','--project',P,'--name',carrier,'--slot',e['slot'],'--image',e['image']])
  record['materials'].append({'name':mat['name'],'carrier':carrier,'textures':edits,'parameters':params,'team_slots_preserved':team})
 report['models'].append(record)
(ART/'recipe.json').write_text(json.dumps(report,indent=2));print('LUMBER_RECIPE_READY',len(report['models']))
