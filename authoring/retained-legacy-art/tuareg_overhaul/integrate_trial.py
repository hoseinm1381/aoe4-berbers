"""Isolated Berber candidate, native cook and archive-bound readback for original Tuareg art."""
import argparse,copy,hashlib,json,os,shutil,subprocess,sys,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/tuareg_overhaul';WORK=ROOT/'output/tuareg_art_guard_trial';CANDIDATE=WORK/'candidate'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';ARCHIVER=EXT/'bin/sga-archiver.exe'
GUID='1d3145e8f1b2427f8bb0067851fcf0f1';GM='scar/winconditions/berber_future_kingdom_GM.scar';MODULE='scar/Units/tuareg_q_art_guard_trial.scar'
VERSION='0.1.4-tuareg-original-art.1'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(args):
    p=subprocess.run([str(a) for a in args],capture_output=True,encoding='utf-8',errors='replace');assert p.returncode==0,p.stderr;return p.stdout
def inventory(path):return json.loads(run([ARCHIVER,'list',path,'--verify']))
def cook_info(name):
    record=json.loads((ART/f'garrison_library/Mods/{name}/mod-project.json').read_text());cook=record['cooks'][-1]
    assert sha(Path(cook['archive']))==cook['sha256'];assert cook['live_reload'] is False
    return cook
def guard():
    base=json.loads((WORK/'source-baseline.json').read_text())
    for file,digest in base.items():assert sha(ROOT/file)==digest,file
    return len(base)
def prepare():
    assert not CANDIDATE.exists()
    baseline={p.relative_to(ROOT).as_posix():sha(p) for p in [ROOT/'Berber_future_kingdom.aoe4mod',*sorted(p for p in (ROOT/'assets').rglob('*') if p.is_file())]}
    (WORK/'source-baseline.json').write_text(json.dumps(baseline,indent=2))
    shutil.copytree(ROOT/'output/tuareg_shield_posture_test/candidate',CANDIDATE)
    recipes=cook_info('tuareg_weapon_lists');weapon_archive=Path(recipes['archive']);parents=json.loads((WORK/'weapon-parent-map.json').read_text())
    ids={node.get('value') for p in (CANDIDATE/'assets/attrib/instances').rglob('*.xml') for node in ET.parse(p).iter('uniqueid')}
    sources=[];readback=WORK/'weapon-identity-readback';readback.mkdir()
    for parent,name in parents.items():
        logical=f'attachments/attachment_lists/garrison/tuareg_weapon_lists/{name}'
        rgd=readback/(name+'.rgd');decoded=readback/(name+'.xml')
        run([ARCHIVER,'extract-member',weapon_archive,'attrib/'+logical+'.rgd',rgd]);run([ARCHIVER,'decode-rgd',rgd,decoded])
        identifier=ET.parse(decoded).find("./RGDNode/RGDNode[@Key='pbgid']").get('Value');assert identifier not in ids;ids.add(identifier)
        official=WORK/'official-weapon-sources'/(parent+'.xml');official.parent.mkdir(parents=True,exist_ok=True)
        run([ARCHIVER,'extract-member',r'E:\Games\steamapps\common\Age of Empires IV\cardinal\archives\ReferenceAttributes.sga','instances/'+parent+'.xml',official])
        source=ET.parse(official).getroot()
        # The exact authoritative weapon-list receiving field is parent_animator.
        assert source.find('.//file[@name="parent_animator"]') is not None
        root=ET.Element('instance',version=source.get('version'),description='Private Tuareg spear visual; all stock attachment rules inherited',template=source.get('template'))
        def fields(container):
            group=ET.SubElement(container,'group',name='attachment_lists')
            ET.SubElement(group,'file',name='parent_animator',value='art\\scenario\\tuareg\\tuareg_leaf_spear\\tuareg_leaf_spear',overrideParent='True')
            ET.SubElement(container,'uniqueid',name='pbgid',value=identifier)
            ET.SubElement(container,'instance_reference',name='parent_pbg',value=parent.replace('/','\\'))
        fields(root)
        for variant in source.findall('variant'):
            if variant.find('.//file[@name="parent_animator"]') is not None:fields(ET.SubElement(root,'variant',name=variant.get('name')))
        out=CANDIDATE/('assets/attrib/instances/'+logical+'.xml');out.parent.mkdir(parents=True,exist_ok=True);ET.indent(root,space='\t');ET.ElementTree(root).write(out,encoding='utf-8',xml_declaration=True)
        sources.append({'logical':logical,'pbgid':identifier,'parent':parent,'source_sha256':sha(official),'serializer':recipes['sha256']})
    changes=[]
    for age in range(1,5):
        path=CANDIDATE/f'assets/attrib/instances/attachments/attachment_lists/garrison/tuareg_shield_assets/tuareg_shield_tier{age}_ber.xml'
        old=path.read_bytes();data=old
        body=f'art\\scenario\\garrison\\tuareg_shield_assets\\tuareg_body_age{age}\\tuareg_body_age{age}'.encode()
        new_body=f'art\\scenario\\garrison\\tuareg_art_v2\\units\\tuareg_age{age}\\body\\model'.encode()
        shield=b'art\\scenario\\garrison\\tuareg_shield_assets\\tuareg_shield_model\\tuareg_shield_model'
        new_shield=b'art\\scenario\\tuareg\\tuareg_agher_shield\\tuareg_agher_shield'
        assert data.count(body)==1 and data.count(shield)==1;data=data.replace(body,new_body).replace(shield,new_shield);path.write_bytes(data)
        assert data.replace(new_body,body).replace(new_shield,shield)==old;changes.append(path.relative_to(CANDIDATE).as_posix())
        path=CANDIDATE/f'assets/attrib/instances/ebps/races/malian/units/unit_spearman_tuareg_{age}_ber.xml';old=path.read_bytes();root=ET.fromstring(old)
        count=0
        for node in root.findall('.//instance_reference[@name="animator_attachments"]'):
            parent=node.get('value').replace('\\','/')
            if parent in parents:
                node.set('value',f'attachments\\attachment_lists\\garrison\\tuareg_weapon_lists\\{parents[parent]}');node.set('mod',GUID);count+=1
        assert count==3,(age,count);ET.indent(root,space='\t');ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
        # Compare receiving fields only; source whitespace is editor-normalized.
        before=ET.fromstring(old)
        for a,b in zip(before.iter(),root.iter()):
            if a.tag=='instance_reference' and a.get('name')=='animator_attachments' and a.get('value').replace('\\','/') in parents:continue
            assert a.tag==b.tag and a.attrib==b.attrib,(age,a.attrib,b.attrib)
        changes.append(path.relative_to(CANDIDATE).as_posix())
    gm=CANDIDATE/'assets'/GM;data=gm.read_bytes();old=b'import("Units/tuareg_q_posture_trial.scar")';assert data.count(old)==1
    gm.write_bytes(data.replace(old,b'import("Units/tuareg_q_art_guard_trial.scar")'));changes.append('assets/'+GM)
    shutil.copy2(ART/'tuareg_q_art_guard_trial.scar',CANDIDATE/'assets'/MODULE)
    (WORK/'candidate-source.json').write_text(json.dumps({'guid':GUID,'changed_sources':changes,'new_weapon_lists':sources,'new_controller':MODULE,'source_files_preserved':guard(),'ability_and_other_gameplay':'unchanged','animation_scope':'stock posture with selector persistence and movement diagnostics; no forced leaf queue; instant moving transition remains unresolved'},indent=2))
    print('CANDIDATE_READY',len(changes),len(sources),flush=True)
def build():
    # Content Editor validates File fields before archive assembly: the actual cooked
    # model resources must be present in this candidate, not only in the later graft.
    failed=WORK/'candidate-build.json'
    if failed.exists() and json.loads(failed.read_text()).get('status')=='failed' and not (WORK/'candidate-build-failed-missing-art').exists():
        shutil.copytree(WORK/'candidate-build',WORK/'candidate-build-failed-missing-art')
        shutil.copy2(failed,WORK/'candidate-build-failed-missing-art/build-result.json')
    previous_sources=WORK/'candidate-media-sources.json'
    previous={r['path']:r['sha256'] for r in json.loads(previous_sources.read_text())['files']} if previous_sources.exists() else {}
    art=cook_info('tuareg_art_v2');archive=Path(art['archive']);inv=inventory(archive)
    prefixes=[f'art/scenario/garrison/tuareg_art_v2/units/tuareg_age{a}/body/' for a in range(1,5)]+['art/scenario/tuareg/tuareg_agher_shield/','art/scenario/tuareg/tuareg_leaf_spear/']
    rows=[]
    for item in inv['members']:
        path=item['path']
        if not any(path.lower().startswith(p) for p in prefixes):continue
        output=CANDIDATE/'assets'/path;output.parent.mkdir(parents=True,exist_ok=True)
        fresh=WORK/'staged-art'/art['sha256']/path;fresh.parent.mkdir(parents=True,exist_ok=True)
        if not fresh.exists():run([ARCHIVER,'extract-member',archive,path,fresh])
        if output.exists():assert sha(output)==previous.get(path,sha(fresh)),path
        shutil.copy2(fresh,output)
        rows.append({'path':path,'sha256':sha(output),'crc':item['crc'],'size':item['size']})
    assert len([r for r in rows if r['path'].endswith('.rrgeom')])==6
    (WORK/'candidate-media-sources.json').write_text(json.dumps({'art_archive_sha256':art['sha256'],'files':rows},indent=2))
    old_run=WORK/'candidate-build'
    if old_run.exists():
        assert failed.exists() and json.loads(failed.read_text()).get('status')=='failed'
        destination=WORK/'candidate-build-attempt1';assert not destination.exists()
        assert old_run.resolve().is_relative_to(WORK.resolve()) and destination.resolve().is_relative_to(WORK.resolve())
        old_run.rename(destination)
    sys.path.insert(0,str(ROOT/'art/tuareg_shield'));import shrek_trigger_probe as builder
    builder.WORK=WORK;builder.CANDIDATE=CANDIDATE;builder.build()
def package():
    guard();art_cook=cook_info('tuareg_art_v2');art_archive=Path(art_cook['archive']);art_inventory=inventory(art_archive)
    body_prefix='art/scenario/garrison/tuareg_art_v2/units/'
    prefixes=[body_prefix+f'tuareg_age{a}/body/' for a in range(1,5)]+['art/scenario/tuareg/tuareg_agher_shield/','art/scenario/tuareg/tuareg_leaf_spear/']
    media=[x['path'] for x in art_inventory['members'] if any(x['path'].lower().startswith(p) for p in prefixes)]
    assert len([p for p in media if p.endswith('.rrgeom')])==6
    report=json.loads((WORK/'candidate-source.json').read_text());result=json.loads((WORK/'candidate-build.json').read_text());assert result['status']=='succeeded' and result['exit_code']==0
    donor=Path(result['archives'][0]['path']);assert sha(donor)==result['archives'][0]['sha256']
    prev=json.loads((ROOT/'output/tuareg_shield_posture_test/delivery.json').read_text());base=Path(prev['archive']);assert sha(base)==prev['archive_sha256']
    candidates=inventory(donor);paths={x['path'].lower():x['path'] for x in candidates['members']}
    logical=[GM,MODULE]+[p.removeprefix('assets/attrib/instances/').removesuffix('.xml') for p in report['changed_sources'] if p.startswith('assets/attrib/instances/')]+[r['logical'] for r in report['new_weapon_lists']]
    attrib=['attrib/'+p+'.rgd' for p in logical if p not in (GM,MODULE)];tuning=[paths[p.lower()] for p in [GM,MODULE,*attrib]]
    package=WORK/'package';package.mkdir(exist_ok=True);intermediate=WORK/'candidate-tuning.sga';final=package/'Berber_future_kingdom.sga'
    assert not intermediate.exists() and not final.exists()
    run([ARCHIVER,'graft',base,donor,intermediate,*tuning]);run([ARCHIVER,'graft',intermediate,art_archive,final,*media])
    inv=inventory(final);old={x['path'].lower():x for x in inventory(base)['members']};new={x['path'].lower():x for x in inv['members']}
    changed=[p for p in old if (old[p]['crc'],old[p]['size'])!=(new[p]['crc'],new[p]['size'])]
    expected={p.lower() for p in tuning if p.lower() in old};assert set(changed)==expected
    assert inv['archive']['name'].replace('-','').lower()==GUID and inv['archive']['verification']['verified']
    readback=WORK/'readback';assert not readback.exists();run([ARCHIVER,'unpack',final,'--output',readback])
    for path in [GM,MODULE]:assert sha(readback/new[path.lower()]['path'])==sha(CANDIDATE/'assets'/path)
    for path in media:
        original=WORK/'art-resource-readback'/path;original.parent.mkdir(parents=True,exist_ok=True)
        run([ARCHIVER,'extract-member',art_archive,path,original]);assert sha(original)==sha(readback/path)
    result={'version':VERSION,'guid':GUID,'archive':str(final),'archive_sha256':sha(final),'members':len(new),'changed_baseline_members':changed,'unchanged_baseline_members':len(old)-len(changed),'added_members':sorted(set(new)-set(old)),
            'original_source_files_preserved':guard(),'new_models':6,'new_skin_bones':48,'gameplay_values_voices_and_stock_units':'byte-preserved except private visual references','native_acceptance':'pending user test','immediate_moving_q':'not solved; missing qualified private interruptible graph or phase-preserving arm layer interface','stop_pose_stability':'force requests removed, owned selector reasserted; native result pending'}
    (WORK/'archive-inventory.json').write_text(json.dumps(inv,indent=2));(package/'EVIDENCE.json').write_text(json.dumps(result,indent=2))
    shutil.copy2(WORK/'TEST-TRIAL.txt',package/'TEST-TRIAL.txt')
    sys.path.insert(0,str(EXT));from garrison_shared import mod_bundle
    mod_bundle.write_manifest(package,bundle_key='berber_future_kingdom',members=[{'mod_key':'berber_future_kingdom','role':'tuning','path':final.name,'sha256':sha(final)}],details={'id':'berber_future_kingdom','name':'The Berber Dynasties','version':VERSION,'summary':'Original Tuareg age skins, hide shield and spear; guard stability trial','author':'hossein81 and marcokistan','updated':'2026-10-11','min_garrison':'0.1.3','content_types':['game-mode','tuning-pack'],'description':'Original Tuareg art Ages I-IV with existing Q gameplay. Removed ineffective forced clip queue; owned posture selector persists during the effect. Instant moving animation switching remains unresolved. Solo native visual testing required.','changelog':'Six new model resources and five private spear attachment lists; new guard stability diagnostics.'})
    zipped=WORK/f'berber_future_kingdom-{VERSION}.zip'
    with zipfile.ZipFile(zipped,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(package.iterdir()):z.write(p,p.name)
    with zipfile.ZipFile(zipped) as z:assert z.testzip() is None;assert hashlib.sha256(z.read(final.name)).hexdigest()==result['archive_sha256']
    result.update(zip=str(zipped),zip_sha256=sha(zipped));(WORK/'delivery.json').write_text(json.dumps(result,indent=2));print('TRIAL_PACKAGED',str(zipped),flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','build','package']);globals()[parser.parse_args().stage]()
