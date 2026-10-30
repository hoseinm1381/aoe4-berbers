"""Historical 0.7.3 two-package functions; CLI now delegates to unified 0.8.1.

Check: python -B research/next_release.py --check
Build: python -B research/next_release.py --version 0.8.0 --summary "Changes" --sga <validated.sga>
The functions below remain for historical fixtures. Normal command-line use now
calls package_unified_release.py and does not require retired 0.7.3 deliveries.
This packages an already validated SGA; it does not cook Blender/source changes.
"""
import argparse,hashlib,json,re,zipfile
from pathlib import Path
ROOT=Path(__file__).absolute().parents[1]
SOURCE=ROOT/'output/berber_update_0_7_3'
SGA=ROOT/'output/berber_update_0_6_1/Berber_future_kingdom.sga'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check():
 report=json.loads((SOURCE/'release-validation.json').read_text(encoding='utf-8-sig'))
 for item in report['packages'].values():
  path=SOURCE/Path(item['zip']).name
  if sha(path)!=item['sha256']:raise ValueError('Retained 0.7.3 ZIP changed')
  with zipfile.ZipFile(path) as z:
   if set(z.namelist())!=set(item['members']):raise ValueError('Unexpected member set')
   for name,digest in item['members'].items():
    with z.open(name) as stream:
     if hashlib.file_digest(stream,'sha256').hexdigest()!=digest:raise ValueError('Member changed: '+name)
 if sha(SGA)!='48f09ed61020740932b0a653e165710fda49d25aa7739d05f6486b79dbe661bb':raise ValueError('Canonical current SGA changed')
 return {'status':'passed','retained_packages':2,'base_sga_sha256':sha(SGA),'dependencies':'0.7.3 ZIP pair and 0.6.1 SGA; no older release ZIPs','scope':'Package/rebuild input check only, not gameplay acceptance'}
def build(version,summary,sga,output=None):
 if not re.fullmatch(r'\d+\.\d+\.\d+',version) or version=='0.7.3':raise ValueError('Use a new three-part version')
 if not summary.strip() or len(summary)>180:raise ValueError('Summary must be 1-180 characters')
 check();sga=Path(sga).absolute()
 if sga.suffix.lower()!='.sga' or not sga.is_file():raise ValueError('Validated SGA required')
 archive_hash=sha(sga);out=Path(output) if output else ROOT/'output'/('berber_update_'+version.replace('.','_'))
 destinations=[out/('Berber-'+version+'-'+k+'.zip') for k in ('MAIN-GARRISON','VOICES-INSTALLER')]
 if any(p.exists() for p in destinations):raise FileExistsError('Existing delivery preserved')
 out.mkdir(parents=True,exist_ok=True);reports=[]
 for kind,target in zip(('MAIN-GARRISON','VOICES-INSTALLER'),destinations):
  expected={}
  with zipfile.ZipFile(SOURCE/('Berber-0.7.3-'+kind+'.zip')) as old,zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
   for item in old.infolist():
    name=item.filename
    if name=='Berber_future_kingdom.sga':z.write(sga,name);expected[name]=archive_hash;continue
    data=old.read(item)
    if name=='garrison.json':
     m=json.loads(data);m['details'].update(version=version,summary=summary,description=summary+' Install the separate native voice package; import the main ZIP in Garrison.',changelog=summary)
     for member in m['members']:
      if member['path']=='Berber_future_kingdom.sga':member['sha256']=archive_hash
     data=(json.dumps(m,indent=2)+'\n').encode()
    elif name in ('Setup-BerberVoices.ps1','START-HERE.txt'):data=data.replace(b'0.7.3',version.encode())
    z.writestr(name,data);expected[name]=hashlib.sha256(data).hexdigest()
  with zipfile.ZipFile(target) as z:
   if set(z.namelist())!=set(expected):raise ValueError('Package member mismatch')
   for name,digest in expected.items():
    with z.open(name) as stream:
     if hashlib.file_digest(stream,'sha256').hexdigest()!=digest:raise ValueError('Package hash mismatch')
  reports.append({'path':str(target),'sha256':sha(target),'bytes':target.stat().st_size,'members':expected})
 result={'status':'package_verified','version':version,'sga_sha256':archive_hash,'packages':reports,'voices':'Unchanged 0.7.3 payloads and ownership states','audible_gameplay':'pending'}
 (out/'release-validation.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
 from package_unified_release import cli
 cli()
