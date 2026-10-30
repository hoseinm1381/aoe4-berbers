"""Selective approved-art production integration with durable rollback and proof."""
import sys,os,json,hashlib,shutil,subprocess,copy,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_2_0'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
CORE=EXT/'bin/core/garrison-core.exe';ARCH=EXT/'bin/sga-archiver.exe'
GUID='1d3145e8f1b2427f8bb0067851fcf0f1';VERSION='0.2.0'
PROJECT=Path('E:/bt20/Mods/berber_tent_art_020')
ACCEPTED=ROOT/'output/tuareg_lowprofile_shield_trial/candidate'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path,data):
    Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def run(label,args,timeout=1200):
    with (OUT/(label+'.log')).open('w',encoding='utf-8') as log:
        p=subprocess.run([str(x) for x in args],stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
    assert p.returncode==0,(label,p.returncode)
    return (OUT/(label+'.log')).read_text(encoding='utf-8')
def inventory(archive,label):return json.loads(run(label,[ARCH,'list',archive,'--verify']))
def serialize(path,root):
    ET.indent(root,space='\t');ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
def sources():return [ROOT/'Berber_future_kingdom.aoe4mod',*[p for p in (ROOT/'assets').rglob('*') if p.is_file()]]
def backup():
    baseline=OUT/'source-baseline.json'
    assert not baseline.exists(),'Preserve existing integration; do not repeat backup over edited production.'
    rows={p.relative_to(ROOT).as_posix():sha(p) for p in sources()}
    for rel in rows:
        dest=OUT/'rollback'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,dest)
    archive=ROOT/'archives/Berber_future_kingdom.sga'
    shutil.copy2(archive,OUT/'rollback/Berber_future_kingdom.sga')
    write(baseline,rows);write(OUT/'rollback-record.json',{'production_archive_sha256':sha(archive),'source_files':len(rows),'guid':GUID})
    art=ROOT/'art/tribal_tent/iterations/002/iteration.json';approved=read(art)
    assert sha(ROOT/approved['blend'])==approved['blend_sha256']
    approved.update(approval_status='accepted',approved_on='2026-10-12',approval_scope='User approved iteration 002 style and requested the Berber update build.',age_approvals={str(i):'accepted' for i in range(1,5)})
    write(art,approved)
    history=read(ROOT/'Design/asset_overhaul/tribal_tent/ITERATIONS.json');history['accepted_iteration']='002';history['iterations']=[approved if r['iteration']=='002' else r for r in history['iterations']];write(ROOT/'Design/asset_overhaul/tribal_tent/ITERATIONS.json',history)
    print('PRODUCTION_BACKUP_AND_TENT_APPROVAL_SAVED',flush=True)
def tuareg():
    assert (OUT/'source-baseline.json').exists()
    approved=read(ROOT/'Design/asset_overhaul/BUILD_MANIFEST.json')['approved_assets'][0]
    archive=ROOT/approved['reference_package']['archive'];assert sha(archive)==approved['reference_package']['archive_sha256']
    changed=[]
    for age in range(1,5):
        rel=f'assets/attrib/instances/ebps/races/malian/units/unit_spearman_tuareg_{age}_ber.xml'
        old=ET.parse(ROOT/rel).getroot();new=ET.parse(ACCEPTED/rel).getroot()
        # Exact structural equality after removing only the known presentation references.
        def normalized(root):
            for node in root.iter('instance_reference'):
                if node.get('name') in ('animator_attachments','schema'):
                    node.attrib.pop('mod',None);node.set('value','VISUAL_REFERENCE')
            return ET.tostring(root)
        assert normalized(old)==normalized(new),('Unexpected accepted/current gameplay drift',rel)
        shutil.copy2(ACCEPTED/rel,ROOT/rel);changed.append(rel)
    private=['statemodel_schema/garrison/tuareg_posture_schema/tuareg_shield_posture_ber.xml']
    private += [f'attachments/attachment_lists/garrison/tuareg_shield_assets/tuareg_shield_tier{a}_ber.xml' for a in range(1,5)]
    private += [f'attachments/attachment_lists/garrison/tuareg_weapon_lists/tuareg_spear_visual_{i}.xml' for i in range(1,6)]
    for tail in private:
        rel='assets/attrib/instances/'+tail;dest=ROOT/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        src=ACCEPTED/rel;assert src.exists();shutil.copy2(src,dest);changed.append(rel)
    module='assets/scar/Units/tuareg_q_art_guard_trial.scar'
    assert not (ROOT/module).exists();shutil.copy2(ACCEPTED/module,ROOT/module);changed.append(module)
    gm=ROOT/'assets/scar/winconditions/berber_future_kingdom_GM.scar';raw=gm.read_bytes()
    marker=b'import("Units/tuareg_voice_profile.scar")';assert raw.count(marker)==1
    newline=b'\r\n' if b'\r\n' in raw else b'\n'
    gm.write_bytes(raw.replace(marker,marker+newline+b'import("Units/tuareg_q_art_guard_trial.scar")'));changed.append(gm.relative_to(ROOT).as_posix())
    inv=inventory(archive,'accepted-tuareg-inventory')
    media=[r['path'] for r in inv['members'] if any(r['path'].lower().startswith(p) for p in approved['retained_media_prefixes'])]
    assert sum(p.endswith('.rrgeom') for p in media)==6
    for member in media:
        dest=ROOT/'assets'/member;dest.parent.mkdir(parents=True,exist_ok=True)
        run('tuareg-extract',[ARCH,'extract-member',archive,member,dest]);changed.append('assets/'+member)
    write(OUT/'tuareg-port.json',{'status':'passed','approved_archive_sha256':sha(archive),'changed_sources':changed,'media':media,'Q':'accepted stock guard; moving delay retained','voices':'unchanged'})
    print('TUAREG_ACCEPTED_ART_PORTED',flush=True)
def tent_art():
    export=read(OUT/'tent-export.json');assert export['status']=='passed'
    for age in export['ages']:
        run(f'tent-age{age["age"]}-add',[CORE,'mod-project','building','--project',PROJECT,'--source',age['source'],'--name',f'berber_tent_age{age["age"]}','--profile','english-house','--integration','script'])
    editor=Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe'
    run('tent-art-cook',[CORE,'mod-project','cook','--project',PROJECT,'--editor',editor,'--timeout','900'])
    record=read(PROJECT/'mod-project.json');cook=record['cooks'][-1]
    assert not cook['live_reload'] and sha(cook['archive'])==cook['sha256']
    write(OUT/'tent-art-build.json',{'status':'passed','project':str(PROJECT),'cook':cook})
    print('TENT_ART_COOKED',flush=True)
def tent_recook():
    editor=Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe'
    run('tent-art-final-cook',[CORE,'mod-project','cook','--project',PROJECT,'--editor',editor,'--timeout','900'])
    cook=read(PROJECT/'mod-project.json')['cooks'][-1]
    assert not cook['live_reload'] and sha(cook['archive'])==cook['sha256']
    inv=inventory(cook['archive'],'tent-final-inventory');assert inv['archive']['name'].replace('-','').lower()==GUID
    write(OUT/'tent-art-build.json',{'status':'passed','project':str(PROJECT),'cook':cook})
    print('TENT_ART_FINAL_IDENTITY_COOKED',flush=True)
def tent_port():
    art=read(OUT/'tent-art-build.json');assert art['status']=='passed'
    archive=Path(art['cook']['archive']);assert sha(archive)==art['cook']['sha256']
    inv=inventory(archive,'tent-port-inventory')
    tier_prefix='attrib/attachments/attachment_lists/garrison/berber_tent_art_020/'
    prefixes=['art/scenario/garrison/berber_tent_art_020/buildings/','art/stamps/garrison/berber_tent_art_020/']
    members=[r['path'] for r in inv['members'] if r['path'].startswith(tier_prefix) or any(r['path'].startswith(p) for p in prefixes)]
    assert len([p for p in members if p.endswith('.rrgeom')])==4
    assert len([p for p in members if p.startswith(tier_prefix)])==4
    for member in members:
        dest=ROOT/'assets'/member;dest.parent.mkdir(parents=True,exist_ok=True);run('tent-extract',[ARCH,'extract-member',archive,member,dest])
    # Copy the current project's editor-serialized age group, retaining its item identities.
    tent=ROOT/'assets/attrib/instances/ebps/races/malian/buildings/tent/building_hut_ayy.xml'
    root=ET.parse(tent).getroot();house=ET.parse(ROOT/'assets/attrib/instances/ebps/races/malian/buildings/building_house_mal.xml').getroot()
    for ext in root.iter('template_reference'):
        if ext.get('value')=='ebpextensions\\entity_blueprint_ext':
            ref=ext.find("instance_reference[@name='animator_attachments']");assert ref is not None
            ref.set('value',r'attachments\attachment_lists\races\core\buildings\building_house');ref.attrib.pop('mod',None)
        if ext.get('value')=='ebpextensions\\statemodel_ext':
            ref=ext.find("instance_reference[@name='schema']");assert ref is not None
            ref.set('value',r'statemodel_schema\buildings\house');ref.attrib.pop('mod',None)
    tier=next(x for x in root.findall('./list/template_reference') if x.get('value')==r'ebpextensions\tier_ext')
    old_list=tier.find("list[@name='tier_group_list']");old_group=old_list.find("list[@name='tier_group']")
    group_id=old_group.get('List.ItemID');first_id=old_group.find("group[@name='tier']").get('List.ItemID')
    template=next(x for x in house.findall('./list/template_reference') if x.get('value')==r'ebpextensions\tier_ext').find("list[@name='tier_group_list']/list[@name='tier_group']")
    group=copy.deepcopy(template);group.set('List.ItemID',group_id)
    for age,entry in enumerate(group.findall("group[@name='tier']"),1):
        if age==1:entry.set('List.ItemID',first_id)
        ref=entry.find("instance_reference[@name='attachments']")
        ref.set('value',rf'attachments\attachment_lists\garrison\berber_tent_art_020\berber_tent_age{age}_tier');ref.set('mod',GUID)
    assert len(group.findall("group[@name='tier']"))==4
    for child in list(old_list):old_list.remove(child)
    old_list.append(group);serialize(tent,root)
    write(OUT/'tent-port.json',{'status':'passed','source':tent.relative_to(ROOT).as_posix(),'members':members,'age_requirements':['','upgrade/dev/ages/feudal_age','upgrade/dev/ages/castle_age','upgrade/dev/ages/imperial_age'],'visual_profile':'English House construction and state schema; Tent gameplay extensions retained','custom_damage_geometry':False,'owner_colour':'pattern source retained; static object material keeps original red/ochre palette'})
    print('TENT_FOUR_AGE_VISUALS_PORTED',flush=True)
def production_cook():
    # Model media and generated attachment RGDs are already cooked; the editor compiles current editable production.
    editor=Path(r'E:/Games/steamapps/common/Age of Empires IV/EssenceEditor.exe')
    build=OUT/('production-build-v2' if (OUT/'production-build').exists() else 'production-build');assert not build.exists()
    for folder in ('logs','output','intermediate'):(build/folder).mkdir(parents=True,exist_ok=True)
    args=[editor,'-rtm','--safe_settings','--do_not_restore','--quiet_crash_report','--no_source_control','--log_path',build/'logs','--build_mod',ROOT/'Berber_future_kingdom.aoe4mod','--no_burn_window','--burn_verbose_log_level','--burn_cache_type','Local','--burn_max_threads','1','--burn_log_path',build/'logs/burn.log','--build_path',build/'output','--intermediate_path',build/'intermediate']
    write(OUT/'production-build.json',{'status':'running','command':[str(a) for a in args]})
    startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=subprocess.SW_HIDE
    with (build/'logs/stdout.log').open('w') as a,(build/'logs/stderr.log').open('w') as b:
        result=subprocess.run([str(x) for x in args],cwd=editor.parent,stdout=a,stderr=b,startupinfo=startup,timeout=900)
    archives=list((build/'output').rglob('*.sga'))
    write(OUT/'production-build.json',{'status':'passed' if result.returncode==0 else 'failed','exit_code':result.returncode,'archives':[{'path':str(a),'sha256':sha(a)} for a in archives]})
    assert result.returncode==0 and len(archives)==1
    print('BERBER_PRODUCTION_COOK_PASSED',flush=True)
def register_tent_identities():
    # Register generator-owned identities with the Content Editor. Full visual lists
    # remain Garrison-derived compiled resources; never reconstruct their RGD fields.
    archive=Path(read(OUT/'tent-art-build.json')['cook']['archive'])
    rows=[]
    for age in range(1,5):
        tail=f'attachments/attachment_lists/garrison/berber_tent_art_020/berber_tent_age{age}_tier'
        rgd=OUT/f'tent-age{age}-generated.rgd';xml=rgd.with_suffix('.readback.xml')
        run('tent-identity-extract',[ARCH,'extract-member',archive,'attrib/'+tail+'.rgd',rgd])
        run('tent-identity-decode',[ARCH,'decode-rgd',rgd,xml])
        compiled=ET.parse(xml).getroot();ids={n.get('Value') for n in compiled.iter('RGDNode') if n.get('Key')=='pbgid'}
        assert len(ids)==1;identity=next(iter(ids))
        root=ET.Element('instance',version='2',description='Garrison-owned tent visual identity. Full list supplied by approved build recipe; see Design/asset_overhaul/BUILD_0_2_0_PLAN.md.',template=r'attachments\attachment_lists')
        ET.SubElement(root,'uniqueid',name='pbgid',value=identity)
        ET.SubElement(root,'instance_reference',name='parent_pbg',value=r'attachments\attachment_lists\civilizations\english\buildings\house_eng\tier1_house_eng')
        path=ROOT/'assets/attrib/instances'/(tail+'.xml');assert not path.exists();path.parent.mkdir(parents=True,exist_ok=True);serialize(path,root)
        rows.append({'source':path.relative_to(ROOT).as_posix(),'generated_member':'attrib/'+tail+'.rgd','pbgid':identity,'generated_sha256':sha(rgd),'integration':'compile identity references, then graft exact Garrison visual list'})
    write(OUT/'tent-generated-identities.json',rows)
    print('GARRISON_TENT_IDENTITIES_REGISTERED',flush=True)
def package():
    build=read(OUT/'production-build.json');assert build['status']=='passed' and build['exit_code']==0
    base=Path(build['archives'][0]['path']);assert sha(base)==build['archives'][0]['sha256']
    manifest=read(ROOT/'Design/asset_overhaul/BUILD_MANIFEST.json');tuareg=manifest['approved_assets'][0]
    accepted=ROOT/tuareg['reference_package']['archive'];assert sha(accepted)==tuareg['reference_package']['archive_sha256']
    tent=Path(read(OUT/'tent-art-build.json')['cook']['archive']);assert sha(tent)==read(OUT/'tent-art-build.json')['cook']['sha256']
    directory=OUT/'package';directory.mkdir(exist_ok=True)
    middle=OUT/'production-with-tuareg.sga';final=directory/'Berber_future_kingdom.sga'
    tuareg_members=read(OUT/'tuareg-port.json')['media'];tent_members=read(OUT/'tent-port.json')['members']
    if not final.exists():
        run('graft-approved-tuareg',[ARCH,'graft',base,accepted,middle,*tuareg_members])
        run('graft-four-age-tent',[ARCH,'graft',middle,tent,final,*tent_members])
    inv=inventory(final,'final-inventory');assert inv['archive']['verification']['verified']
    assert inv['archive']['name'].replace('-','').lower()==GUID
    baseinv=inventory(base,'production-final-base-inventory')
    old={x['path']:x for x in baseinv['members']};new={x['path']:x for x in inv['members']}
    expected=set(tuareg_members+tent_members)
    assert set(old)<=set(new)
    assert all((r['crc'],r['size'])==(new[p]['crc'],new[p]['size']) for p,r in old.items() if p not in expected)
    number=1
    while (OUT/f'final-readback-pass{number}').exists():number+=1
    dest=OUT/f'final-readback-pass{number}'
    run('final-unpack',[ARCH,'unpack',final,'--output',dest])
    original=OUT/'fresh-production-readback'
    if not original.exists():run('production-base-unpack',[ARCH,'unpack',base,'--output',original])
    assert all(sha(dest/p)==sha(original/p) for p in old if p not in expected)
    for p in tuareg_members+tent_members:
        assert sha(dest/p)==sha(ROOT/'assets'/p),p
    for p in ('scar/Units/tuareg_q_art_guard_trial.scar','scar/winconditions/berber_future_kingdom_GM.scar'):
        assert sha(dest/p)==sha(ROOT/'assets'/p)
    def decode(member):
        output=(dest/member).with_suffix('.readback.xml')
        run('final-decode',[ARCH,'decode-rgd',dest/member,output]);return ET.parse(output).getroot()
    entity=decode('attrib/ebps/races/malian/buildings/tent/building_hut_ayy.rgd')
    referenced={n.get('Value') for n in entity.iter('RGDNode') if n.get('Key')=='$PBGNAME'}
    assert all(GUID+f':berber_tent_age{i}_tier' in referenced for i in range(1,5)),referenced
    for age in range(1,5):
        tier=decode(f'attrib/attachments/attachment_lists/garrison/berber_tent_art_020/berber_tent_age{age}_tier.rgd')
        assert any(n.get('Value','').endswith('berber_tent_age'+str(age)) for n in tier.iter('RGDNode') if n.get('Key')=='stamp')
        for family,tail in [('ebps',f'races/malian/units/unit_spearman_tuareg_{age}_ber'),('sbps',f'races/malian/berbers/unit_spearman_tuareg_{age}_ber')]:
            body=decode(f'attrib/{family}/{tail}.rgd')
            speaker='speaker_code' if family=='ebps' else 'squad_speaker_code'
            assert any(n.get('Key')==speaker and n.get('Value')=='tuarg' for n in body.iter('RGDNode'))
        body=decode(f'attrib/attachments/attachment_lists/garrison/tuareg_shield_assets/tuareg_shield_tier{age}_ber.rgd')
        values=[n.get('Value','') for n in body.iter('RGDNode')]
        assert any('tuareg_refined_art' in v for v in values) and any('tuareg_agher_lowprofile' in v for v in values)
    baseline=read(OUT/'source-baseline.json');now={p.relative_to(ROOT).as_posix():sha(p) for p in sources()}
    changed=[p for p,h in baseline.items() if now[p]!=h];added=sorted(set(now)-set(baseline))
    allow=set(read(OUT/'tuareg-port.json')['changed_sources'])|{'assets/'+p for p in tent_members}|{read(OUT/'tent-port.json')['source']}|{x['source'] for x in read(OUT/'tent-generated-identities.json')}
    assert set(changed+added)<=allow,set(changed+added)-allow
    assert sha(ROOT/'Berber_future_kingdom.aoe4mod')==baseline['Berber_future_kingdom.aoe4mod']
    assert all(sha(ROOT/p)==h for p,h in baseline.items() if '/abilities/' in p or '/weapon/' in p or '/sbps/' in p or '/upgrade/' in p or '/locdb/' in p)
    approval=read(ROOT/'art/tribal_tent/iterations/002/iteration.json');assert sha(ROOT/approval['blend'])==approval['blend_sha256']
    evidence={'status':'build and readback passed; native acceptance pending','version':VERSION,'guid':GUID,'archive':str(final),'archive_sha256':sha(final),'members':len(new),'new_model_count':10,'tent_age_variants':4,'tuareg_body_ages':4,'source_changed':changed,'source_added':added,'source_unchanged':len(baseline)-len(changed),'compiled_base_members_byte_preserved':len(old)-len(set(old)&expected),'full_Garrison_tent_lists_replaced':4,'gameplay_ability_upgrades_voices_source':'unchanged','Q':'accepted native stock guard; moving delay remains','tent_damage':'inherited stock profile; custom ruins not authored','tent_owner_colour':'static material palette; dynamic pattern not enabled','native_acceptance':'pending user'}
    write(directory/'EVIDENCE.json',evidence)
    for source in ('tuning-validation-final.json','scar-validation.json','production-build.json','tent-art-build.json','tent-export.json','tent-generated-identities.json'):
        shutil.copy2(OUT/source,directory/source)
    shutil.copy2(OUT/'production-build-v2/logs/stdout.log',directory/'content-editor.log')
    artcook=read(OUT/'tent-art-build.json')['cook']['build_id']
    log=PROJECT/'dist/cook'/artcook/'logs/EssenceEditorLog.txt'
    if log.exists():shutil.copy2(log,directory/'tent-model-cook.log')
    test='''BERBER DYNASTIES — UPDATE 0.2.0 — 2026-10-12

Includes the approved Tribal Tent ages I-IV and accepted Tuareg bodies, low-profile shield, 4.375 m spear and existing stock-guard Q controller. This is an update of the original Berber mod GUID, not a new civilization slot.

INSTALL
1. Close AoE4. In Garrison import berber_future_kingdom-0.2.0.zip and confirm The Berber Dynasties shows version 0.2.0. Enable that update. Leave old experimental copies disabled.
2. Launch using Garrison Play. Start a fresh custom solo match; saved/restarted old matches can retain earlier assets.
3. Tuning Pack: The Berber Dynasties. Game Mode: Berber Civilization. Civilization: Malians (the existing Berber replacement slot).

TEST THE TENT
Build a Tribal Tent in Age I and watch construction from placement to completion. It should be a portable dark woven tent. Age II adds red council furnishings. Age III has ivory cloth and banners. Age IV adds red roof bands and paired banners.
Age up with the existing tent present, then build a new tent in each age if allowed. Confirm both match that age's design. Inspect near/far, rotate views, entrance/rope clearance, ground contact and selection/placement footprint. Damage and destroy one tent: construction and destruction retain inherited stock support; custom charred/destroyed tent geometry has not been authored.
Confirm Tent Influence UI and free-villager production still behave normally. Record any workers blocked at the entrance or oversized/undersized visuals. The tent material currently retains the approved fixed red/ochre palette; a dynamic player-colour shader is not included in this update.

TEST TUAREGS
Train and upgrade through Ages I-IV. Confirm the refined wraps, low-profile hide shield and long spear remain present. Check idle, walk/run/turn/stop, spear attacks, charge, brace, torch attacks and death; near/far views and two player colours. Q should preserve movement/combat, raise guard and restore after its effect. The previously observed 3-5 second moving-state delay remains; this build does not claim to fix it.
Gameplay remains the existing 50% ranged-damage reduction for 15 seconds with the 90-second recharge field. Verify these separately from appearance. Existing native tuarg voice bindings are retained; use the previously installed native audio sidecar for the custom speech.

REPORT BACK
Send the Garrison card version, age, whether the tent was built before or after age-up, a screenshot/clip of each fault, and warnings.log. State whether tent influence/villager production, Tuareg equipment and Q cleanup worked.

ROLLBACK
Close AoE4 and reimport the previous accepted 0.1.7-tuareg-lowprofile-shield.1 ZIP. Production source/archive backups and a changed/new-file list are retained under output/berber_update_0_2_0/rollback and EVIDENCE.json. Do not replace current production source with an old experiment wholesale.
'''
    (directory/'INSTALL_AND_TEST.txt').write_text(test,encoding='utf-8')
    request={'bundle_key':'berber_future_kingdom','members':[{'mod_key':'berber_future_kingdom','role':'tuning','path':final.name,'sha256':sha(final)}],'details':{'id':'berber_future_kingdom','name':'The Berber Dynasties','version':VERSION,'summary':'Four-age Tribal Tent and accepted Tuareg spearman overhaul','author':'hossein81 and marcokistan','updated':'2026-10-12','min_garrison':'0.1.4','content_types':['game-mode','tuning-pack'],'description':'Production Berber update with approved four-age tents, refined Tuareg bodies, low-profile shield and long spear. Existing gameplay, upgrades, voices and Q stock-guard controller retained. Native acceptance pending.','changelog':'Integrates approved Tribal Tent iteration 002 and accepted Tuareg art into the original civilization project.'}}
    write(OUT/'bundle-request.json',request)
    # Installed shared modules target Blender's Python 3.13, not the general runtime.
    code="import sys,json;sys.path.insert(0,sys.argv[1]);from garrison_shared import mod_bundle;doc=json.load(open(sys.argv[2],encoding='utf-8'));mod_bundle.write_manifest(sys.argv[3],**doc)"
    run('write-bundle-manifest',[r'E:/Blender5.2/5.2/python/bin/python.exe','-c',code,EXT,OUT/'bundle-request.json',directory])
    zip_path=OUT/f'berber_future_kingdom-{VERSION}.zip'
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(directory.iterdir()):z.write(p,p.name)
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None and hashlib.sha256(z.read(final.name)).hexdigest()==sha(final)
    evidence.update(zip=str(zip_path),zip_sha256=sha(zip_path));write(OUT/'delivery.json',evidence)
    # Update standard production output only after final verification; rollback is already retained.
    shutil.copy2(final,ROOT/'archives/Berber_future_kingdom.sga')
    library=ROOT/'art/tribal_tent/garrison_library_0_2_0/Mods/berber_tent_art_020'
    shutil.copytree(PROJECT,library,ignore=shutil.ignore_patterns('dist','.garrison.lock'),dirs_exist_ok=True)
    print('BERBER_UPDATE_0_2_0_READY',str(zip_path),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
