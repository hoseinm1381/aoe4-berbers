"""Earthen windmill housing repair; leave moving machinery and owner masks intact."""
import os,json,hashlib,subprocess,random
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/building_remix_0_2_6/windmill';OUT=ROOT/'output/berber_update_0_2_6/authors/windmill';EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 recipe=json.loads((ART/'recipe.json').read_text());d=json.loads(Path(recipe['decode']).read_text());mat=next(m for m in recipe['materials'] if m['name']=='windmill');stock=next(m for m in d['material']['materials'] if m['name']=='windmill');textures={t['name']:t for b in stock['blocks'] for t in b.get('textures',[])};proof=[]
 for slot,colour in [('albedoTex2',(211,167,114)),('albedoTex3',(176,126,84)),('albedoTex4',(211,168,119))]:
  edit=next(t for t in mat['textures'] if t['slot']==slot);original=Image.open(edit['image']).convert('RGBA');w,h=original.size;alpha=original.getchannel('A');rng=random.Random(2600+int(slot[-1]));image=Image.new('RGBA',(w,h));pix=[]
  for y in range(h):
   for x in range(w):
    grain=rng.uniform(-3,3)+2*((x*13+y*17)%29)/29;pix.append(tuple(max(0,min(255,round(c+grain))) for c in colour)+(255,))
  image.putdata(pix)
  if slot=='albedoTex2':
   draw=ImageDraw.Draw(image);mid=int(h*.24);unit=max(20,int(w/6));radius=max(7,int(h*.035));band=radius+max(3,int(h*.008));umber=(119,62,36,255);cream=(234,201,149,255);width=max(2,int(w*.008))
   for yy in [mid-band,mid+band]:draw.line((0,yy,w,yy),fill=umber,width=width);draw.line((0,yy+width,w,yy+width),fill=cream,width=max(1,width//2))
   for cx in range(0,w+unit,unit):
    shape=[(cx,mid-radius),(cx+radius,mid),(cx,mid+radius),(cx-radius,mid),(cx,mid-radius)];draw.line(shape,fill=umber,width=width,joint='curve');draw.rectangle((cx-width,mid-width,cx+width,mid+width),fill=cream)
  image.putalpha(alpha);path=Path(edit['image']);before=sha(path);image.save(path);edit['sha256']=sha(path);edit['role']='earthen_plaster_with_diamond_border' if slot=='albedoTex2' else 'earthen_plaster';edit['art_repair']='Suppress stock plank/shingle texture; subtle plaster grain. Wall layer2 carries repeated restrained diamond border in its actual native UV tile.'
  assert Image.open(path).getchannel('A').tobytes()==alpha.tobytes()
  p=subprocess.run([str(EXT/'bin/core/garrison-core.exe'),'mod-project','variant-set','--project',recipe['project'],'--name',mat['carrier'],'--slot',slot,'--image',str(path)],capture_output=True,text=True);(OUT/('art-repair-'+slot+'.log')).write_text(p.stdout+p.stderr);assert p.returncode==0
  proof.append({'slot':slot,'before_albedo_sha256':before,'after_albedo_sha256':sha(path),'alpha_dimensions_preserved':True})
 overrides={}
 for suffix in ['2','3']:
  for prefix in ['normalMap','metalTex']:
   slot=prefix+suffix;source=textures[prefix+'6'];overrides[slot]=source['logical_path'];proof.append({'slot':slot,'before_native_reference':textures[slot]['logical_path'],'after_native_reference':source['logical_path'],'source':'Existing stock native plaster layer6 packed resource, unchanged channel bytes'})
 mat['native_texture_overrides']=overrides;recipe['art_direction']='Earthen plaster housing and cap with restrained dark-umber and cream diamond wall band, native timber supports/machinery and team trim retained.';recipe['housing_pbr_override_allowlist']=list(overrides)
 (ART/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n');(OUT/'art-repair-source.json').write_text(json.dumps({'status':'prepared','building':'windmill','proof':proof,'sails_axle_geometry_native_masks_team_charred':'all unchanged','fresh_cook':'pending granted root slot'},indent=2)+'\n');print('WINDMILL_ART_REPAIR_PREPARED')
if __name__=='__main__':main()
