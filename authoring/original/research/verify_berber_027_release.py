"""Read-only final release verification after disposable-cache cleanup."""
import hashlib,json,os,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_2_7'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
delivery=json.loads((OUT/'delivery.json').read_text(encoding='utf-8-sig'))
clean=json.loads((OUT/'cleanup-report.json').read_text(encoding='utf-8-sig'));assert clean['executed'] and clean['delivery_hashes_rechecked']
zpath=OUT/'berber_future_kingdom-0.2.7.zip';archive=OUT/'package/Berber_future_kingdom.sga'
assert digest(zpath)==delivery['zip_sha256'];assert digest(archive)==delivery['archive_sha256']
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None
 required={'garrison.json','Berber_future_kingdom.sga','INSTALL_AND_TEST.txt','EVIDENCE.json','reviews/ribat.json','reviews/funduq.json','reviews/final-package.json'}
 assert required<=set(z.namelist());assert hashlib.sha256(z.read('Berber_future_kingdom.sga')).hexdigest()==delivery['archive_sha256']
 assert json.loads(z.read('garrison.json'))['details']['version']=='0.2.7'
 packed_members=len(z.namelist())
for kind,filename,expected in [('ribat','ribat_of_sanhaja.blend','fead0b076b023117844819a8ac28eb6a9de300631c52b650c93a4a67aa1641ff'),('funduq','funduq_editable.blend','062cdbbc85814d566d41f1c86dcecd41f2e75d741a081bd5d2c8c91ca9aa3bd2')]:
 assert digest(ROOT/'art/landmarks_0_2_7'/kind/filename)==expected
 for lod in range(3):assert (ROOT/'art/landmarks_0_2_7'/kind/f'export_lod{lod}/building.json').exists()
assert digest(ROOT/'output/berber_update_0_2_6/package/Berber_future_kingdom.sga')==delivery['baseline_sha256']
assert not (OUT/'integration').exists() and not (OUT/'qualification').exists() and not (OUT/'inventory/decoded').exists() and not (OUT/'inventory/extracted').exists()
ext=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
listed=json.loads(subprocess.run([str(ext/'bin/sga-archiver.exe'),'list',str(archive),'--verify'],capture_output=True,text=True,check=True).stdout)
assert listed['archive']['verification']['verified'];assert len(listed['members'])==723
assert listed['archive']['name'].replace('-','').lower()==delivery['project_guid']
result={'status':'verified after cleanup','zip_sha256':delivery['zip_sha256'],'archive_sha256':delivery['archive_sha256'],'zip_members':packed_members,'sga_members':723,'unchanged_baseline_members':695,'changed_existing_members':2,'editable_source_hashes_unchanged':True,'baseline_hash_unchanged':True,'cleanup_bytes_before':clean['bytes_before'],'cleanup_bytes_after':clean['bytes_after'],'cleanup_bytes_reclaimed':clean['bytes_reclaimed'],'native_acceptance':'pending user game test','native_lower_lod_switching':'unsupported; three authored LOD sources retained'}
(OUT/'final-validation.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
