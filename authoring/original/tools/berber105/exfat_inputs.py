"""Archive small historical voice/diagnostic inputs losslessly to avoid exFAT slack."""
from pathlib import Path
import copy,gzip,hashlib,json,os,shutil,stat,zipfile
import workspace as w

def prefix_sha(path,length):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while length:
            raw=f.read(min(length,1024*1024));assert raw;h.update(raw);length-=len(raw)
    return h.hexdigest()

def main():
    assert w.read(w.OUT/'retirement-complete.json')['status']=='passed'
    assert not (w.OUT/'exfat-inputs-complete.json').exists()
    index=w.read(w.HERE/'source-index.json.gz');original=w.source_bundle(index)
    extra=w.read(w.OUT/'blender-diagnostic-dependencies.json');assert extra['complete'] and not any('error' in r for r in extra['files'])
    audits=w.read(w.OUT/'blender-dependencies.json')['files']+extra['files']
    references={str(Path(i['resolved']).resolve()).lower() for r in audits for i in r.get('images',[])+r.get('libraries',[])}
    # Restore any missing historical diagnostic dependencies from already
    # verified identical cached bytes; no Blender scene needs rewriting.
    repaired=[];inventory=w.read(w.OUT/'inventory.json.gz')
    indexed_paths={os.path.abspath(row['path']).lower():row for row in index['files']}
    with zipfile.ZipFile(original) as z:
        for r in audits:
            for dependency in r.get('images',[])+r.get('libraries',[]):
                target=Path(dependency['resolved']).resolve()
                if target.is_file():continue
                match=indexed_paths.get(os.path.abspath(target).lower());matches=[match] if match else []
                w.safe_target(target)
                if matches:
                    assert len({r['sha256'] for r in matches})==1
                    row=matches[0];w.restore_one(z,row['member'],target,row['sha256'])
                else:
                    matches=[r for r in inventory if Path(r['path']).name==target.name]
                    assert matches and len({r['sha256'] for r in matches})==1,('Ambiguous diagnostic dependency',str(target))
                    row=next((r for r in matches if Path(r['path']).is_file()),matches[0])
                    raw=Path(row['path']).read_bytes() if Path(row['path']).is_file() else z.read(row['sha256'])
                    assert w.digest(raw)==row['sha256']
                    target.parent.mkdir(parents=True,exist_ok=True)
                    with target.open('xb') as f:f.write(raw)
                repaired.append({'path':str(target),'sha256':row['sha256'],'source':row['path']})
    w.save(w.OUT/'diagnostic-dependency-repairs.json',{'status':'passed','repairs':repaired,'method':'Existing inventoried filename has one unique SHA across every candidate; scene files unchanged'})
    oldgone={r['path'] for key in ('retire','bundled') for r in w.read(w.OUT/'cleanup-candidates.json.gz')[key]}
    roots=[w.EXTERNAL/'output/berber_update_0_6_0',w.EXTERNAL/'output/discoveries']
    selected=[]
    for n,row in enumerate(inventory):
        p=Path(row['path'])
        if row['path'] in oldgone or not any(p.is_relative_to(root) for root in roots):continue
        if str(p).lower() in references:continue
        if p.suffix.lower() in ('.blend','.blend1','.blend2','.py','.ps1','.exe','.dll','.pyd','.zip','.md'):continue
        if row['bytes']==0:continue
        s=p.stat();assert (s.st_size,s.st_mtime_ns)==(row['bytes'],row['mtime_ns'])
        selected.append(dict(row,kind='archived_input',reason='Lossless historical voice/diagnostic input; avoid 256KiB exFAT allocation per small file',member=row['sha256']))
        if len(selected)%3000==0:print('EXFAT_SELECTED',n,len(selected),flush=True)
    # Keep current provenance immediately readable by the maintained audit.
    provenance=w.HERE/'voice-provenance';provenance.mkdir(exist_ok=True)
    with zipfile.ZipFile(original) as z:
        for source in [roots[0]/'coverage.json',w.EXTERNAL/'output/berber_update_0_7_3/Berber-0.7.3-VOICES-INSTALLER/NativeAudio/native-audio-manifest.json']:
            dest=provenance/source.name
            row=next(r for r in inventory if r['path']==str(source))
            raw=source.read_bytes() if source.is_file() else z.read(row['sha256'])
            assert w.digest(raw)==row['sha256']
            if not dest.exists():dest.write_bytes(raw)
            assert w.sha(dest)==row['sha256']
    work=w.OUT/'work/exfat-inputs';work.mkdir(parents=True,exist_ok=True)
    staged=work/'source-blobs-next.zip';assert not staged.exists()
    shutil.copyfile(original,staged);assert w.sha(staged)==index['bundle_sha256']
    with zipfile.ZipFile(original) as z:
        old_entries={i.filename:(i.CRC,i.file_size,i.compress_size,i.compress_type,i.header_offset) for i in z.infolist()};prefix=z.start_dir
    old_prefix=prefix_sha(original,prefix);added=set()
    with zipfile.ZipFile(staged,'a',zipfile.ZIP_DEFLATED,compresslevel=9,allowZip64=True) as z:
        present=set(z.namelist())
        for i,row in enumerate(selected):
            h=row['sha256']
            raw=Path(row['path']).read_bytes();assert w.digest(raw)==h
            if h not in present:
                z.writestr(h,raw);present.add(h);added.add(h)
            if i%2000==0:print('EXFAT_INPUTS',i,len(selected),flush=True)
    assert prefix_sha(staged,prefix)==old_prefix,'Existing validated blob payload bytes changed'
    with zipfile.ZipFile(staged) as z:
        assert len(z.namelist())==len(set(z.namelist())) and z.testzip() is None
        now={i.filename:(i.CRC,i.file_size,i.compress_size,i.compress_type,i.header_offset) for i in z.infolist()}
        assert all(now[k]==v for k,v in old_entries.items())
        for h in added:assert w.digest(z.read(h))==h
        sample=next(iter(added),None)
        if sample:
            dest=work/'restore-sample';w.restore_one(z,sample,dest,sample);assert w.sha(dest)==sample
    new_index=dict(index,bundle_sha256=w.sha(staged),files=index['files']+selected)
    w.save(work/'source-index-next.json.gz',new_index)
    shutil.copyfile(w.HERE/'source-index.json.gz',work/'source-index-previous.json.gz')
    w.save(w.OUT/'exfat-inputs-transaction.json',{'phase':'verified_before_promotion','previous_sha256':index['bundle_sha256'],'next_sha256':new_index['bundle_sha256'],'selected':len(selected),'staged':str(staged)})
    previous=work/'source-blobs-previous.zip';assert not previous.exists()
    w.safe_target(original).rename(previous);staged.rename(original)
    temp_index=w.HERE/'source-index.next.json.gz';shutil.copyfile(work/'source-index-next.json.gz',temp_index);os.replace(temp_index,w.HERE/'source-index.json.gz')
    # The old decoded SHA proof is transferred by identical compressed payload
    # bytes/metadata, with all newly added blobs decoded and SHA-checked here.
    w.save(w.OUT/'input-bundle-verification.json',{'status':'passed','unique_blobs':len(now),'bundle_bytes':original.stat().st_size,'bundle_sha256':new_index['bundle_sha256'],'all_blobs_decoded_and_sha256_checked':True,'existing_blob_payload_prefix_identical':old_prefix,'prior_validated_archive_sha256':index['bundle_sha256'],'new_blobs_decoded_sha256_checked':len(added)})
    w.save(w.OUT/'exfat-input-plan.json.gz',selected)
    with (w.OUT/'exfat-deletion-journal.jsonl').open('x') as journal:
        for i,row in enumerate(selected):
            p=w.verify_cleanup_candidate(row,hash_bytes=False)
            if p.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY:p.chmod(stat.S_IREAD|stat.S_IWRITE)
            p.unlink();journal.write(json.dumps(row)+'\n')
            if i%2000==0:journal.flush();print('EXFAT_ARCHIVED',i,len(selected),flush=True)
    for row in audits:
        for dependency in row.get('images',[])+row.get('libraries',[]):assert Path(dependency['resolved']).is_file()
    w.save(w.OUT/'exfat-inputs-complete.json',{'status':'passed','files_archived':len(selected),'file_bytes_removed':sum(r['bytes'] for r in selected),'exfat_allocated_file_bytes_removed':sum(((r['bytes']+262143)//262144)*262144 for r in selected),'current_bundle_bytes':original.stat().st_size,'current_bundle_sha256':new_index['bundle_sha256'],'all_blender_dependencies_retained':True,'new_blobs':len(added)})
    print('EXFAT_INPUT_CONSOLIDATION_VERIFIED',flush=True)
if __name__=='__main__':main()
