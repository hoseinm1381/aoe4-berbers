"""Exercise actual retained bytes after cleanup; remove only probe-owned restores."""
from pathlib import Path
import hashlib,json,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import source_bundle as sb
import restore_cleanup_cache as legacy
from inventory import REPORT,sha,save

rows=sb.load()['files'];proof=[]
for kind in ('decoded','projection','duplicate_cache'):
 row=min((r for r in rows if r['kind']==kind),key=lambda r:r['bytes'])
 p=Path(row['path']);assert not p.exists()
 raw=sb.read_bytes(p);assert hashlib.sha256(raw).hexdigest()==row['sha256']
 assert sb.restore(p)==1 and sha(p)==row['sha256']
 assert sb.restore(p)==0
 # Exact file was absent at entry, and created by this test. No recursion.
 sb.safe_target(p);assert sha(p)==row['sha256'];p.unlink()
 proof.append({'kind':kind,'path':str(p),'bytes':row['bytes'],'sha256':row['sha256'],'direct_read':'passed','actual_restore':'passed','idempotence':'passed','probe_removed':True})
audio=next(r for r in rows if r['kind']=='duplicate_cache' and Path(r['path']).suffix in ('.wav','.wem'))
with tempfile.TemporaryDirectory(prefix='legacy-restore-probe-',dir=REPORT) as scratch:
 scratch=Path(scratch);target=scratch/('cache/file'+Path(audio['path']).suffix)
 (scratch/'deletion-plan.json').write_text(json.dumps({'files':[{'path':str(target),'sha256':audio['sha256'],'restore':{'file':audio['path']}}]}))
 old=legacy.REPORT;legacy.REPORT=scratch
 try:
  assert legacy.restore(target.parent)==1 and sha(target)==audio['sha256']
  target.write_bytes(b'user edit');assert legacy.restore(target.parent)==0 and target.read_bytes()==b'user edit'
 finally:legacy.REPORT=old
save(REPORT/'restore-probes.json',{'status':'passed','real_bundled_inputs':proof,'legacy_restore_reads_archived_source':'passed','existing_user_edits':'preserved','temporary_probe_tree':'removed'})
print('ACTUAL_SOURCE_RESTORES_PASSED',len(proof),'plus legacy audio and edited-file checks')
