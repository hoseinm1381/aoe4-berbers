from pathlib import Path
import json,shutil,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_3_0'
report=json.loads((OUT/'export-report.json').read_text());changes=[];affected=[]
for asset in report['assets']:
    folder=Path(asset['export'])
    for png in (folder/'materials').rglob('*.png'):
        with Image.open(png) as im:
            size=im.size;target=tuple(1<<(n-1).bit_length() for n in size)
            if size==target:continue
            backup=OUT/'texture-backups'/asset['name']/png.relative_to(folder);backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(png,backup)
            converted=im.resize(target,Image.Resampling.LANCZOS);converted.save(png)
            changes.append({'name':asset['name'],'file':str(png),'from':size,'to':target,'source_unchanged':True})
            affected.append(asset['name'])
(OUT/'texture-normalization.json').write_text(json.dumps({'changes':changes,'rebuild_names':sorted(set(affected))},indent=2))
print(json.dumps({'texture_fixes':len(changes),'models_rebuilt':len(set(affected))}))
