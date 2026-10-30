"""Material-only native mining remix: no topology or shared assets are edited."""
import os,sys,json,hashlib,subprocess,math,io,struct
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]; ART=ROOT/'art/building_remix_0_2_6/outpost';OUT=ROOT/'output/berber_update_0_2_6/authors/outpost'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';CORE=EXT/'bin/core/garrison-core.exe'
PROJECT=OUT/'l/Mods/bo026';KEY='bo026'
ART.mkdir(parents=True,exist_ok=True)
def run(label,args):
 p=subprocess.run([str(CORE),*map(str,args)],capture_output=True,text=True,encoding='utf8',timeout=180);(OUT/(label+'.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,(label,p.stderr)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def role(t):
 n=(t.get('texture_name','')+' '+t.get('logical_path','')).lower()
 if 'team' in n:return 'team'
 for k in ['wood','fabric','plaster','shingle','brick','trim','building_kits']:
  if '/'+k+'/' in n:return k
 if '/structures/stone/' in n:return 'earth'
 return 'retain'
def repaint(src,dest,kind):
 im=Image.open(src).convert('RGBA');px=im.load()
 base={'wood':(104,64,35),'fabric':(174,138,94),'plaster':(180,126,79),'earth':(174,116,71),'shingle':(143,101,62),'brick':(177,120,74),'trim':(149,91,49),'building_kits':(113,76,41)}[kind]
 for y in range(im.height):
  for x in range(im.width):
   r,g,b,a=px[x,y];lum=(.2126*r+.7152*g+.0722*b)/255;detail=.65+.45*lum
   px[x,y]=tuple(round(c*detail) for c in base)+(a,)
 dest.parent.mkdir(parents=True,exist_ok=True);im.save(dest)
 return {'width':im.width,'height':im.height,'source_sha256':sha(src),'sha256':sha(dest)}
ps=list((OUT/'stock').glob('*/decoded-static.json'))
report={'schema':'berber.economy-native-remix/v1','building':'outpost','project':str(PROJECT),'key':KEY,'scale':1,'models':[],'native_acceptance':'pending user','geometry_policy':'donor main masonry geometry moderately reshaped; topology/UV/state preserved; misc weapon components roof markers and complete native transforms retained'}
preview_paths={}
for p in ps:
 d=json.loads(p.read_text());model=Path(d['request']['logical_path']).stem;name='stone' if model.endswith('upgrade_stone') else 'base';materials=[]
 for t in d['textures']:
  src=Path(t['projection']['path']);dest=ART/'preview-projections'/(t['source']['sha256']+'.png');dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():
   raw=bytearray(src.read_bytes())
   if raw[84:88]==b'DX10':
    fmt=struct.unpack_from('<I',raw,128)[0]
    if fmt in (72,75,78):struct.pack_into('<I',raw,128,fmt-1) # identical BC pixel decoder; Blender sets original colour space.
   Image.open(io.BytesIO(raw)).save(dest)
  preview_paths[str(src)]=str(dest)
 for i,m in enumerate(x for x in d['material']['materials'] if not x['name'].endswith('_collection')):
  carrier=name if i==0 else name+'_m'+str(i);edits=[];params={};team=[];parameters={q['name'] for b in m['blocks'] for q in b.get('parameters',[])}
  existing={v['name'] for v in json.loads((PROJECT/'mod-project.json').read_text()).get('model_variants',[])}
  if carrier not in existing:run('variant-'+carrier,['mod-project','variant','--project',PROJECT,'--source',d['request']['logical_path'][:-4],'--name',carrier])
  for t in [t for b in m['blocks'] for t in b.get('textures',[]) if t['name'].startswith('albedoTex') and t['name']!='albedoTexCharred']:
   k=role(t);slot=t['name']
   if k=='team':team.append(slot);continue
   if k=='retain':continue
   q=[q for q in d['textures'] if q.get('texture_name')==t.get('texture_name')];assert len(q)==1,(model,m['name'],slot)
   src=Path(q[0]['projection']['path']);png=ART/'textures'/f'{name}_{i}_{slot}_{k}.png';info=repaint(src,png,k)
   run(carrier+'-'+slot,['mod-project','variant-set','--project',PROJECT,'--name',carrier,'--slot',slot,'--image',png])
   layer=1 if slot=='albedoTex' else int(slot.removeprefix('albedoTex'))
   for label,c in [('highlight',1),('midtone',.84),('shadow',.6)]:
    if f'{label}Color{layer}' in parameters:params[f'{label}Color{layer}']=[c,c,c,1]
   edits.append({'slot':slot,'role':k,'image':str(png),'source_logical_path':t['logical_path'],**info})
  materials.append({'name':m['name'],'carrier':carrier,'textures':edits,'parameters':params,'team_slots_preserved':team})
 report['models'].append({'name':name,'decode':str(p),'source':d['request']['logical_path'],'source_hashes':{k:v['sha256'] for k,v in d['resources'].items() if isinstance(v,dict) and 'sha256'in v},'materials':materials})
(ART/'recipe.json').write_text(json.dumps(report,indent=2)+'\n');print('READY',[(x['name'],sum(len(m['textures']) for m in x['materials'])) for x in report['models']])
(ART/'preview-projections/paths.json').write_text(json.dumps(preview_paths,indent=2)+'\n')
