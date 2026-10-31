"""Record trial .2 source hashes and rollback scope without touching gameplay."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'output/tuareg_shield_test'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
integration=json.loads((WORK/'model-integration.json').read_text())
sources=json.loads((WORK/'source-integration.json').read_text())
rows=json.loads((WORK/'editor-attachment-sources.json').read_text())
for row in rows:
    row['inheritance']='exact Donso parent list identities; only body/shield model paths overridden; stock left-palm socket and remaining fields inherited'
    row['current_sha256']=sha(ROOT/row['source'])
sources['private_editor_instances']=rows
sources['private_native_models']=integration
sources['archive_integration']='Content Editor compiles attachment XML; Garrison archiver grafts 20 genuine pre-cooked model resources into the complete original cook'
sources['repair_status']='built/readback pending package and fresh native owner-provider/appearance verification'
(WORK/'source-integration.json').write_text(json.dumps(sources,indent=2),encoding='utf-8')
(WORK/'editor-attachment-sources.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
manifest={'restore':sources['changes'],'remove':[{'file':row['source'],'sha256':row['current_sha256']} for row in rows]+integration['resources']}
for row in manifest['restore']:
    assert sha(ROOT/row['file'])==row['after_sha256']
    assert sha(WORK/'before'/row['file'])==row['before_sha256']
for row in manifest['remove']:assert sha(ROOT/row['file'])==row['sha256']
(WORK/'rollback-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
with (WORK/'progress.md').open('a',encoding='utf-8') as ledger:
    ledger.write('\n- Corrected generic @variant references to installed model_variants.art_reference canonical native File paths. Rejected the earlier failed @ cook; no literal @ model path is delivered.\n- Original Content Editor cook 195553 exited 0 with 243 members but omits pre-cooked native art inputs. Installed Garrison archiver graft added only 20 verified model resources; all 243 editor members were preserved and combined readback has 263 members.\n- Source guard: ten tier references; 238 unrelated baseline hashes preserved. Tuning validation: 0 errors, 2 preexisting locale warnings. Rollback manifest now covers four attachment XML and 20 native model files.\n- Native promotion and visible actors are still pending trial .2; adding genuine model resources is a package repair, not proof the launcher will admit the owner.\n')
print(json.dumps({'restore_entities':len(manifest['restore']),'remove_trial_files':len(manifest['remove'])}))
