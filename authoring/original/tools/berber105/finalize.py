"""Preserve prior documentation, publish current rebuild index and exact accounting."""
from pathlib import Path
import ast,gzip,json,subprocess,sys,zipfile
import workspace as w
import allocation

DOCS=['STORAGE.md','PORTING.md','REBUILD_NEXT.md','README.md']
def save_prior_docs():
    target=w.OUT/'prior-documentation.zip'
    if target.exists():return
    originals={name:(w.ROOT/name).read_bytes() for name in DOCS}
    current=(w.ROOT/'research/source_bundle.py').read_text()
    node=next(n for n in ast.parse(current).body if isinstance(n,ast.FunctionDef) and n.name=='load')
    original=current.replace(ast.get_source_segment(current,node),"def load():return json.loads(INDEX.read_text(encoding='utf8')) if INDEX.exists() else {'files':[]}")
    original=original.replace('import argparse,gzip,hashlib','import argparse,hashlib').replace("EXTERNAL=Path(os.environ.get('BERBER_STORAGE','F:/aoe_4_temp/Berber_future_kingdom_ai_20261014'))","EXTERNAL=Path('F:/aoe_4_temp/Berber_future_kingdom_ai_20261014')")
    expected=next(r['sha256'] for r in w.read(w.OUT/'inventory.json.gz') if r['path']==str(w.ROOT/'research/source_bundle.py'))
    candidates=[original.encode(),original.replace('\n','\r\n').encode()]
    restored=next((raw for raw in candidates if w.digest(raw)==expected),None)
    assert restored is not None,'Preserve exact prior source reader before documenting its replacement'
    originals['research/source_bundle.py']=restored
    with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,raw in originals.items():z.writestr(name,raw)
    w.save(w.OUT/'documentation-changes.json',{'before':{name:w.digest(raw) for name,raw in originals.items()},'prior_documentation_zip_sha256':w.sha(target),'policy':'Preserve all previous text beneath current authoritative header; exact prior source reader retained in ZIP.'})

def main():
    assert w.read(w.OUT/'cleanup-report.json')['status']=='passed'
    assert w.read(w.OUT/'git-repack-result.json')['status']=='passed'
    save_prior_docs()
    with zipfile.ZipFile(w.OUT/'prior-documentation.zip') as z:old={name:z.read(name).decode('utf-8-sig') for name in DOCS}
    delivery=w.verify_zip(w.OUT/'Berber-1.0.5.zip');assert delivery['version']=='1.0.5'
    before=w.read(w.OUT/'storage-before.json');retired=w.read(w.OUT/'retirement-complete.json');git=w.read(w.OUT/'git-repack-result.json')
    note='''# Current: Berber 1.0.5 development workspace (2026-10-19)

Authoritative build/edit/restore instructions: [tools/berber105/README.md](tools/berber105/README.md).
Import: [Berber-1.0.5.zip](output/berber_update_1_0_5/Berber-1.0.5.zip).
All 8,529 game resources are unchanged from 1.0.4; native acceptance remains
pending with the user. Retained rollback is the original 1.0.4 ZIP. The single
immutable 1.0.4 SGA is also the 1.0.5 game archive and current rebuild baseline.
No duplicate loose 1.0.5 SGA is necessary. Its SHA256 is
`55629909581fd0035a141f212e38274d3e1f7f185fecffed635b821e2b7204a6`.

The maintained workflow imports no historical release helpers and needs no
older playable archive. Source/recipe/resource indexes, current cook snapshots,
compiled overrides, UV/speech protections and lossless restore routes are under
tools/berber105. Required compressed inputs are at F:/aoe_4_temp/
Berber_future_kingdom_ai_20261014/rebuild_inputs/current. Existing E:/F: art,
source, donor folders and junctions remain; unique ambiguous sources are kept.
Three adjacent donor trees (160,676,063 bytes) remain required; see the current
README relocation instructions and output/berber_update_1_0_5/adjacent-storage.json.

Historical sections below are provenance. Their earlier playable checkpoints
and release-generator dependencies have been retired. Use the current workflow
for new development; do not follow an older 'current release' paragraph.

'''
    for name in DOCS:(w.ROOT/name).write_text(note+old[name],encoding='utf8')
    (w.OUT/'NATIVE_ACCEPTANCE.md').write_text((w.HERE/'NATIVE_ACCEPTANCE.md').read_text())
    (w.OUT/'REBUILD.md').write_text('See tools/berber105/README.md in the retained E: editable workspace.\n\nThe current archive is final1.0.4, SHA256 '+w.BASE_SHA+'.\n1.0.5 changes package metadata only; use explicit scoped overlays for future edits.\n')
    versions={'python':sys.version,'python_executable':sys.executable,'garrison_manifest':(w.EXT/'blender_manifest.toml').read_text(),'archiver':str(w.ARCH),'archiver_sha256':w.sha(w.ARCH),'compatible_sga_reader':str(w.READER),'blender':'5.2.2 LTS (434-file native audit)','ffmpeg':w.run('ffmpeg','-version').splitlines()[0]}
    w.save(w.OUT/'toolchain.json',versions)
    editor=Path('E:/Games/steamapps/common/Age of Empires IV/EssenceEditor.exe')
    versions['content_editor']={'path':str(editor),'file_version':'1.0.0.0','product_version':'1.0.0.0','sha256':w.sha(editor),'note':'Generic Windows version fields; binary SHA pins the verified installed cook tool'}
    w.save(w.OUT/'toolchain.json',versions)
    # Compact completed intermediate journals without losing their evidence.
    for name in ('inventory-hashes.jsonl','deletion-journal.jsonl','exfat-deletion-journal.jsonl'):
        source=w.OUT/name;target=source.with_suffix(source.suffix+'.gz')
        if source.exists():
            raw=source.read_bytes()
            with gzip.open(target,'wb',compresslevel=9) as f:f.write(raw)
            with gzip.open(target,'rb') as f:assert w.digest(f.read())==w.digest(raw)
            w.safe_target(source).unlink()
    changes=w.read(w.OUT/'documentation-changes.json');changes['after']={name:w.sha(w.ROOT/name) for name in DOCS};changes['after']['research/source_bundle.py']=w.sha(w.ROOT/'research/source_bundle.py');w.save(w.OUT/'documentation-changes.json',changes)
    archivebytes=w.BASE.stat().st_size+w.ROLLBACK.stat().st_size+(w.OUT/'Berber-1.0.5.zip').stat().st_size
    old_artifacts=sum(r['bytes'] for r in w.read(w.OUT/'cleanup-candidates.json.gz')['retire'] if Path(r['path']).suffix.lower()=='.sga' or Path(r['path']).name.startswith('Berber-'))+w.BASE.stat().st_size+w.ROLLBACK.stat().st_size
    adjacent=sum(r['bytes'] for r in w.read(w.OUT/'adjacent-storage.json'))
    (w.OUT/'SHA256SUMS.txt').write_text(delivery['zip_sha256']+'  Berber-1.0.5.zip\n'+w.BASE_SHA+'  ../berber_update_1_0_4/Berber_future_kingdom.sga\n'+w.ROLLBACK_SHA+'  ../berber_update_1_0_4/Berber-1.0.4.zip\n')
    for _ in range(5):
        after=w.totals();drives={}
        for root in (w.ROOT,w.EXTERNAL):
            b=before[str(root)]['total'];a=after[str(root)]['total'];drives[root.drive]={'before':b,'after':a,'reclaimed':b-a}
        accounting={'status':'passed','units':'physical file bytes, decimal GB; junction targets counted once','drives':drives,'total_before':sum(x['before'] for x in drives.values()),'total_after':sum(x['after'] for x in drives.values()),'net_reclaimed':sum(x['reclaimed'] for x in drives.values()),'git_before':before[str(w.ROOT)]['.git'],'git_after':after[str(w.ROOT)]['.git'],'git_objects_preserved':git['object_count_preserved'],'current_and_rollback_artifacts':archivebytes,'other_retained_development_and_evidence':sum(x['after'] for x in drives.values())-after[str(w.ROOT)]['.git']-archivebytes,'adjacent_required_donors_retained':adjacent,'observed_scratch_bytes_removed':w.read(w.OUT/'cleanup-report.json')['scratch']['reclaimed'],'native_acceptance':'pending; user tests','retained_exceptions':['Unique ambiguous editable sources/backups and their texture dependencies','Native donor/cook resources without a proven source replacement','12.5MB root Content Editor cache: complete root art cook not qualified','Three adjacent native donor trees referenced by historical art recipes','All Git history and unreachable objects; no expiration']}
        alloc=allocation.measure(w.EXTERNAL,262144)
        initial_alloc=w.read(w.OUT/'allocation-report.json')['initial_inventoried_F_allocated_file_bytes']
        accounting['F_regular_file_allocation']={'before':initial_alloc,'after':alloc['totals']['allocated_cluster_bytes'],'reclaimed':initial_alloc-alloc['totals']['allocated_cluster_bytes'],'cluster_bytes':262144,'excludes_directory_metadata':True}
        accounting['canonical_inputs']=w.read(w.OUT/'exfat-inputs-complete.json')
        accounting['categories']={
            'Git':{'before':accounting['git_before'],'after':accounting['git_after']},
            'Designated release artifacts':{'before':old_artifacts,'after':archivebytes},
            'Development inputs and evidence':{'before':accounting['total_before']-accounting['git_before']-old_artifacts,'after':accounting['other_retained_development_and_evidence']}}
        for category in accounting['categories'].values():category['reclaimed']=category['before']-category['after']
        w.save(w.OUT/'storage-accounting.json',accounting)
        table='\n'.join('| '+d+' | '+f"{r['before']/1e9:.3f} GB | {r['after']/1e9:.3f} GB | {r['reclaimed']/1e9:.3f} GB |" for d,r in drives.items())
        categories='\n'.join('| '+d+' | '+f"{r['before']/1e9:.3f} GB | {r['after']/1e9:.3f} GB | {r['reclaimed']/1e9:.3f} GB |" for d,r in accounting['categories'].items())
        report=f'''# Berber 1.0.5 delivery and storage report

All 8,529 resources retain exact final1.0.4 bytes. Manifest version is1.0.5.
ZIP SHA256: `{delivery['zip_sha256']}` ({delivery['bytes']:,} bytes).
SGA SHA256: `{w.BASE_SHA}`.

| Drive | Before | After | Reclaimed |
|---|---:|---:|---:|
{table}

| Category | Before | After | Reclaimed |
|---|---:|---:|---:|
{categories}

Net reclaimed: **{accounting['net_reclaimed']/1e9:.3f} GB**. Totals count physical
files once and exclude the separately reported {adjacent/1e9:.3f} GB adjacent
required donors. No file movement to another drive is counted as reclamation.
F: uses exFAT with 256 KB allocation units. Regular-file allocation fell from
{initial_alloc/1e9:.3f} to {alloc['totals']['allocated_cluster_bytes']/1e9:.3f} GB
({accounting['F_regular_file_allocation']['reclaimed']/1e9:.3f} GB reclaimed),
excluding directory metadata. File bytes and allocated space are separate.
Git shrank from {accounting['git_before']/1e9:.3f} to {accounting['git_after']/1e9:.3f}
GB while preserving all {git['object_count_preserved']:,} object IDs, refs,
reflogs, staged entries and linked worktree. A read-only status refreshed index
cache bytes; its semantic preservation is documented separately.

Release/rollback artifacts: {archivebytes/1e9:.3f} GB. Other retained development
inputs/evidence: {accounting['other_retained_development_and_evidence']/1e9:.3f} GB.
This includes the {accounting['canonical_inputs']['current_bundle_bytes']/1e9:.3f} GB
lossless canonical input bundle. All 46,265 unique blobs passed full decoded
SHA256 verification; four input categories passed isolated restoration.
Unique ambiguous sources, required native donors and the small root editor
cache remain intentionally preserved; detailed reasons are in accounting.

Verified: six cleanup/restore safety tests;11 native mappings; fresh Content
Editor cook/readback;434 Blender dependency audits; two disposable Blender
edits/exports; native geometry/UV/speaker/Lua/audio probes; cold exact rebuild
and packaging with original Berber reads denied; canonical input restoration;
complete resource inventory; old-package non-SGA input preservation; protected
file rehashes; Git full fsck; post-cleanup ZIP/SGA/rollback hashes.

Source and rebuild: tools/berber105/README.md. The original1.0.4 ZIP is the sole
playable rollback. Older author scripts are historical references; current
builds use only the maintained workflow. Native import/match testing remains
the user's acceptance step. Community Civilization Pack and normal Berber
edition were not modified.
'''
        (w.OUT/'REVIEW.md').write_text(report,encoding='utf8')
    assert w.verify_zip(w.OUT/'Berber-1.0.5.zip')==delivery and w.sha(w.BASE)==w.BASE_SHA and w.sha(w.ROLLBACK)==w.ROLLBACK_SHA
    print('FINALIZED',json.dumps(accounting),flush=True)
if __name__=='__main__':main()
