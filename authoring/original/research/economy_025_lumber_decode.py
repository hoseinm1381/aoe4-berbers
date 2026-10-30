import os,json,subprocess
from pathlib import Path
R=Path.cwd();O=R/'output/berber_update_0_2_5/authors/lumber';G=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'; C=G/'bin/core/garrison-core.exe'
paths=['art/civilizations/common/structures/lumber_camp/com_lumber_camp_crane_age01/com_lumber_camp_crane_age01','art/civilizations/common/props/buildpile_wood_lumber/buildpile_wood_lumber','art/civilizations/common/props/wood_logs/wood_logs','art/civilizations/common/props/bow_saw/bow_saw']
for p in paths:
 r=subprocess.run([str(C),'convert','decode-static','--logical-path',p+'.rgm','--config','C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.local.json','--index','C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3','--output-root',str(O/'stock')],capture_output=True,text=True)
 (O/(Path(p).name+'-decode.log')).write_text(r.stdout+r.stderr);assert r.returncode==0,(p,r.stderr);print(p,flush=True)
