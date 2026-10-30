"""Restore removed duplicate caches before an older recipe needs them.

Usage: python -B research/restore_cleanup_cache.py --root <cache directory>
Only files listed in the saved, hash-verified cleanup map can be written.
"""
import argparse,hashlib,json,os,shutil,zipfile,subprocess
from pathlib import Path
REPORT=Path(__file__).absolute().parent/'cleanup_20261016'
def digest(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def restore(root):
 root=Path(root).resolve();report=REPORT/'deletion-plan.json'
 if not report.exists():return 0
 count=0;checked_tools={}
 for row in json.loads(report.read_text())['files']:
  target=Path(row['path'])
  if root!=target and root not in target.parents:continue
  if target.exists():continue
  source=row['restore']
  for p in (target,*target.parents):
   if p.exists() and (p.is_junction() or p.is_symlink()):raise ValueError('Linked restore destination refused')
  target.parent.mkdir(parents=True,exist_ok=True)
  temp=target.with_name(target.name+'.cleanup-restore.tmp')
  if temp.exists():raise FileExistsError('Temporary restore file exists')
  try:
   if 'decoder' in source:
    if source['decoder'] not in checked_tools:checked_tools[source['decoder']]=digest(source['decoder'])
    if checked_tools[source['decoder']]!=source['decoder_sha256'] or digest(source['wem'])!=source['wem_sha256']:raise ValueError('Decoder input changed')
    subprocess.run([source['decoder'],'-i','-o',str(temp),source['wem']],capture_output=True,check=True,timeout=60)
   else:
    with temp.open('xb') as writer:
     if 'file' in source:
      # Historical sources may now be retained in the lossless development
      # bundle. Read them directly without expanding a whole old cache.
      from source_bundle import read_bytes
      writer.write(read_bytes(source['file']))
     else:
      with zipfile.ZipFile(source['zip']) as z,z.open(source['member']) as reader:shutil.copyfileobj(reader,writer)
   if digest(temp)!=row['sha256']:raise ValueError('Restore hash differs')
   if target.exists():raise FileExistsError('Restore destination created concurrently')
   os.rename(temp,target);count+=1
  finally:
   if temp.exists():temp.unlink()
 from source_bundle import restore as restore_bundled
 return count+restore_bundled(root)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True)
 print('Restored files:',restore(p.parse_args().root))
