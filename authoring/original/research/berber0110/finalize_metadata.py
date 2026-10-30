"""Correct release scope labels; preserve all game payload bytes and cleanup history."""
from pathlib import Path
import json,hashlib,zipfile
from release import ROOT,OUT,ZIP,FINAL,verify
from pipeline import sha,write
report=json.loads((OUT/'release-validation.json').read_text(encoding='utf8'))
previous=report['zip_sha256']
temp=OUT/'Berber-0.11.0.metadata.tmp'
assert not temp.exists()
changed=[]
with zipfile.ZipFile(ZIP) as source,zipfile.ZipFile(temp,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as target:
    for info in source.infolist():
        raw=source.read(info.filename)
        if info.filename=='garrison.json':
            data=json.loads(raw)
            data['details']['description']=data['details']['description'].replace('Connected land normal/Nomad, teams/FFA candidate.','Normal starts on connected land, teams/FFA candidate.')
            raw=(json.dumps(data,indent=2)+'\n').encode()
            changed.append(info.filename)
        elif info.filename=='VOICE_COVERAGE.json':
            data=json.loads(raw)
            data['runtime_test']=data['runtime_test'].replace('Fresh0.10.1 native acceptance pending.','Fresh0.11.0 native acceptance pending.')
            raw=(json.dumps(data,indent=2)+'\n').encode()
            changed.append(info.filename)
        else:
            assert hashlib.sha256(raw).hexdigest()==report['zip_members'][info.filename]
        target.writestr(info,raw,compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
        report['zip_members'][info.filename]=hashlib.sha256(raw).hexdigest()
with zipfile.ZipFile(temp) as z:assert z.testzip() is None
temp.replace(ZIP)
report.update(zip_sha256=sha(ZIP),zip_bytes=ZIP.stat().st_size)
write(OUT/'release-validation.json',report)
(OUT/'SHA256SUMS.txt').write_text(sha(ZIP)+'  '+ZIP.name+'\n'+sha(FINAL)+'  '+FINAL.name+'\n',encoding='ascii')
verify()
plan=json.loads((OUT/'cleanup-plan.json').read_text(encoding='utf8'))
updates={str(ZIP):sha(ZIP),str(ROOT/'research/berber0110/release.py'):sha(ROOT/'research/berber0110/release.py')}
for name,expected in plan['protected_hashes'].items():
    assert sha(Path(name))==updates.get(name,expected),name
write(OUT/'metadata-correction.json',{'status':'passed','changed_zip_members':changed,'previous_zip_sha256':previous,'final_zip_sha256':sha(ZIP),'sga_unchanged':sha(FINAL)==report['sga_sha256'],'cleanup_history':'Original deletion inventory and hashes preserved; all protected inputs rechecked, with only ZIP metadata and release recipe intentionally corrected.','protected_inputs_rechecked':len(plan['protected_hashes']),'temporary_copy_removed':not temp.exists()})
print('FINAL_DELIVERY_VERIFIED',report['zip_bytes'],report['zip_sha256'])
