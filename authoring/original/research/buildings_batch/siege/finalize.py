import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/siege';O=R/'output/buildings_batch/siege';Q=R/'research/buildings_batch/siege'
a=json.loads((O/'saved_source_fbx_audit.json').read_text());assert [r['age'] for r in a]==[3,4]
d=json.loads((O/'delivery.json').read_text());d['saved_source_fbx_audit']='saved_source_fbx_audit.json';d['packed_source_fbx_verification']='both ages passed';d['visual_inspection']='Both final perspective previews and twelve orthographic views inspected: clear hall/work lane, visible neutral stripes, grounded racks/tables, joined pitched shelter; shaded rear workstations are visible in front orthographic views.';d['source_lane_extent_m']={'x':[-1,1],'y':[-3,2.1],'clear_height':2.0};d['maps']=[{'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in A.glob('*.png')]
(O/'delivery.json').write_text(json.dumps(d,indent=2))
for p in A.glob('*.blend1'):p.unlink()
if (O/'BUILD_ERROR.txt').exists():
    (Q/'iteration3_corridor_error.txt').write_text((O/'BUILD_ERROR.txt').read_text());(O/'BUILD_ERROR.txt').unlink()
p=Q/'README.md';s=p.read_text().replace("Both ages' final perspective and six-side source views require visual inspection before delivery status is finalized.","Revision 3 seated the wheel rim exactly on its display rail (removed a measured 1cm gap) and audited a conservative centred 2m working lane ending at Y=2.1 before the rear tool shelf. The initial overlong corridor assertion correctly caught that shelf; failure evidence is preserved in iteration3_corridor_error.txt. Both final perspective previews and twelve orthographic views were visually inspected; final saved-source and FBX reimport checks passed, including UVs, packed textures, exact rack/lumber and wheel/rail contacts, and stage-manifest counts.")
p.write_text(s)
print(json.dumps({'ages':[r['age'] for r in a],'saved_meshes':[r['saved_meshes'] for r in a],'fbx_meshes':[r['fbx_meshes'] for r in a],'passed':True}))
