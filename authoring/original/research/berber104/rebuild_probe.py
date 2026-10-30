"""Exercise composition with no work directory, using retained inputs only."""
from pathlib import Path
import importlib.util,json,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('probe104',HERE/'build.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
release=b.OUT;probe=release/'work/rebuild-probe';assert not probe.exists()
probe.mkdir(parents=True)
for name in ('compiled-validation.json','mcp-check.json'):shutil.copyfile(release/name,probe/name)
b.OUT=probe;b.WORK=probe/'work';b.FINAL=probe/'Berber_future_kingdom.sga';b.ZIP=probe/'Berber-1.0.4.zip'
assert not b.WORK.exists()
b.checks();b.compose()
expected=json.loads((release/'member-sha256-proof.json').read_text())
actual=json.loads((probe/'member-sha256-proof.json').read_text())
assert actual['after']==expected['after']
b.write(release/'rebuild-probe.json',{'status':'passed','work_directory_initially_absent':True,'retained_inputs_only':True,'all_decoded_members_identical':len(actual['after']),'reproduced_archive_sha256':b.sha(b.FINAL),'release_archive_sha256':expected['archive_sha256'],'byte_identical_archive':b.sha(b.FINAL)==expected['archive_sha256'],'native_match':'not run'})
print('REBUILD_PROBE_PASSED',len(actual['after']),'identical decoded members')
