"""Verify040 ZIP then clean only explicitly inventoried regenerable040 output."""
import hashlib,json,os,shutil,sys
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from berber_040_integrate import ROOT,OUT,BASE,BASE_SHA,read,write,sha

def admit_payloads(report,manifests):
 composed={r['member']:r['sha256'] for r in report['payloads']}
 for manifest in manifests:
  for row in manifest['payloads']:
   assert composed.get(row['member'])==row['sha256'],('Missing or stale composed model payload',row['member'])
 return composed

def package():
 artcook=read(OUT/'art-cook.json');assert artcook['status']=='passed' and artcook['cook']['live_reload'] is False
 inputs=read(OUT/'art-cook-inputs.json')
 assert inputs['sources']==artcook['source_files_sha256'],'Latest source snapshot did not complete art cook'
 assert inputs['university_recipe_sha256']==artcook['university_recipe_sha256'] and inputs['carrier_image_hashes']==artcook['carrier_image_hashes'],'Latest material snapshot did not complete art cook'
 assert sha(ROOT/'art/building_remix_0_4_0/university/recipe.json')==inputs['university_recipe_sha256']
 for source,expected in inputs['sources'].items():
  source=Path(source);assert {str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}==expected,('Export changed after cook',str(source))
 for image,expected in inputs['carrier_image_hashes'].items():assert sha(image)==expected,image
 report=read(OUT/'integration/composition-report.json')
 assert report['status']=='passed' and report['baseline_sha256']==BASE_SHA and sha(BASE)==BASE_SHA
 attributes=read(OUT/'final-attribute-readback.json')
 assert attributes['status']=='passed' and attributes['archive_sha256']==report['archive_sha256']
 # Full release admission: all four newly requested buildings must be bound.
 for kind in ('university','koutoubia','fez','grand_keep'):
  admission=read(OUT/'integration/model-manifests'/(kind+'-binding.json'))
  assert admission['status']=='passed',kind
 manifests=[read(p) for p in sorted((OUT/'integration/model-manifests').glob('*.json'))]
 admit_payloads(report,manifests)
 assert read(OUT/'media-dependency-validation.json')['status']=='passed'
 candidate=Path(report['archive']);assert sha(candidate)==report['archive_sha256']
 # Re-extract every admitted media/binding member from the archive being shipped.
 from berber_040_integrate import ARCH,run
 import tempfile
 with tempfile.TemporaryDirectory(prefix='berber040-admission-') as temporary:
  for index,(member,expected) in enumerate(admit_payloads(report,manifests).items()):
   target=Path(temporary)/str(index);run(ARCH,'extract-member',candidate,member,target)
   assert sha(target)==expected,('Final archive member mismatch',member)
 dest=OUT/'package';dest.mkdir(parents=True,exist_ok=True)
 shutil.copy2(candidate,dest/'Berber_future_kingdom.sga')
 manifest=read(ROOT/'output/berber_update_0_3_1/package/garrison.json')
 manifest['members'][0]['sha256']=sha(candidate)
 manifest['details'].update(version='0.4.0',summary='Berber coherent architecture repairs and four distinct new buildings',description='Keep, Marrakech and Siege composition repairs; Tlemcen construction/completion consistency; University, Koutoubia, Fez and Grand Keep visual update. Gameplay preserved.',changelog='New art and scoped native visual bindings. Native match acceptance remains pending.')
 write(dest/'garrison.json',manifest)
 write(dest/'EVIDENCE.json',{'version':'0.4.0','baseline_sha256':BASE_SHA,'sga_sha256':sha(candidate),'guid':report['project_guid'],'baseline_members':report['baseline_members'],'candidate_members':report['candidate_members'],'changed_existing_members':report['changed_existing_members'],'new_members':report['new_members'],'unrelated_members_sha256_identical':True,'native_game':'unverified; no native match automation available','owner_colour':'native masks/material/flag dependencies preserved; two-owner runtime probe pending'})
 (dest/'INSTALL_AND_TEST.txt').write_text('BERBER 0.4.0 CANDIDATE\nClose AoE4, import this ZIP into Garrison, enable Berber. Start a fresh match selecting Tuning Pack The Berber Dynasties, Game Mode Berber Civilization, civilization Malians.\nReview construction/preview/completion and age tiers for Tlemcen, Keep, Marrakech and Siege; inspect University, Koutoubia, Fez and Grand Keep. Test two owner colours, damage/destruction, entrances/rally, garrison/fire/research/landmark functions. Accepted market/mosque and other031 art are preserved.\nCook, archive and ZIP checks do not establish native acceptance. Retained0.3.1 ZIP is the rollback.\n',encoding='utf8')
 members=sorted(dest.glob('*'));assert {p.name for p in members}=={'Berber_future_kingdom.sga','garrison.json','EVIDENCE.json','INSTALL_AND_TEST.txt'}
 zipfile=OUT/'berber_future_kingdom-0.4.0.zip'
 with ZipFile(zipfile,'w',ZIP_DEFLATED,compresslevel=6) as z:
  for p in members:z.write(p,p.name)
 result=verify_zip(zipfile,sha(candidate));result.update(zip=str(zipfile),zip_sha256=sha(zipfile),sga=str(dest/'Berber_future_kingdom.sga'),sga_sha256=sha(candidate),status='passed',native_acceptance='unverified')
 write(OUT/'release-validation.json',result);print(json.dumps(result,indent=2))

def verify_zip(path,sga_sha):
 with ZipFile(path) as z:
  assert z.testzip() is None
  assert set(z.namelist())=={'Berber_future_kingdom.sga','garrison.json','EVIDENCE.json','INSTALL_AND_TEST.txt'}
  assert hashlib.sha256(z.read('Berber_future_kingdom.sga')).hexdigest()==sga_sha
  manifest=json.loads(z.read('garrison.json'));assert manifest['details']['version']=='0.4.0'
  assert manifest['members'][0]['sha256']==sga_sha
  return {'zip_members':z.namelist(),'zip_readable':True,'manifest_sga_hash_matches':True}

def size_tree(root):return sum(p.stat().st_size for p in Path(root).rglob('*') if p.is_file())
def inspect_target(path,allowed):
 path=Path(path).resolve();assert path.is_relative_to(allowed) and path!=allowed,(path,allowed)
 assert not path.is_symlink() and not path.is_junction(),path
 if path.is_dir():
  for parent,dirs,files in os.walk(path,followlinks=False):
   for name in dirs+files:
    p=Path(parent)/name
    assert not p.is_symlink() and not p.is_junction(),p
    assert not p.lstat().st_file_attributes&0x400,p
 return path

def cleanup():
 assert sha(BASE)==BASE_SHA
 delivery=read(OUT/'release-validation.json');archive=Path(delivery['zip']);sga=Path(delivery['sga'])
 assert sha(archive)==delivery['zip_sha256'] and sha(sga)==delivery['sga_sha256'];verify_zip(archive,sha(sga))
 allowed=OUT.resolve();art=(ROOT/'art/building_remix_0_4_0').resolve();external=Path('F:/aoe_4_temp/berber_040_university_donors').resolve()
 before_by_root={str(p):size_tree(p) for p in (allowed,art,external)};before=sum(before_by_root.values());inventory=[]
 # Source recipes/blends/media are never eligible. Logs and compact reports retained.
 patterns=['baseline-inputs','official-inputs','integration/baseline-readback','integration/candidate-readback','integration/repair-readback','integration/payload','integration/candidate','integration/data-candidate.sga','integration/attrib-candidate.sga','integration/university-rebound.bin','qualification/readback','qualification/source','art-cook-readback-*','assembled','reflect-source/source','reflect-readback-*','reflect-native-*/intermediate','reflect-native-*/output']
 for name in ('qualification-native','qualification-native-02'):
  for sub in ('intermediate','output'):patterns.append(name+'/'+sub)
 patterns+=['integration/repair-data-candidate.sga','integration/repair-attrib-candidate.sga']
 project=OUT/'garrison-library/Mods/berber_buildings_040'
 for sub in ('project','dist'):patterns.append(str((project/sub).relative_to(OUT)))
 paths=[]
 # Author exports and native edited sources are rebuild inputs, not caches.
 for prep in OUT.glob('*-prepare.json'):
  data=read(prep)
  if 'source_files_sha256' in data:
   source=Path(data['source'])
   assert source.resolve().is_relative_to((ROOT/'art/building_remix_0_4_0').resolve())
   assert {str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}==data['source_files_sha256'],str(source)
 university=ROOT/'art/building_remix_0_4_0/university/recipe.json'
 if university.exists():
  for model in read(university)['models']:assert sha(model['native_geometry'])==model['native_geometry_sha256']
 for pattern in patterns:
  for path in OUT.glob(pattern):
   checked=inspect_target(path,allowed)
   assert checked not in (archive.resolve(),sga.resolve())
   paths.append(checked)
 # Preserve all Garrison recipe and cook records before deleting generated copies.
 if (project/'mod-project.json').exists():write(OUT/'retained-garrison-project.json',read(project/'mod-project.json'))
 native_runs=[]
 for runfile in sorted((project/'dist/cook').glob('*/run.json')):
  burn=runfile.parent/'logs/burn.log'
  native_runs.append({'run':read(runfile),'burn_log_tail':burn.read_text(encoding='utf8',errors='replace').splitlines()[-50:] if burn.exists() else []})
 write(OUT/'retained-native-cook-evidence.json',{'runs':native_runs})
 scoped_paths=[(path,allowed) for path in paths]
 for family in ('fez','grand_keep'):
  for name in ('export_lod0','export_lod0_ready'):
   path=art/family/name
   if path.exists():scoped_paths.append((inspect_target(path,art),art))
 failed=art/'wonder/export_failed_npot_evidence'
 if failed.exists():scoped_paths.append((inspect_target(failed,art),art))
 for path,scope in scoped_paths:inventory.append({'path':str(path),'allowed_root':str(scope),'bytes':size_tree(path) if path.is_dir() else path.stat().st_size,'reason':'040 generated staging/readback/native cache or superseded export; current authoritative source/export retained'})
 write(OUT/'cleanup-inventory.json',{'allowed_root':str(allowed),'output_junction_target':str(OUT.resolve()),'targets':inventory})
 for path,scope in scoped_paths:
  inspect_target(path,scope)
  if path.is_dir():shutil.rmtree(path)
  else:path.unlink()
 #040-only projection/decoded JSON is preserved losslessly in verified bundles.
 from berber_040_integrate_cache import bundle,bundle_decoded
 compressed=[]
 for family in ('keep','marrakech','siege','university'):
  if list((art/family).glob('*-projection.json'))+list((art/family).glob('*_projection.json')):compressed.append({'family':family,**bundle(family,delete=True)})
 for decoded in external.glob('*/decoded-static.json'):
  inspect_target(decoded,external)
  compressed.append({'decoded':str(decoded),**bundle_decoded(decoded,delete=True)})
 assert sha(archive)==delivery['zip_sha256'] and sha(sga)==delivery['sga_sha256'];verify_zip(archive,sha(sga))
 assert sha(BASE)==BASE_SHA
 write(OUT/'baseline-preservation-after-cleanup.json',{'baseline':str(BASE),'sha256_before':BASE_SHA,'sha256_after':sha(BASE),'status':'passed'})
 after_by_root={str(p):size_tree(p) for p in (allowed,art,external)};after=sum(after_by_root.values())
 write(OUT/'cleanup-report.json',{'status':'passed','bytes_before':before,'bytes_after':after,'bytes_reclaimed':before-after,'bytes_before_by_root':before_by_root,'bytes_after_by_root':after_by_root,'deleted':inventory,'lossless_compressed_rebuild_caches':compressed,'delivery_hashes_after':{'zip':sha(archive),'sga':sha(sga)},'retained_inputs':['art/building_remix_0_4_0 editable blends, source textures/exports, recipes and research scripts','040 Garrison mod-project.json and retained-garrison-project.json','current package SGA/ZIP and prior rollback releases','University native donor geometry/material/texture inputs and lossless decoded JSON bundles; all040 readers support verified compressed reads','shared native donor cache and prior-release decoded caches retained because prior-release recipes require them'],'native_acceptance':'unverified'})
 print('040_CLEANUP_VERIFIED',before-after,'bytes reclaimed')

if __name__=='__main__':globals()[sys.argv[1]]()
