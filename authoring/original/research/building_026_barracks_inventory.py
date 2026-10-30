import os,sys,json,sqlite3,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'output/berber_update_0_2_6/authors/barracks';A=R/'art/building_remix_0_2_6/barracks';O.mkdir(parents=True,exist_ok=True);A.mkdir(parents=True,exist_ok=True)
G=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';S=G/'bin/sga-archiver.exe';C=G/'bin/core/garrison-core.exe'
c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
rows=c.execute("select logical_path,archive_path from resolved_assets where logical_path like '%barracks%' and logical_path like '%abb%' and extension='.bin'").fetchall();c.close()
if not rows:
 arc='E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Data.sga';result=subprocess.run([str(S),'inspect',arc],capture_output=True,text=True,check=True);members=json.loads(result.stdout)['archive']['members'];rows=[(m['path'],arc) for m in members if 'abb_barracks' in m['path'] and m['path'].endswith('.bin')]
print(rows)
sys.path.insert(0,str(R/'research'));from economy_025_native_stamp import NativeTree
for p,arc in rows:
 dest=O/'stamps'/Path(p).name;dest.parent.mkdir(exist_ok=True)
 if not dest.exists():subprocess.run([str(S),'extract-member',arc,p,str(dest)],check=True,capture_output=True)
 t=NativeTree(dest);items=[t.describe(x) for x in t.objects.values()];(dest.with_suffix('.json')).write_text(json.dumps(items,indent=2));print(p,[(x['type'],x['fields'].get('m_blueprint')) for x in items if 'm_blueprint' in x['fields']])
