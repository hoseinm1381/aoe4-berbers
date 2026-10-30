import subprocess,json,sqlite3,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[3]; Q=Path(__file__).parent
A=R/'art/buildings/marrakech';O=R/'output/buildings_batch/marrakech'
for p in [A,O]:p.mkdir(parents=True,exist_ok=True)
bin=Path('C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin')
for key,path in [('core','attrib/ebps/races/core/buildings/building_wonder_age2.rgd'),('mal','attrib/ebps/races/malian/buildings/building_landmark_age2_landmarkd_control_mal.rgd'),('age_apply','attrib/state_tree/building_action_apply/buildings/landmark_age_2_action_apply.rgd')]:
 r=Q/(key+'.rgd');x=r.with_suffix('.xml')
 if not r.exists():
  res=subprocess.run([str(bin/'sga-archiver.exe'),'extract-member','E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga',path,str(r)],capture_output=True,text=True)
  if res.returncode:print(key,res.stderr);continue
 if not x.exists():subprocess.run([str(bin/'sga-archiver.exe'),'decode-rgd',str(r),str(x)],check=True,capture_output=True)
c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
rows=c.execute("select logical_path,archive_path from resolved_assets where extension='.rgm' and logical_path like '%malian%landmark_2%'").fetchall();c.close()
(Q/'catalog.json').write_text(json.dumps(rows,indent=2))
p=next(row[0] for row in rows if 'landmark_2b/' in row[0])
if not list((Q/'stock').glob('*/decoded-static.json')):
 res=subprocess.run([str(bin/'core/garrison-core.exe'),'convert','decode-static','--logical-path',p,'--config','C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.local.json','--index','C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3','--output-root',str(Q/'stock')],capture_output=True,text=True)
 (Q/'decode_result.json').write_text(json.dumps({'exit':res.returncode,'stdout':res.stdout,'stderr':res.stderr},indent=2));res.check_returncode()
for source,target in [('art/buildings/tlemcen/geometry_helpers.py','art/buildings/marrakech/geometry_helpers.py'),('research/buildings_batch/tlemcen/run_build.py','research/buildings_batch/marrakech/run_build.py')]:
 text=(R/source).read_text().replace('tlemcen','marrakech').replace('Tlemcen','Marrakech');(R/target).write_text(text)
print('PREPARED',p)
