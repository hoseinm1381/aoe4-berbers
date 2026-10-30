"""Repair 0.2.2 house PBG admission: preserve every member's bytes, fix its TOC."""
import os,sys,json,hashlib,subprocess,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT/'output/berber_update_0_2_2';OUT=ROOT/'output/berber_update_0_2_3';OUT.mkdir(exist_ok=True)
ART=ROOT/'art/house_remix_0_2_2';sys.path.insert(0,str(ART))
from archive_contract import validate_house_namespaces
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';ARCH=EXT/'bin/sga-archiver.exe'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def run(label,args):
    with (OUT/(label+'.log')).open('w',encoding='utf-8') as f:result=subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT,timeout=300)
    assert result.returncode==0,(label,result.returncode)
    return (OUT/(label+'.log')).read_text(encoding='utf-8')
old=read(OLD/'delivery.json');broken=Path(old['archive']);assert sha(broken)==old['archive_sha256']
baseline=read(ROOT/'output/berber_update_0_2_1/delivery.json');base=Path(baseline['archive']);assert sha(base)==baseline['archive_sha256']
before=json.loads(run('broken-inventory',[ARCH,'list',broken,'--verify']))
try:validate_house_namespaces(before)
except ValueError as e:observed=str(e)
else:raise AssertionError('Expected known 0.2.2 native namespace fault')
bindings=read(OLD/'bindings-report.json');assert bindings['status']=='passed'
for item in bindings['payloads']:assert sha(item['file'])==item['sha256']
lists={}
for alias,prefix in [('data','art/'),('attrib','attrib/')]:
    rows=[r for r in bindings['payloads'] if r['member'].startswith(prefix)];assert rows
    p=OUT/(alias+'-members.txt');p.write_text('\n'.join(r['member']+'='+r['file'] for r in rows)+'\n',encoding='utf-8');lists[alias]=p
assert sum(len(p.read_text().splitlines()) for p in lists.values())==len(bindings['payloads'])
package=OUT/'package';package.mkdir(exist_ok=True);mid=OUT/'with-house-media.sga';final=package/'Berber_future_kingdom.sga'
run('house-media',[ARCH,'set-members',base,lists['data'],mid,'--alias','data'])
run('house-attributes',[ARCH,'set-members',mid,lists['attrib'],final,'--alias','attrib'])
after=json.loads(run('final-inventory',[ARCH,'list',final,'--verify']));assert after['archive']['verification']['verified']
assert after['archive']['name'].replace('-','').lower()=='1d3145e8f1b2427f8bb0067851fcf0f1'
validate_house_namespaces(after)
oldmembers={m['path']:m for m in before['members']};newmembers={m['path']:m for m in after['members']};assert set(oldmembers)==set(newmembers)
moved=[{'member':name,'from':oldmembers[name]['toc'],'to':newmembers[name]['toc']} for name in sorted(oldmembers) if oldmembers[name]['toc']!=newmembers[name]['toc']]
expected={f'attrib/attachments/attachment_lists/garrison/berber_house_022/house_age{a}_tier.rgd' for a in range(1,5)}
assert {m['member'] for m in moved}==expected and all(m['from']=='data' and m['to']=='attrib' for m in moved)
oldread=OUT/'broken-readback';fresh=OUT/'final-readback'
run('unpack-broken',[ARCH,'unpack',broken,'--output',oldread]);run('unpack-fixed',[ARCH,'unpack',final,'--output',fresh])
for name in oldmembers:assert sha(oldread/name)==sha(fresh/name),name
for item in bindings['payloads']:assert sha(fresh/item['member'])==item['sha256']
for age in range(1,5):
    tier=f'attrib/attachments/attachment_lists/garrison/berber_house_022/house_age{age}_tier.rgd'
    run('tier'+str(age)+'-decode',[ARCH,'decode-rgd',fresh/tier,OUT/f'house-tier{age}.xml'])
manifest=read(OLD/'package/garrison.json');manifest['members'][0]['sha256']=sha(final)
manifest['details'].update(version='0.2.3',updated='2026-10-13',summary='Fix invisible Berber houses: correct native attribute namespace',description='Repairs 0.2.2 house attachment registration. All four private house tiers are now in the attrib TOC, with art and stamps in data. House surfaces and all resource bytes remain unchanged; full tent and Tuareg content retained.',changelog='Correct data-to-attrib archive placement for the four private house attachment blueprints; prevent the entity from having no registered house visual tier.')
write(package/'garrison.json',manifest)
evidence={'version':'0.2.3','status':'namespace regression and final archive/readback passed; native retest pending',
 'root_cause':'0.2.2 placed four new house attachment RGDs in the data TOC; native PBG loading requires attrib',
 'observed_fault':observed,'namespace_changes':moved,'all_400_member_bytes_preserved_from_0_2_2':True,
 'member_count':len(newmembers),'guid_preserved':True,'original_0_2_1_and_0_2_2_preserved':True,
 'art_geometry_materials_stamps_gameplay_tent_Tuareg_SCAR_audio':'unchanged; no new asset cook required',
 'archive':str(final),'archive_sha256':sha(final),'native_acceptance':'pending user retest'}
write(package/'EVIDENCE.json',evidence)
(package/'INSTALL_AND_TEST.txt').write_text('''BERBER 0.2.3 — INVISIBLE HOUSE FIX
Close AoE4 before importing. Import berber_future_kingdom-0.2.3.zip into Garrison, confirm version 0.2.3, enable The Berber Dynasties and launch through Play.
Start a FRESH match: Tuning Pack The Berber Dynasties; Game Mode Berber Civilization; Civilization Malians.
Build several houses in Age I. The house should now have its native visual attachment registered instead of only a selection footprint. Check an existing house through Ages II-IV and one newly built at each age. Check construction/cancel, damage/destruction and two player colours. Confirm the tent and Tuareg still work.
Cause: the four private house attachment blueprints were mistakenly packaged in data instead of attrib. 0.2.3 fixes their TOC placement. Every one of the 400 resource members has exactly the same bytes as 0.2.2; all geometry, materials, gameplay, Tent, Tuareg, SCAR and audio are preserved. No gameplay or shader workaround was introduced.
Archive/static regression checks pass. Native appearance and selectors still require this fresh-match test. An existing match or saved game is not a valid test of changed attribute admission.
If a house still fails, report the age and screenshots and preserve warnings.log from that run. Roll back by closing AoE4 and reimporting the preserved working 0.2.1 ZIP.
''',encoding='utf-8')
zpath=OUT/'berber_future_kingdom-0.2.3.zip'
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
    for p in package.iterdir():
        if p.is_file():z.write(p,p.name)
with zipfile.ZipFile(zpath) as z:
    assert z.testzip() is None and hashlib.sha256(z.read(final.name)).hexdigest()==sha(final)
evidence.update(zip=str(zpath),zip_sha256=sha(zpath));write(OUT/'delivery.json',evidence)
print('BERBER_0_2_3_NAMESPACE_REPAIR_READY',str(zpath),flush=True)
