"""Read back the latest successful original-project cook for trial .2."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'output/tuareg_shield_test'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
build=json.loads((WORK/'build-result.json').read_text())
assert build['status']=='succeeded' and build['exit_code']==0 and len(build['archives'])==1
release=json.loads((WORK/'release-result.json').read_text())
assert release['status']=='verified' and release['editor_archive_sha256']==build['archives'][0]['sha256']
archive=Path(release['archive'])
assert hashlib.sha256(archive.read_bytes()).hexdigest()==release['sha256']
inventory=json.loads(subprocess.check_output([str(EXT/'bin/sga-archiver.exe'),'list',str(archive),'--verify'],text=True))
assert inventory['archive']['verification']['verified'] is True
assert Path(inventory['archive']['path']).resolve()==archive.resolve()
readback=WORK/'final-readback-v2-combined'
assert not readback.exists(),'Choose a new readback folder after a later rebuild; do not reuse stale output.'
subprocess.run([str(EXT/'bin/sga-archiver.exe'),'unpack',str(archive),'--output',str(readback)],check=True,capture_output=True)
(WORK/'evidence/final-inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
print(json.dumps({'archive':str(archive),'members':len(inventory['members']),'readback':str(readback)}))
