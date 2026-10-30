"""Freeze existing editable production references/requirements, never invent IDs."""
from pathlib import Path
import re,json,xml.etree.ElementTree as X
from concurrent.futures import ThreadPoolExecutor
from pipeline import ROOT,OUT,WORK,BASE,ARCH,run,extract,write,sha

INST=ROOT/'assets/attrib/instances'
def lua(v):
    if v is None:return 'nil'
    if isinstance(v,bool):return 'true' if v else 'false'
    if isinstance(v,(int,float)):return str(v)
    if isinstance(v,str):return json.dumps(v,ensure_ascii=True)
    if isinstance(v,list):return '{'+','.join(lua(x) for x in v)+'}'
    return '{'+','.join('['+lua(k)+']='+lua(x) for k,x in sorted(v.items()))+'}'
def role(n):
    for term,r in [('villager','villager'),('scout','scout'),('trade_cart','trader'),('mehari','mehari'),('sanhaja_ca','sanhaja'),('masmuda_cb','masmuda'),('spearman_tuareg','tuareg'),('horseman','zenata'),('archer','archer'),('monk','monk'),('imam','monk'),('ram','ram'),('trebuchet','treb'),('mangonel','mangonel'),('cannon','cannon')]:
        if term in n:return r
    return 'other'
def age(n):
    m=re.search(r'_(\d)(?:_|$)',n)
    return int(m[1]) if m and int(m[1]) in range(1,5) else 1
def requirement(e):
    reason=e.find('./enum[@name="reason"]')
    if reason is not None and reason.get('value')=='display':return True
    typ=e.get('value','').rsplit('\\',1)[-1]
    if typ=='required_player_upgrade':
        u=e.find('./instance_reference[@name="upgrade_name"]')
        b=e.find('./bool[@name="is_present"]')
        if u is None:return True
        return {'op':'upgrade','name':u.get('value').rsplit('\\',1)[-1],'present':b is None or b.get('value').lower()=='true'}
    if typ=='required_structure':
        u=e.find('./instance_reference[@name="structure_name"]')
        c=e.find('./int[@name="required_structure_count"]')
        complete=e.find('./bool[@name="require_construction_complete"]')
        if u is None:return True
        return {'op':'building','name':u.get('value').rsplit('\\',1)[-1],'count':int(c.get('value')) if c is not None else 1,'complete':complete is not None and complete.get('value').lower()=='true'}
    kids=[]
    for container in e:
        if container.tag in ('list','group'):
            for child in container:
                if child.tag=='template_reference':kids.append(requirement(child))
    if not kids:return True  # remaining conditions are enforced by normal engine commands
    return {'op':'not' if typ=='required_not' else 'any' if typ=='required_any_in_list' else 'all','items':kids}
def rootreq(rt,ext):
    for e in rt.findall('./list/template_reference'):
        if e.get('value','').endswith('\\'+ext):return requirement(e)
    return True
def rgdval(n,key,default=None):
    e=n.find('./RGDNode[@Key="'+key+'"]')
    return e.get('Value',default) if e is not None else default
def rgdref(n,key):
    e=n.find('./RGDNode[@Key="'+key+'"]/RGDNode[@Key="$PBGNAME"]')
    return e.get('Value','').split(':')[-1].rsplit('\\',1)[-1] if e is not None else None
def rgdreq(n):
    if n is None:return True
    if rgdval(n,'reason')=='display':return True
    kind=rgdval(n,'$REF',n.get('Key','')).rsplit('\\',1)[-1]
    if kind=='required_player_upgrade':
        present=rgdval(n,'is_present')
        name=rgdref(n,'upgrade_name')
        if present is None or not name:return {'op':'engine'}
        return {'op':'upgrade','name':name,'present':present=='true'}
    if kind=='required_structure':
        name=rgdref(n,'structure_name')
        if not name:return {'op':'engine'}
        return {'op':'building','name':name,'count':int(rgdval(n,'required_structure_count','1')),
                'complete':rgdval(n,'require_construction_complete','false')=='true'}
    if kind.startswith('required_') and kind not in ('required_not','required_all_in_list','required_any_in_list'):
        return {'op':'engine'}
    kids=[]
    for c in n.findall('./RGDNode'):
        if c.get('Type')=='List' and c.get('Key') in ('requirements','requirement_table'):
            kids.extend(rgdreq(x) for x in c.findall('./RGDNode') if x.get('Type')=='List')
    if not kids:return True
    return {'op':'not' if kind=='required_not' else 'any' if kind=='required_any_in_list' else 'all','items':kids}
def resolved_requirements(data):
    """Read native compiled values for inherited fields; never synthesize tuning XML."""
    official=Path('E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga')
    indexes={}
    for archive in [official,BASE]:
        listing=json.loads(run(ARCH,'list',archive))
        for entry in listing['members']:
            name=entry['path'];parts=name.replace('\\','/').split('/')
            if name.endswith('.rgd'):
                for category in ['ebps','sbps','upgrade']:
                    if category in parts:indexes[(category,Path(name).stem)]=(archive,name)
    wanted=[]
    for kind,category,ext in [('buildings','ebps','requirement_ext'),('squads','sbps','squad_requirement_ext'),('upgrades','upgrade','requirement_ext')]:
        for name,record in data[kind].items():
            location=indexes.get((category,name))
            if location is None:
                record['requirement']={'op':'engine'}
            else:wanted.append((kind,name,ext,*location))
    archives={}
    for _,_,_,archive,member in wanted:archives.setdefault(archive,[]).append(member)
    for archive,members in archives.items():extract(archive,WORK/'resolved'/archive.stem,members)
    def decode(row):
        kind,name,ext,archive,member=row
        p=WORK/'resolved'/archive.stem/member;xml=p.with_suffix('.decoded.xml')
        if not xml.exists():run(ARCH,'decode-rgd',p,xml)
        rt=X.parse(xml).getroot();node=rt.find('./RGDNode[@Key="default"]/RGDNode[@Key="'+ext+'"]')
        return kind,name,rgdreq(node),{'archive':str(archive),'member':member,'decoded_rgd_sha256':sha(p)}
    proof=[]
    with ThreadPoolExecutor(max_workers=8) as pool:
        for kind,name,req,evidence in pool.map(decode,wanted):
            data[kind][name]['requirement']=req;proof.append(evidence)
    return proof
def generate():
    data={'buildings':{},'squads':{},'upgrades':{}}
    evidence={}
    for f in sorted((INST/'ebps/races/malian/buildings').rglob('*.xml')):
        rt=X.parse(f).getroot();prod=[];ups=[]
        for ext in rt.findall('./list/template_reference'):
            if ext.get('value','').endswith('\\spawner_ext'):
                for e in ext.findall('.//group[@name="spawn_item"]/instance_reference[@name="squad"]'):
                    v=e.get('value','')
                    if v:prod.append(v.rsplit('\\',1)[-1])
            if ext.get('value','').endswith('\\upgrade_ext'):
                ups=[e.get('value').rsplit('\\',1)[-1] for e in ext.findall('.//instance_reference[@name="upgrade"]') if e.get('value')]
        data['buildings'][f.stem]={'squads':prod,'upgrades':ups,'requirement':rootreq(rt,'requirement_ext')}
        evidence[str(f.relative_to(ROOT))]=sha(f)
    for category,ext in [('sbps','squad_requirement_ext'),('upgrade','requirement_ext')]:
        for f in sorted((INST/category).rglob('*.xml')):
            if category=='sbps' and '/malian/' not in f.as_posix():continue
            rt=X.parse(f).getroot()
            entry={'age':age(f.stem),'requirement':rootreq(rt,ext)}
            if category=='sbps':entry['role']=role(f.stem)
            data['squads' if category=='sbps' else 'upgrades'][f.stem]=entry
            evidence[str(f.relative_to(ROOT))]=sha(f)
    # Existing inherited squads are named in the existing production tables.
    villager=INST/'sbps/races/malian/berbers/unit_villager_1_mal.xml'
    for e in X.parse(villager).getroot().findall('.//instance_reference[@name="ebp"]'):
        n=e.get('value','').rsplit('\\',1)[-1]
        if n:data['buildings'].setdefault(n,{'squads':[],'upgrades':[],'requirement':True})
    for b in data['buildings'].values():
        for name in b['squads']:
            data['squads'].setdefault(name,{'age':age(name),'role':role(name),'requirement':True})
        for name in b['upgrades']:
            a=age(name)
            if name.endswith('_iii'):a=4
            elif name.endswith('_ii'):a=3
            elif name.endswith('_i'):a=2
            data['upgrades'].setdefault(name,{'age':a,'requirement':True})
    compiled=resolved_requirements(data)
    dst=ROOT/'assets/scar/ai/berber_ai_catalog.scar'
    dst.parent.mkdir(parents=True,exist_ok=True)
    lines=['-- Production names from editable sources; inherited requirements resolved from native 0.9.1/official RGD.','-- Read-only decoding: no tuning records or speculative Attribute Editor XML authored.','BerberAI_Catalog = {buildings={}, squads={}, upgrades={}}']
    for kind,entries in data.items():
        for name,entry in sorted(entries.items()):lines.append('BerberAI_Catalog.'+kind+'['+lua(name)+'] = '+lua(entry))
    dst.write_text('\n'.join(lines)+'\n',encoding='utf8')
    write(OUT/'catalog-provenance.json',{'source_sha256':evidence,'resolved_native_requirements':compiled,'catalog_sha256':sha(dst),'counts':{k:len(v) for k,v in data.items()},'unknown_requirement_policy':'three-valued predicates defer unknown conditions to normal engine commands; no bypass'})
    print('Catalog:',{k:len(v) for k,v in data.items()})
if __name__=='__main__':generate()
