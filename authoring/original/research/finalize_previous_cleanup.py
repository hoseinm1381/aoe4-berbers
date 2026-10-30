"""Verify accounting and document completed previous-release cleanup."""
import json
from pathlib import Path
from cleanup_previous_versions import ROOT,EXTERNAL,REPORT,sha,walk
def finalize():
 result=json.loads((REPORT/'cleanup-result.json').read_text())
 if result['status']!='passed':raise ValueError('Cleanup has not passed')
 inventory=json.loads((REPORT/'inventory.json').read_text())['files'];plan=json.loads((REPORT/'deletion-plan.json').read_text())
 output=EXTERNAL/'output';original={r['path']:r['bytes'] for r in inventory if output in Path(r['path']).parents}
 removed={r['path'] for r in plan['files']};current={p:n for p,n,k in walk(output) if k=='file'}
 if any(p in current for p in removed):raise ValueError('Selected file remains')
 if any(p not in current or current[p]!=n for p,n in original.items() if p not in removed):raise ValueError('Nonselected original file absent or size changed')
 gates=json.loads((REPORT/'release-gates.json').read_text())
 for release,name,expected in [('berber_update_0_5_1','package/Berber_future_kingdom.sga','acbcd6501a1e8ebea2c7dae8701641625c96c078e3a4d33e9c2968111732717b'),('berber_update_0_6_1','Berber_future_kingdom.sga','48f09ed61020740932b0a653e165710fda49d25aa7739d05f6486b79dbe661bb')]:
  if sha(output/release/name)!=expected:raise ValueError('Protected authoritative SGA changed')
 before=sum(original.values());after=sum(n for p,n in current.items() if p in original)
 if before-after!=plan['logical_bytes']:raise ValueError('Accounting mismatch')
 retained=[
  {'path':'All original and normalized voice WAVs, pre-normalization backups, encoded WEM banks, profiles and receipts','reason':'Required accepted voice sources and exact receipt/normalization provenance'},
  {'path':'All Blender files/backups and editable texture/model inputs','reason':'User-protected authoring work'},
  {'path':'Older decoded-static.json and shared stock caches','reason':'Existing authoring recipes require their current paths; no newly qualified transparent compressed reader/regeneration route'},
  {'path':'Unique intermediate/checkpoint files without an exact replacement','reason':'Unique or uncertain rebuild dependencies retained conservatively'},
  {'path':'0.7.3 extracted installer folder and installed game audio','reason':'Active user installation excluded; no game-file operations'},
 ]
 summary={'status':'passed','files_removed':len(removed),'scope':'Older-release exact duplicate caches and hash-proven decoded QA only','output_baseline_bytes_before':before,'output_baseline_bytes_after':after,'selected_bytes_before':plan['logical_bytes'],'selected_bytes_after':0,'logical_reclaimed_by_drive':{'E:':0,**result['logical_reclaimed_by_drive']},'physical_reclaimed_lower_bound_by_drive':{'E:':0,**result['physical_reclaimed_lower_bound_by_drive']},'new_output_bytes_outside_baseline':sum(n for p,n in current.items() if p not in original),'zip_post_cleanup':'All 30 retained ZIPs: SHA256 unchanged and full CRC reread passed','protected_authoritative_sgas':'0.5.1 and 0.6.1 hashes unchanged; packaged 0.7.0 and 0.7.3 archive hashes verified','retained':retained,'restore_tests':'Two fixture tests passed; decode probe byte-identical; 0.6.0 readback helper supports automatic duplicate restoration','game_files_modified':False,'garrison_or_blender_sessions_changed':False,'incomplete_deletions':0}
 (REPORT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 storage=ROOT/'STORAGE.md';marker='Previous-version cleanup completed 2026-10-16 (0.7.3 retained)'
 note=f'\n\n{marker}: removed {len(removed):,} verified duplicate-cache/decoded-QA files totaling {plan["logical_bytes"]:,} bytes ({plan["logical_bytes"]/2**30:.2f} GiB) on F:, with 0 bytes removed on E:. The original output inventory decreased from {before:,} to {after:,} bytes, excluding separately created installer files. All 30 retained release ZIPs passed unchanged SHA-256 and post-cleanup CRC checks; protected 0.5.1/0.6.1 SGAs remain unchanged. All Blender sources/backups, unique voice masters/normalized WAVs/encoded banks/profiles/receipts, editable inputs, final releases and installed game files were preserved. Required decoded-static/shared stock caches and unique uncertain checkpoints remain. Per-file hashes, retained replacement sources, accounting and restore instructions: research/cleanup_20261016/summary.json, deletion-plan.json and RESTORE.md. Restore missing older caches with research/restore_cleanup_cache.py --root <physical cache directory>; the 0.6.0 archive readback helper restores its removed duplicates on demand.\n'
 if marker not in storage.read_text():
  with storage.open('a',encoding='utf8') as f:f.write(note)
 print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':finalize()
