from pathlib import Path
q=Path('art/buildings/wall_tower'); src=Path('art/buildings/house/build_house.py').read_text(); head=src[:src.index('def build(age):')];head=head.replace('/buildings/house','/buildings/wall_tower').replace('/buildings_batch/house','/buildings_batch/wall_tower').replace('House','WallTower').replace("('straw',(.52,.40,.22),0)","('metal',(.19,.20,.18),0)");head=head.replace("((co[axes[0]]*.3)%1)","((co[axes[0]]*.3)%1)")
(q/'build_wall_tower.py').write_text(head)
