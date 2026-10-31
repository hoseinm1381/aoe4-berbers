import subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/tuareg_lowprofile_shield_trial'
python=r'E:/Blender5.2/5.2/python/bin/python.exe'
for stage in ('cook','candidate','package'):
 with (OUT/(stage+'-stdout.log')).open('w') as a,(OUT/(stage+'-stderr.log')).open('w') as b:
  p=subprocess.run([python,str(ROOT/'art/tuareg_refined/build_lowprofile_shield.py'),stage],stdout=a,stderr=b,timeout=1200)
 assert p.returncode==0,(stage,p.returncode)
 (OUT/'pipeline-status.json').write_text(json.dumps({'last_completed':stage,'exit_code':p.returncode}))
