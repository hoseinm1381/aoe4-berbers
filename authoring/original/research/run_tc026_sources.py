"""Render each TC age in a fresh owned Blender process to bound memory."""
import os,subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_2_6/authors/towncenter'
rows=[]
for age in range(1,5):
 env=os.environ.copy();env['BERBER_START_AGE']=str(age);env['BERBER_END_AGE']=str(age)
 with (OUT/f'lower-profile-age{age}.log').open('w',encoding='utf8') as log:
  p=subprocess.run(['E:/Blender5.2/blender.exe','--background','--factory-startup','--python',str(ROOT/'research/building_026_towncenter_blender.py')],env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 rows.append({'age':age,'exit_code':p.returncode});(OUT/'lower-profile-worker.json').write_text(json.dumps(rows,indent=2))
 if p.returncode:raise SystemExit(p.returncode)
print('ALL_FOUR_TC_LOWER_PROFILE_SOURCES_READY')
