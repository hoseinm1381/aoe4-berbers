"""Preserve non-SGA inputs/provenance from retired packages; retire only game history."""
from pathlib import Path
import collections,zipfile
import workspace as w

def main():
    plan=w.read(w.OUT/'cleanup-candidates.json.gz');inventory=w.read(w.OUT/'inventory.json.gz')
    removed={r['path'] for r in plan['retire']+plan['bundled']}
    available={r['sha256'] for r in inventory if r['path'] not in removed}
    source=w.read(w.HERE/'source-index.json.gz');assert w.sha(source['bundle'])==source['bundle_sha256']
    available.update(r['sha256'] for r in source['files'])
    destination=w.INPUTS/'retired-package-inputs.zip';assert not destination.exists()
    records=[];stored=set()
    with zipfile.ZipFile(destination,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as out:
        for r in plan['retire']:
            path=Path(r['path'])
            if path.suffix.lower()!='.zip' or path.name=='source-blobs.zip':continue
            with zipfile.ZipFile(path) as z:
                assert z.testzip() is None
                for n in z.namelist():
                    if n.endswith('/') or n.lower().endswith('.sga'):continue
                    w.member_name(n);raw=z.read(n);h=w.digest(raw)
                    route='retained input'
                    if h not in available:
                        if h not in stored:out.writestr(h,raw);stored.add(h)
                        route='retired-package-inputs.zip/'+h
                    records.append({'original_package':str(path),'member':n,'sha256':h,'bytes':len(raw),'retained_route':route})
            print('PACKAGE_INPUTS_PRESERVED',path.name,flush=True)
    with zipfile.ZipFile(destination) as z:
        assert z.testzip() is None
        for h in stored:assert w.digest(z.read(h))==h
    w.save(w.HERE/'retired-package-inputs.json.gz',{'archive':str(destination),'sha256':w.sha(destination),'files':records})
    w.save(w.OUT/'retired-package-input-proof.json',{'status':'passed','non_sga_members_preserved':len(records),'unique_additional_inputs':len(stored),'additional_archive_bytes':destination.stat().st_size,'sha256':w.sha(destination),'only_historical_sga_payloads_deliberately_retired':True})
    print('ALL_RETIRED_PACKAGE_INPUTS_QUALIFIED',flush=True)
if __name__=='__main__':main()
