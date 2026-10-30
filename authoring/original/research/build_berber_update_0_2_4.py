"""Fresh native house stamp resize: +200% linear size; preserve all other bytes."""
import os,sys,json,hashlib,subprocess,shutil,struct,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT/'output/berber_update_0_2_3';OUT=ROOT/'output/berber_update_0_2_4';OUT.mkdir(exist_ok=True)
STAMP_BUILD=OUT/'stamp-build-normal-access'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';CORE=EXT/'bin/core/garrison-core.exe';ARCH=EXT/'bin/sga-archiver.exe'
sys.path.insert(0,str(ROOT/'art/house_remix_0_2_2'));from archive_contract import validate_house_namespaces
SCALE=1.38;PREVIOUS=.46
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def run(label,args,timeout=600):
    with (OUT/(label+'.log')).open('w',encoding='utf-8') as f:r=subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    assert r.returncode==0,(label,r.returncode)
    return (OUT/(label+'.log')).read_text(encoding='utf-8')
def source():
    candidate=OUT/'stamp-source';candidate.mkdir(exist_ok=True)
    shutil.copy2('E:/bhs22/house_stamps.aoe4mod',candidate/'house_stamps.aoe4mod')
    shutil.copytree('E:/bhs22/source',candidate/'source',dirs_exist_ok=True)
    rows=[]
    for age in range(1,5):
        p=candidate/f'source/art/stamps/garrison/berber_house_022/house_age{age}.rdo';d=ET.parse(p)
        prop=next(n for n in d.iter('DataProperty') if n.get('Name')=='m_scale')
        before=[]
        for n in prop.iter('DataProperty'):
            if n.get('Name') in ('x','y','z'):
                v=float(n.get('Value'));assert abs(v-PREVIOUS)<1e-8;before.append(v);n.set('Value',str(SCALE))
        assert len(before)==3 and all(abs(SCALE/v-3)<1e-8 for v in before)
        d.write(p,encoding='utf-8');rows.append({'age':age,'old_scale':before,'new_scale':[SCALE]*3,'linear_multiplier':3,'source_sha256':sha(p)})
    write(OUT/'scale-source.json',{'status':'passed','ages':rows,'visual_only':True})
    run('stamp-cook',[CORE,'essence','build-mod','--editor','E:/Games/steamapps/common/Age of Empires IV/EssenceEditor.exe','--mod',candidate/'house_stamps.aoe4mod','--run-root',STAMP_BUILD,'--timeout','600'])
    assert read(STAMP_BUILD/'run.json')['status']=='succeeded'
    print('HOUSE_3X_STAMP_COOK_PASSED',flush=True)
def package():
    old=read(OLD/'delivery.json');base=Path(old['archive']);assert sha(base)==old['archive_sha256']
    assert read(STAMP_BUILD/'run.json')['status']=='succeeded'
    archives=list((STAMP_BUILD/'output').rglob('*.sga'));assert len(archives)==1
    donor=OUT/'stamp-readback';run('stamp-unpack',[ARCH,'unpack',archives[0],'--output',donor])
    rows=[]
    for age in range(1,5):
        member=f'art/stamps/garrison/berber_house_022/house_age{age}.bin';p=donor/member
        d=ET.parse(p.with_suffix('.rdo'));prop=next(n for n in d.iter('DataProperty') if n.get('Name')=='m_scale');raw=next(n for n in prop.iter('DataProperty') if n.get('Name')=='#Raw');values=struct.unpack('<3f',bytes.fromhex(raw.get('Value')))
        assert all(abs(v-SCALE)<1e-7 for v in values)
        rows.append({'member':member,'file':str(p),'sha256':sha(p),'compiled_scale':values})
    listing=OUT/'stamp-members.txt';listing.write_text('\n'.join(r['member']+'='+r['file'] for r in rows)+'\n',encoding='utf-8')
    folder=OUT/'package';folder.mkdir(exist_ok=True);final=folder/'Berber_future_kingdom.sga'
    run('replace-stamps',[ARCH,'set-members',base,listing,final])
    after=json.loads(run('final-inventory',[ARCH,'list',final,'--verify']));before=json.loads(run('baseline-inventory',[ARCH,'list',base,'--verify']));validate_house_namespaces(after)
    assert after['archive']['verification']['verified'] and after['archive']['name'].replace('-','')==before['archive']['name'].replace('-','')
    a={m['path']:m for m in before['members']};b={m['path']:m for m in after['members']};assert set(a)==set(b) and all(a[n]['toc']==b[n]['toc'] for n in a)
    oldread=OUT/'baseline-readback';fresh=OUT/'final-readback'
    run('old-unpack',[ARCH,'unpack',base,'--output',oldread]);run('final-unpack',[ARCH,'unpack',final,'--output',fresh])
    changed=[n for n in sorted(a) if sha(oldread/n)!=sha(fresh/n)];assert set(changed)=={r['member'] for r in rows}
    for r in rows:assert sha(fresh/r['member'])==r['sha256']
    manifest=read(OLD/'package/garrison.json');manifest['members'][0]['sha256']=sha(final);manifest['details'].update(version='0.2.4',updated='2026-10-13',summary='Berber houses 3x larger across all four ages',changelog='Increase native house visual stamp scale from 0.46 to 1.38 (+200% linear size), retaining corrected attribute namespaces and all other resources.')
    write(folder/'garrison.json',manifest)
    evidence={'version':'0.2.4','status':'fresh stamp cook and archive readback passed; native sizing retest pending','linear_multiplier':3,'increase_percent':200,'old_scale':PREVIOUS,'new_scale':SCALE,'changed_members':changed,'unchanged_members':len(a)-4,'namespace_contract':'passed','gameplay_footprint_tent_Tuareg_materials_models':'byte-preserved from 0.2.3','archive':str(final),'archive_sha256':sha(final),'native_acceptance':'pending sizing retest'}
    write(folder/'EVIDENCE.json',evidence)
    (folder/'INSTALL_AND_TEST.txt').write_text('''BERBER 0.2.4 — HOUSE SIZE +200%
Close AoE4. Import berber_future_kingdom-0.2.4.zip in Garrison, confirm 0.2.4, enable and launch through Play. Start a fresh match with The Berber Dynasties tuning pack, Berber Civilization game mode and Malians civilization.
House Ages I-IV are uniformly 3x their 0.2.3 visual size: native stamp scale 0.46 -> 1.38. This is a 200% increase on every axis. All other resource bytes and native namespaces are preserved.
Compare houses against villagers and nearby buildings. Test existing/new houses after each age-up, ground contact, doorway orientation, selection, construction/destruction and adjacent-building overlap. Gameplay/placement/pathfinding footprint remains unchanged.
The 0.2.3 screenshot confirmed visibility after namespace repair; the new size still needs your native test. The project now records a 3x visual-sizing default for future buildings authored at the same 2x2 reference scale.
Rollback: close the game and reimport 0.2.3, or the working 0.2.1 ZIP.
''',encoding='utf-8')
    zpath=OUT/'berber_future_kingdom-0.2.4.zip'
    with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
        for p in folder.iterdir():
            if p.is_file():z.write(p,p.name)
    with zipfile.ZipFile(zpath) as z:assert z.testzip() is None and hashlib.sha256(z.read(final.name)).hexdigest()==sha(final)
    evidence.update(zip=str(zpath),zip_sha256=sha(zpath));write(OUT/'delivery.json',evidence)
    print('BERBER_0_2_4_3X_HOUSES_READY',str(zpath),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
