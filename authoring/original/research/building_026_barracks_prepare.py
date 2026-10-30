"""Prepare native model variants and deduplicated albedo carriers; no stock edits."""
import os,json,hashlib,subprocess
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/building_remix_0_2_6/barracks';OUT=ROOT/'output/berber_update_0_2_6/authors/barracks';KEY='bb026';PROJECT=OUT/'l/Mods'/KEY
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';CORE=EXT/'bin/core/garrison-core.exe'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(label,args):
 p=subprocess.run([str(CORE),*map(str,args)],capture_output=True,text=True,encoding='utf8');(OUT/(label+'.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,(label,p.stderr)
def main():
 if not (PROJECT/'mod-project.json').exists():run('create-project',['mod-project','create','--library',OUT/'l','--name',KEY])
 donors=[m for m in json.loads((ART/'donors.json').read_text()) if '/structures/' in m['source']];known={v['name'] for v in json.loads((PROJECT/'mod-project.json').read_text()).get('model_variants',[])};palette={};models=[]
 for model in donors:
  d=json.loads(Path(model['decode']).read_text());name=f"barracks_age{model['age']}"
  if name not in known:run('variant-'+name,['mod-project','variant','--project',PROJECT,'--source',model['source'][:-4],'--name',name]);known.add(name)
  mats=[]
  for mat in d['material']['materials']:
   if mat['name'].endswith('_collection'):continue
   names={p['name'] for b in mat['blocks'] for p in b.get('parameters',[])};edits=[];params={};team=[]
   for block in mat['blocks']:
    for tex in block.get('textures',[]):
     slot=tex['name'];logical=tex.get('logical_path','');semantic=tex.get('texture_name','').lower()
     if not slot.startswith('albedoTex') or slot=='albedoTexCharred':continue
     if 'team' in semantic:team.append(slot);continue
     role=next((x for x in ['wood','plaster','brick','stone','fabric','shingle','building_kits'] if '/'+x+'/' in semantic),None)
     if not role:continue
     source=next(t for t in d['textures'] if t.get('texture_name')==tex.get('texture_name'));png=Path(source['projection']['path']);pid=sha(png)[:18]
     if pid not in palette:
      carrier='palette_'+pid;dest=ART/'textures'/f'{role}_{pid}.png';dest.parent.mkdir(exist_ok=True)
      im=Image.open(png).convert('RGBA');base={'wood':(88,55,32),'plaster':(178,127,85),'brick':(163,109,74),'stone':(190,162,121),'fabric':(175,138,95),'shingle':(163,120,76),'building_kits':(176,132,89)}[role]
      pixels=[]
      for red,green,blue,alpha in im.getdata():
       detail=.68+.40*(.2126*red+.7152*green+.0722*blue)/255;pixels.append(tuple(round(v*detail) for v in base)+(alpha,))
      im.putdata(pixels);im.save(dest)
      if carrier not in known:run('variant-'+carrier,['mod-project','variant','--project',PROJECT,'--source',donors[0]['source'][:-4],'--name',carrier]);known.add(carrier)
      run('texture-'+carrier,['mod-project','variant-set','--project',PROJECT,'--name',carrier,'--slot','albedoTex','--image',dest])
      palette[pid]={'carrier':carrier,'image':str(dest),'image_sha256':sha(dest),'source_image':str(png),'source_sha256':sha(png),'source_logical_path':logical,'role':role}
     edits.append({'slot':slot,**palette[pid]})
     layer=1 if slot=='albedoTex' else int(slot.removeprefix('albedoTex'))
     for tone,value in [('highlight',1),('midtone',.84),('shadow',.60)]:
      key=f'{tone}Color{layer}'
      if key in names:params[key]=[value,value,value,1]
   mats.append({'name':mat['name'],'textures':edits,'parameters':params,'team_slots_preserved':team})
  models.append({**model,'name':name,'materials':mats,'native_geometry':str(ART/(name+'.rrgeom')),'remix_decode':str(ART/(name+'-remix-projection.json'))})
 recipe={'schema':'berber.native-building-remix/v1','building':'barracks','key':KEY,'project':str(PROJECT),'scale':1.0,'models':models,'palettes':list(palette.values()),'geometry_policy':'Preserve x/y and all positions at/below z=3.5. Continuously lower existing upper roof/parapet by 30 percent with smooth one-meter transition. Common pier models untouched; native shoreline deck anchors and launch paths retained.','state_policy':'Age-specific dock control donors only, never combined duplication. Full common pier donors retained with native selectors and stamp transforms; repeated dock props remain stock dependencies.'}
 (ART/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n');print('TC_PREPARED',len(models),'native components',len(palette),'shared textures')
if __name__=='__main__':main()
