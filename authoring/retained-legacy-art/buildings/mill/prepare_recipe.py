from pathlib import Path
p=Path(__file__).parent
root=p.parents[2]
s=(root/'art/buildings/house/build_house.py').read_text()
helper=s[:s.index('def build(age):')].replace('art/buildings/house','art/buildings/mill').replace('output/buildings_batch/house','output/buildings_batch/mill').replace('research/buildings_batch/house','research/buildings_batch/mill').replace('House','Mill').replace('house','mill')
(p/'geometry_helpers.py').write_text(helper)
