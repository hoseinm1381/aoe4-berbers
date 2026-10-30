"""Fresh native name-only Ribat recook; controlled probe on verified0.2.7."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'research'))
import build_berber_update_0_2_7 as builder
import landmark_027_export_actual as actual
OUT=ROOT/'output/berber_update_0_2_7_1';ART=ROOT/'art/landmarks_0_2_7_1';INT=OUT/'integration'
builder.OUT=OUT;builder.INT=INT;builder.ART=ART;builder.BASE=ROOT/'output/berber_update_0_2_7/package/Berber_future_kingdom.sga';builder.BASE_SHA='bbc965d9797c37e79aa95626bca1a83eb17874945671d9bd0b8ca463076c3b91';builder.SPECS={'ribat':builder.SPECS['ribat']}
actual.INT=INT;actual.ART=ART
if __name__=='__main__':
 action=sys.argv[1]
 if action=='prepare':builder.prepare()
 elif action=='cook':builder.cook_family('ribat')
 elif action=='assemble':actual.assemble_actual('ribat')
 elif action=='finish':actual.finish_actual('ribat')
 else:raise ValueError(action)
