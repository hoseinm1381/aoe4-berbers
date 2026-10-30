"""Recook only this project's nine UI surfaces using a fresh native carrier.

Run with Python 3.13 after render_presentation.mjs. Never promotes carrier
gameplay, metadata or locale. Existing work folders are protected diagnostics.
"""
import argparse,hashlib,shutil,subprocess,time
from pathlib import Path
from runtime import ROOT,EXT,stock_game,read_json,write_json
from garrison_shared import rrtex_decoder as rr
def run(cmd,log):
 with log.open('w',encoding='utf-8') as stream:r=subprocess.run([str(x) for x in cmd],stdout=stream,stderr=subprocess.STDOUT)
 if r.returncode:raise RuntimeError('Native tool failed; inspect '+str(log))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,default=ROOT/'output/presentation-current');p.add_argument('--replace-current',action='store_true');p.add_argument('--editor',type=Path,default=Path('E:/Games/steamapps/common/Age of Empires IV/EssenceEditor.exe'));a=p.parse_args()
 work=a.work.resolve()
 if not work.is_relative_to(ROOT.resolve()) or not a.editor.is_file():raise ValueError('Work must stay inside this project; editor must exist')
 cfg=read_json(ROOT/'project.json');core=EXT/'bin/core/garrison-core.exe'
 if work.exists():
  if not a.replace_current or work!=ROOT/'output/presentation-current':raise ValueError('Existing diagnostics protected; --replace-current reuses only verified output/presentation-current')
  receipt=read_json(work/'verification.json')
  if receipt.get('owner')!=cfg['owner'] or not receipt.get('only_ui_promoted'):raise ValueError('Unverified/foreign UI work is protected')
  for member,row in receipt['members'].items():
   raw=(ROOT/'inputs/native'/member).read_bytes()
   if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Promoted UI changed; preserve its previous work')
  for item in work.rglob('*'):
   if item.is_symlink() or item.is_junction() or not item.resolve().is_relative_to(work):raise ValueError('Linked UI work is protected')
  write_json(ROOT/'docs/PRESENTATION_PREVIOUS_COOK.json',receipt)
  # Files first also works on the project's exFAT storage.
  for item in work.rglob('*'):
   if item.is_file():item.unlink()
  for item in sorted(work.rglob('*'),key=lambda q:len(q.parts),reverse=True):
   if item.is_dir():item.rmdir()
 else:work.mkdir(parents=True)
 profile=ROOT/'source/authoring-profile.json'
 if not profile.exists():profile=ROOT/'source/native-ui-profile.json'
 run([core,'civilization-authoring',profile,'--library',work/'library'],work/'authoring.log')
 carrier=work/'library/Mods'/cfg['race'];surfaces=read_json(ROOT/'source/presentation/presentation-011.json')['surfaces']
 for row in surfaces:
  source=ROOT/'source/presentation/derived_011'/(row['name']+'.png');dest=carrier/'project/source/ui/images/garrison'/cfg['race']/'presentation_011'/source.name
  dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
 started=time.time();run([core,'mod-project','cook','--project',carrier,'--editor',a.editor,'--timeout','900'],work/'cook.log')
 archive=carrier/'dist'/(cfg['race']+'.sga')
 if archive.stat().st_mtime<started:raise ValueError('Cook did not produce a fresh archive')
 game=stock_game.current();listing=game.archiver.run(['list',str(archive),'--verify'])
 if not listing['archive']['verification']['verified']:raise ValueError('Carrier archive verification failed')
 staged=[]
 for row in surfaces:
  member='ui/images/garrison/'+cfg['race']+'/presentation_011/'+row['name']+'.rrtex';raw=game.archiver.read(archive,member);dest=work/'verified'/member;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
  doc=rr.load(dest);mips=[]
  for chunk in doc.walk():
   if chunk.tag==b'TDAT':mips+=rr._decode_mips(chunk.payload)[1]
  if len(mips)!=1 or (mips[0].width,mips[0].height)!=(row['width'],row['height']):raise ValueError('Cooked dimensions differ: '+member)
  staged.append((member,dest,{'toc':'data','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'origin':'Native 0.1.1 UI recook'}))
 manifest=read_json(ROOT/'inputs/native-manifest.json')
 for member,src,row in staged:
  dest=ROOT/'inputs/native'/member;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest);manifest[member]=row
 write_json(ROOT/'inputs/native-manifest.json',manifest);write_json(work/'verification.json',{'version':cfg['version'],'owner':cfg['owner'],'only_ui_promoted':True,'members':{m:r for m,_,r in staged}})
 print('VERIFIED_NATIVE_UI',len(staged))
if __name__=='__main__':main()
