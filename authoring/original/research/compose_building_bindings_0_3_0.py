"""Visual-only compiled bindings using installed Garrison RGD codec.

Private identities come from Garrison's generated building recipes. Existing
actor gameplay is preserved. The complete recipe and semantic diffs are retained.
"""
import os,sys,json,copy,subprocess,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_3_0'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT));from garrison_shared import rgd
ARCH=EXT/'bin/sga-archiver.exe';GUID='1d3145e8f1b2427f8bb0067851fcf0f1'
OFFICIAL=Path(r'E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga')
batch=json.loads((ROOT/'Design/asset_overhaul/BUILDINGS_BATCH.json').read_text(encoding='utf-8'))
inv=json.loads((OUT/'official-inventory.json').read_text());stock={r['path'].lower():r['path'] for r in inv['members']}
base=OUT/'baseline-readback';donor=OUT/'donor-readback';payload=OUT/'bindings';payload.mkdir(exist_ok=True)
report={'status':'running','families':[],'payloads':[],'semantic_preservation':[]}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def obtain(member):
    member=member.replace('\\','/').lower()
    if (base/member).exists():return base/member
    assert member in stock,member
    path=OUT/'official'/member;path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():subprocess.run([str(ARCH),'extract-member',str(OFFICIAL),stock[member],str(path)],stdout=subprocess.DEVNULL,check=True)
    return path
def load(member):return rgd.read(obtain(member).read_bytes())
def node(nodes,path):return rgd.find(nodes,path)
def value(nodes,path):
    n=node(nodes,path);return n.value if n else None
def child(parent,key):return next((n for n in parent.value if n.key==key),None)
def put(nodes,path,val):
    n=node(nodes,path);assert n is not None,path;n.value=val
def reference(parent,name):
    put(parent.value,'$PBGNAME',GUID+':'+name);put(parent.value,'$PBGMAP',r'attachments\attachment_lists')
def semantic(nodes):
    return [(n.key,n.hash,n.kind,semantic(n.value) if isinstance(n.value,list) else n.value) for n in nodes]
def save(member,document):
    keys={h:k for h,k in document.keys}
    for _,n in rgd.flatten(document.nodes):
        if n.key is not None:keys[n.hash]=n.key
    document.keys=list(keys.items())
    data=rgd.write(document);assert semantic(rgd.read(data).nodes)==semantic(document.nodes)
    path=payload/member;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    report['payloads'].append({'member':member,'file':str(path),'sha256':sha(path)})
def resolve_ref(name,family):
    target=name.split(':')[-1].lower()+'.rgd'
    local=[p for p in base.rglob(target) if p.relative_to(base).as_posix().startswith('attrib/'+family+'/')]
    if ':' in name and local:
        assert len(local)==1,(name,local);return local[0].relative_to(base).as_posix()
    options=[p for p in stock if p.startswith('attrib/'+family+'/') and p.endswith('/'+target)]
    assert len(options)==1,(name,options);return options[0]
def actor_members(row):
    result=['attrib/'+p.replace('\\','/').removeprefix('assets/attrib/instances/').removesuffix('.xml')+'.rgd' for p in row['source_paths']]
    if not result:result=['attrib/'+p.replace('\\','/')+'.rgd' for p in row['blueprint_targets']]
    # The live Fez construction command still uses the stock flat path. Bind
    # that active actor visually as well; no command/gameplay changes.
    if row['key']=='fez':result.append('attrib/ebps/races/malian/buildings/building_landmark_age3_landmarke_mal.rgd')
    return list(dict.fromkeys(result))
for row in batch['rows']:
    if row['id']=='building.tent':continue
    key=row['key'];ages=row['ages'];members=actor_members(row);assert members,key
    original=load(members[0]);first_table=next(n for n in original.nodes if n.kind=='List' and n.key!='instance_version')
    original_ext=node(first_table.value,'tier_ext')
    if original_ext:
        groups=node(original_ext.value,'tier_group_list');group=groups.value[0]
        original_tiers=[n for n in group.value if n.key=='tier'];seed=original_tiers[0]
        names=[value(n.value,'attachments/$PBGNAME') for n in original_tiers]
    else:
        generated=rgd.read((donor/f'attrib/ebps/garrison/berber_buildings_030/{key}_age{ages[0]}.rgd').read_bytes())
        original_ext=node(generated.nodes,'default/tier_ext');groups=node(original_ext.value,'tier_group_list');group=groups.value[0]
        seed=group.value[0]
        main=value(first_table.value,'entity_blueprint_ext/animator_attachments/$PBGNAME');assert main,(key,'No visual root')
        names=[main]
    replacements=[]
    for age in ages:
        name=f'{key}_age{age}_tier';generated_member=f'attrib/attachments/attachment_lists/garrison/berber_buildings_030/{name}.rgd'
        allocated=rgd.read((donor/generated_member).read_bytes())
        candidates=[n for n in names if n]
        actual=next((n for n in candidates if 'tier'+str(age)+'_' in n.lower()),candidates[min(len(candidates)-1,ages.index(age))])
        tier=load(resolve_ref(actual,'attachments/attachment_lists'))
        changed=0
        for table in [n for n in tier.nodes if n.kind=='List' and n.key!='instance_version']:
            identity=value(allocated.nodes,'default/pbgid');put(table.value,'pbgid',identity)
            attachment=node(table.value,'attachment_lists/attachment_lists')
            if attachment:
                for entry in attachment.value:
                    listing=node(entry.value,'attachment_list')
                    if listing is None:continue
                    stamps=[n for n in listing.value if value(n.value,'$REF')==r'options\attachment_types\stamp_attachment']
                    if stamps:
                        put(stamps[0].value,'stamp',rf'art\stamps\garrison\berber_buildings_030\{key}_age{age}');changed+=1
                    else:
                        animators=[n for n in listing.value if node(n.value,'animator') is not None]
                        if animators:
                            put(animators[0].value,'animator',rf'art\scenario\garrison\berber_buildings_030\buildings\{key}_age{age}\model');changed+=1
            parent=node(table.value,'parent_pbg')
            if parent:
                for n in parent.value:
                    if n.kind=='CString':n.value=''
        assert changed,(key,age,actual,'No supported stamp/model visual field')
        save(generated_member,tier);replacements.append(name)
    for member in members:
        actor=load(member);before=copy.deepcopy(actor)
        for table in [n for n in actor.nodes if n.kind=='List' and n.key!='instance_version']:
            ext=node(table.value,'tier_ext')
            if ext is None:
                ext=copy.deepcopy(original_ext);table.value.append(ext)
            group_list=node(ext.value,'tier_group_list');first=group_list.value[0]
            fresh=[]
            for i,(age,name) in enumerate(zip(ages,replacements)):
                item=copy.deepcopy(seed);reference(node(item.value,'attachments'),name)
                req=node(item.value,'statetree_tier_requirements_pbg')
                if req:
                    put(req.value,'$PBGNAME','' if i==0 else {2:'feudal_age',3:'castle_age',4:'imperial_age'}[age]);put(req.value,'$PBGMAP','' if i==0 else 'upgrade')
                for field in ('statetree_tier_pgb_upgrade_target_entity','statetree_tier_pgb_upgrade_target_squad'):
                    ref=node(item.value,field)
                    if ref:
                        for n in ref.value:
                            if n.kind=='CString':n.value=''
                action=node(item.value,'tier_attachment_action')
                if action:action.value=''
                fresh.append(item)
            first.value=fresh
            if key in ('tlemcen','funduq','wonder'):
                scale=node(table.value,'entity_blueprint_ext/animator_scale')
                if scale:scale.value=100.0
        def nonvisual(doc):
            for table in [n for n in doc.nodes if n.kind=='List']:
                table.value=[n for n in table.value if n.key!='tier_ext']
                scale=node(table.value,'entity_blueprint_ext/animator_scale')
                if scale:scale.value=0.0
            return semantic(doc.nodes)
        assert nonvisual(copy.deepcopy(actor))==nonvisual(before),(key,member,'Nonvisual fields changed')
        save(member,actor)
        report['semantic_preservation'].append({'member':member,'all_nonvisual_fields':'unchanged'})
    report['families'].append({'key':key,'ages':ages,'actors':members,'private_tiers':replacements})
    (OUT/'bindings-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('BOUND',key,ages,flush=True)
report['status']='passed';(OUT/'bindings-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('ALL_BUILDING_BINDINGS_READY',flush=True)
