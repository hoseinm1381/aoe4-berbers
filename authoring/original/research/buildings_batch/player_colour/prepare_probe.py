from pathlib import Path
import shutil,xml.etree.ElementTree as ET,json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'output/buildings_batch/player_colour'
PROBE=OUT/'unit_shader_probe'
assert not PROBE.exists()
original=ROOT/'art/tribal_tent/garrison_library_0_2_1/Mods/berber_tent_art_020/project'
PROBE.mkdir()
shutil.copy2(original/'berber_tent_art_020.aoe4mod',PROBE/'owner_probe.aoe4mod')
source=PROBE/'source';source.mkdir()
shutil.copy2(original/'source/_default.burnproj',source/'_default.burnproj')
rel=Path('art/scenario/garrison/berber_tent_art_020/buildings/berber_tent_age1')
shutil.copytree(original/'source'/rel,source/rel)
pattern=ROOT/'art/tribal_tent/game_export_0_2_0_v3/age1/maps/pattern.png'
assert (ROOT/'art/tribal_tent/game_export_0_2_0_v3/age1/maps/albedo.png').read_bytes()==(source/rel/'albedo.png').read_bytes()
shutil.copy2(pattern,source/rel/'pattern.png')
xml=ET.parse(source/rel/'model.material');mat=xml.getroot().find('material');mat.set('source','unit')
ET.SubElement(mat,'param',{'name':'patternTex','type':'tex2D','value':str(rel/'pattern.png').replace('/','\\')})
xml.write(source/rel/'model.material',encoding='utf-8',xml_declaration=True)
img=Image.open(pattern).convert('RGB');r,g,b=img.split()
report={'status':'prepared_experimental_not_native_accepted','geometry':'byte-identical 0.2.1 age1 construction FBX','material':'unit shader + patternTex','pattern':str(pattern),'pattern_size':img.size,'red_range':r.getextrema(),'green_range':g.getextrema(),'blue_range':b.getextrema(),'red_nonzero_pixels':sum(n for v,n in enumerate(r.histogram()) if v),'fbx_sha256':hashlib.sha256((source/rel/'model.fbx').read_bytes()).hexdigest()}
(OUT/'probe-inputs.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
