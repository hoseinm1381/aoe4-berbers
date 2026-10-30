"""Recreate SCAR-only native cook inputs; no art-probe dependency."""
from pathlib import Path
import shutil,sys
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_2_7_1';name=sys.argv[1] if len(sys.argv)>1 else 'precache-source';assert name in ['precache-source','precache-stage-rebuild-test'];stage=OUT/name;source=stage/'source'
assert not stage.exists(),'Use a fresh stage after inspecting any existing run.'
source.mkdir(parents=True)
shutil.copy2(OUT/'rebuild_inputs/landmark_precache.aoe4mod',stage/'landmark_precache.aoe4mod');shutil.copy2(OUT/'rebuild_inputs/_default.burnproj',source/'_default.burnproj')
for member in ['scar/winconditions/berber_future_kingdom_GM.scar','scar/buildings/berber_landmark_visual_precache.scar']:
 p=source/member;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'assets'/member,p)
print('SCAR_ONLY_STAGE_RECREATED',stage)
