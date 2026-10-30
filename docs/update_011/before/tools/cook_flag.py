"""Recreate the original-banner native UI image through supported authoring."""
import argparse
import shutil
import subprocess
from pathlib import Path
from runtime import ROOT, EXT, read_json, stock_game


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--editor',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert not out.exists(),out
    config=read_json(ROOT/'project.json')
    # The maintained profile is derived from the supported authoring contract.
    profile=read_json(ROOT/'source/native-ui-profile.json')
    out.mkdir(parents=True)
    profile_path=out/'profile.json';profile_path.write_text(__import__('json').dumps(profile,indent=2))
    core=EXT/'bin/core/garrison-core.exe'
    for cmd in [[core,'civilization-authoring',profile_path,'--library',out/'library']]:
        subprocess.run([str(x) for x in cmd],check=True,stdout=(out/'authoring.log').open('w'),stderr=subprocess.STDOUT)
    project=out/'library/Mods/berbers'
    member='ui/images/garrison/berbers/presentation/flag_original.rrtex'
    target=project/'project/source'/Path(member).with_suffix('.png')
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/'source/presentation/berbers.png',target)
    subprocess.run([str(core),'mod-project','cook','--project',str(project),'--editor',str(a.editor)],check=True,stdout=(out/'cook.log').open('w'),stderr=subprocess.STDOUT)
    raw=stock_game.current().archiver.read(project/'dist/berbers.sga',member)
    target=out/'flag_original.rrtex';target.write_bytes(raw)
    print('COOKED',target,flush=True)
