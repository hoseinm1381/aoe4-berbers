"""Temporary archive-local Garrison decode index; never edits official catalogue."""
import sqlite3,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_2_7/qualification'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';CORE=EXT/'bin/core/garrison-core.exe';ARCH=EXT/'bin/sga-archiver.exe'
def decode_archive(archive,models,index_path,output):
 db=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
 schema=db.execute("select sql from sqlite_master where name='resolved_assets'").fetchone()[0]
 template=list(db.execute("select * from resolved_assets where logical_path='art/civilizations/common/flags/flag_rectangle/flag_rectangle.rgo'").fetchone())
 db.close()
 index_path=Path(index_path);index_path.parent.mkdir(parents=True,exist_ok=True)
 idx=sqlite3.connect(index_path);idx.execute(schema.replace('CREATE TABLE resolved_assets','CREATE TABLE IF NOT EXISTS resolved_assets'));idx.execute('delete from resolved_assets')
 inv=json.loads(subprocess.run([str(ARCH),'list',str(archive),'--verify'],capture_output=True,text=True,check=True).stdout)
 for n,r in enumerate(inv['members']):
  row=template.copy();p=Path(r['path']);row[0]=n;row[1]=p.as_posix();row[2]=p.parent.as_posix();row[3]=p.stem;row[4]=p.suffix;row[10]=r.get('size',0);row[11]=p.as_posix();row[15]=Path(archive).name;row[16]=str(Path(archive).resolve());row[17]='qualification';row[20]=1;row[21]=1
  idx.execute('insert into resolved_assets values ('+','.join('?' for _ in row)+')',row)
 idx.commit();idx.close()
 reports=[]
 for model in models:
  p=subprocess.run([str(CORE),'convert','decode-static','--logical-path',model,'--config','C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.local.json','--index',str(index_path),'--output-root',str(output)],capture_output=True,text=True,timeout=120)
  reports.append({'model':model,'returncode':p.returncode,'stdout':p.stdout[-3000:],'stderr':p.stderr[-3000:]})
 return reports
if __name__=='__main__':
 cook=json.loads((OUT/'independent-lod-cook.json').read_text())
 report=decode_archive(cook['archive'],[f'art/scenario/garrison/lf027/buildings/fixture_lod{lod}/model.rgm' for lod in range(3)],OUT/'custom-index.sqlite3',OUT/'own-decoded')
 (OUT/'own-decode-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
