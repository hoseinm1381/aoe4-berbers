"""Repaint decoded stock surface maps; retain native UVs, masks and team layers."""
import hashlib,json,math,subprocess,os
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter

ROOT=Path(__file__).resolve().parents[2]
ART=Path(__file__).resolve().parent
OUT=ROOT/'output/berber_update_0_2_2'
CORE=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/core/garrison-core.exe'
PROJECT=Path('E:/bh22/Mods/berber_house_022')
SCALE=.46
def run(label,args):
    result=subprocess.run([str(CORE),*map(str,args)],capture_output=True,text=True,encoding='utf-8',timeout=90)
    (OUT/(label+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
    assert result.returncode==0,(label,result.stderr)
def role(texture):
    name=texture.get('texture_name','').lower()+' '+texture.get('logical_path','').lower()
    if 'team' in name:return 'team'
    if 'trim' in name:return 'trim'
    for r in ('plaster','brick','wood','fabric','shingle'):
        if '/'+r+'/' in name:return r
    return 'retain'
def repaint(source,dest,kind,age):
    image=Image.open(source).convert('RGBA');pixels=image.load();w,h=image.size
    earth=[(162,107,65),(173,118,74),(186,137,91),(196,148,101)][age-1]
    if kind=='wood':base=(93+age*3,57+age*2,30+age)
    elif kind=='fabric':base=(175,139,98)
    elif kind=='trim':base=(170+age*5,111+age*4,65+age*3)
    elif kind=='shingle':base=(142,104,65)
    else:base=earth
    for y in range(h):
        for x in range(w):
            r,g,b,a=pixels[x,y];lum=(.2126*r+.7152*g+.0722*b)/255
            # Earthen brick loses the stock dressed-stone grid; other maps keep stock detail.
            detail=(.94+.045*math.sin(x*1.17+y*.81)+.025*math.sin(x*.043+y*.036)) if kind=='brick' else (.65+.45*lum)
            pixels[x,y]=tuple(max(0,min(255,round(c*detail))) for c in base)+(a,)
    if kind=='trim':
        draw=ImageDraw.Draw(image);unit=max(16,w//16);cy=h//2;radius=max(5,min(unit//3,h//6))
        ink=(92,52,28,255);light=(215,176,119,255)
        for x in range(unit//2,w,unit):
            draw.polygon([(x,cy-radius),(x+radius,cy),(x,cy+radius),(x-radius,cy)],fill=ink)
            draw.polygon([(x,cy-radius//2),(x+radius//2,cy),(x,cy+radius//2),(x-radius//2,cy)],fill=light)
        for yy in (cy-radius-4,cy+radius+4):draw.line([(0,yy),(w,yy)],fill=ink,width=max(1,h//128))
    dest.parent.mkdir(parents=True,exist_ok=True);image.save(dest)
    return {'width':w,'height':h,'source_sha256':hashlib.sha256(Path(source).read_bytes()).hexdigest(),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}

report={'schema':'berber.house-native-remix/v1','scale':SCALE,'ages':[],
 'geometry_policy':'stock topology and native buffers retained; uniform visual scaling through private house actor, mirrored in Blender',
 'construction_policy':'retain stock Abbasid selectors, collection palette, damage and team masks; no generic static recook',
 'native_acceptance':'pending user'}
for manifest in sorted((OUT/'stock').glob('*/decoded-static.json')):
    d=json.loads(manifest.read_text());age=int(d['request']['logical_path'].split('_age0')[-1].split('.')[0])
    textures={t['source']['sha256']:t for t in d['textures']}
    materials=[]
    for mat in d['material']['materials']:
        if mat['name'].endswith('_collection'):continue
        edits=[];params={};team=[]
        parameter_names={p['name'] for b in mat['blocks'] for p in b.get('parameters',[])}
        for block in mat['blocks']:
            slots={t['name']:t for t in block.get('textures',[])}
            for slot,t in slots.items():
                if not slot.startswith('albedoTex') or slot=='albedoTexCharred':continue
                kind=role(t)
                if kind=='team':team.append(slot);continue
                if kind=='retain':continue
                # Resolve projection by logical/native source path, not display name.
                candidates=[q for q in d['textures'] if q.get('texture_name')==t.get('texture_name')]
                if len(candidates)!=1:
                    candidates=[q for q in d['textures'] if Path(q['source']['path']).stem==Path(t['logical_path']).stem]
                assert len(candidates)==1,(age,mat['name'],slot)
                q=candidates[0];dds=Path(q.get('projection',{}).get('path',q.get('dds_path','')))
                if not dds.is_file():
                    choices=[p for p in (Path(d['cache_root'])/'textures').glob('*.dds') if q['source']['sha256'][:12] in p.name]
                    if not choices:choices=list((Path(d['cache_root'])/'textures').glob('*_'+Path(q['source']['path']).stem+'.dds'))
                    assert len(choices)==1,(age,slot,q.keys());dds=choices[0]
                png=ART/'textures'/f'age{age}_{mat["name"]}_{slot}_{kind}.png'
                info=repaint(dds,png,kind,age)
                layer=1 if slot=='albedoTex' else int(slot.removeprefix('albedoTex'))
                for label,c in [('highlight',1),('midtone',.84),('shadow',.60)]:
                    pname=f'{label}Color{layer}'
                    if pname in parameter_names:params[pname]=[c,c,c,1]
                edits.append({'slot':slot,'role':kind,'image':str(png),'source_logical_path':t['logical_path'],**info})
        name=f'house_age{age}' if mat['name']=='main' else f'textures_age{age}_{mat["name"]}'
        record=json.loads((PROJECT/'mod-project.json').read_text());existing={v['name'] for v in record.get('model_variants',[])}
        if name not in existing:run('variant-'+name,['mod-project','variant','--project',PROJECT,'--source',d['request']['logical_path'].removesuffix('.rgm'),'--name',name])
        for edit in edits:run(name+'-'+edit['slot'],['mod-project','variant-set','--project',PROJECT,'--name',name,'--slot',edit['slot'],'--image',edit['image']])
        # Parameters are applied later per material. Carrier slots only produce fresh native RRTextures.
        materials.append({'name':mat['name'],'carrier':name,'textures':edits,'parameters':params,'team_slots_preserved':team})
    assert any(m['name']=='main' for m in materials)
    report['ages'].append({'age':age,'decode':str(manifest),'source':d['request']['logical_path'],'source_hashes':{k:v['sha256'] for k,v in d['resources'].items() if isinstance(v,dict) and 'sha256' in v},'materials':materials})
report['ages'].sort(key=lambda a:a['age']);assert [r['age'] for r in report['ages']]==[1,2,3,4]
(ART/'recipe.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('HOUSE_TEXTURES_AND_NATIVE_VARIANTS_READY',sum(len(m['textures']) for a in report['ages'] for m in a['materials']))
