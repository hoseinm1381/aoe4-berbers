"""Preview or remove only a verified current build's reproducible staging.

python tools/cleanup_staging.py --apply
Preserves release ZIPs, archives, sources, masters, native inputs and diagnostics.
"""
import argparse,hashlib,json,os,shutil,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args();cfg=read(ROOT/'project.json');r=read(ROOT/'docs/BUILD_VERIFICATION.json');assert r['version']==cfg['version'] and r['owner']==cfg['owner']
 assert r['all_member_readback_sha256'] and r['native_crc_sha1'] and r['zip_crc']
 package=ROOT/'release'/r['zip_name'];assert sha(package)==r['zip_sha256']
 assert sha(ROOT/'inputs/native-manifest.json')==r['native_input_manifest_sha256'];assert sha(ROOT/'source/master-index.json')==r['editable_master_index_sha256']
 with zipfile.ZipFile(package) as z:
  assert z.testzip() is None;mn=next(n for n in z.namelist() if n.endswith('garrison.json'));m=json.loads(z.read(mn));prefix=mn[:-len('garrison.json')]
  assert m['bundle_key']==cfg['bundle_key'] and m['details']['version']==cfg['version']
  with z.open(prefix+m['members'][0]['path']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==r['archive_sha256']
 out=(ROOT/'output/current').resolve();assert out.is_relative_to(ROOT.resolve());targets=[out/x for x in ('prepared','delivery','readback') if (out/x).exists()]
 expected=(Path(tempfile.gettempdir())/'garrison-independent-builds'/cfg['owner']/'current').resolve();assembly=Path(r['assembly_path']).resolve();assert assembly==expected
 if assembly.exists():
  report=read(assembly/'report.json');archive=Path(report['archive']).resolve();assert archive.is_relative_to(assembly) and sha(archive)==r['archive_sha256'];targets.append(assembly)
 cache=assembly.parent/'package-current'
 if cache.exists():
  manifests=list(cache.rglob('garrison.json'));assert len(manifests)==1;c=read(manifests[0]);assert c['bundle_key']==cfg['bundle_key']
  a=manifests[0].parent/c['members'][0]['path'];assert a.resolve().is_relative_to(cache.resolve()) and sha(a)==r['archive_sha256'];targets.append(cache)
 for sub in ('tools/__pycache__','tests/__pycache__'):
  if (ROOT/sub).exists():targets.append(ROOT/sub)
 inventory=[]
 for target in targets:
  assert not target.is_symlink() and not target.is_junction();files=0;size=0
  for directory,dirs,names in os.walk(target,followlinks=False):
   for name in dirs+names:
    p=Path(directory)/name;assert not p.is_symlink() and not p.is_junction() and p.resolve().is_relative_to(target.resolve()),p
   for name in names:files+=1;size+=(Path(directory)/name).stat().st_size
  inventory.append({'path':str(target.resolve()),'files':files,'logical_bytes':size})
 report={'owner':cfg['owner'],'version':cfg['version'],'mode':'applied' if args.apply else 'preview','targets':inventory,'logical_bytes':sum(x['logical_bytes'] for x in inventory),'zip_sha256_before':r['zip_sha256'],'native_inputs_and_master_indexes_unchanged':True,'release_and_source_inputs':'preserved'}
 if args.apply:
  for target in targets:shutil.rmtree(target)
  assert sha(package)==r['zip_sha256'];report['zip_sha256_after']=sha(package);p=ROOT/'docs/STAGING_CLEANUP.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
