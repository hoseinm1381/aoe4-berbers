"""Read installed native Town Center assemblies and decode exact used components."""
import os,sys,sqlite3,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_2_6/authors/towncenter';ART=ROOT/'art/building_remix_0_2_6/towncenter'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
CORE=EXT/'bin/core/garrison-core.exe';ARCH=EXT/'bin/sga-archiver.exe';INDEX=Path('C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3');CONFIG=INDEX.with_name('game-assets.local.json')
OUT.mkdir(parents=True,exist_ok=True);ART.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(EXT),str(ROOT/'research')]
from economy_025_native_stamp import NativeTree
def run(name,args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf8');(OUT/(name+'.log')).write_text(p.stdout+p.stderr,encoding='utf8');assert p.returncode==0,(name,p.stderr);return p.stdout
def main():
 c=sqlite3.connect('file:'+str(INDEX)+'?mode=ro',uri=True)
 rows=c.execute("select logical_path,archive_path from resolved_assets where logical_path like '%stamp%' and logical_path like '%town%center%'").fetchall()
 print('STAMP_CANDIDATES',rows)
 (OUT/'stamp-candidates.json').write_text(json.dumps(rows,indent=2))
 models=c.execute("select logical_path,archive_path from resolved_assets where logical_path like '%abb_towncenter%' and extension='.rgm'").fetchall();c.close()
 (OUT/'model-candidates.json').write_text(json.dumps(models,indent=2))
 available={x[0] for x in models};assembly=[];donors=[]
 for age in range(1,5):
  member=f'art/stamps/civ_abbasid/abb_town_center_age_{age:02}.bin';target=OUT/'stock-stamps'/member;target.parent.mkdir(parents=True,exist_ok=True)
  run(f'extract-stamp-age{age}',[ARCH,'extract-member','E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Data.sga',member,target])
  t=NativeTree(target);components=[]
  for obj in t.objects.values():
   if obj['type']!='VisualStampBlueprint':continue
   path=t.field(obj,obj['fields']['m_blueprint'])['text'].replace('\\','/');components.append({'object':obj['id'],'model':path,'fields':t.describe(obj)['fields']})
   if path+'.rgm' in available:donors.append((age,path+'.rgm'))
  assembly.append({'age':age,'stamp':member,'source_file':str(target),'components':components,'objects':[t.describe(o) for o in t.objects.values()]})
 (OUT/'native-assemblies.json').write_text(json.dumps(assembly,indent=2));print('USED_COMPONENTS',[(a['age'],[c['model'] for c in a['components']]) for a in assembly])
 recipes=[]
 for age,path in dict.fromkeys(donors):
  name=Path(path).stem;run('decode-'+name,[CORE,'convert','decode-static','--logical-path',path,'--config',CONFIG,'--index',INDEX,'--output-root',OUT/'stock'])
  decoded=next(p for p in (OUT/'stock').glob('*/decoded-static.json') if json.loads(p.read_text())['request']['logical_path']==path)
  recipes.append({'age':age,'name':name,'source':path,'decode':str(decoded)})
 (ART/'donors.json').write_text(json.dumps(recipes,indent=2));print('DECODED_DONORS',len(recipes))
if __name__=='__main__':main()
