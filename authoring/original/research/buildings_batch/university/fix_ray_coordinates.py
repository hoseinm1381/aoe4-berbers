from pathlib import Path
p=Path('art/buildings/university/build_university.py');s=p.read_text().replace("origin=Vector((-.8,0,z));direction", "origin=o.matrix_world.inverted()@world;origin.x=-.8;direction").replace("origin=Vector((cx,-4,z));direction", "origin=o.matrix_world.inverted()@Vector((cx,-4,z));direction");p.write_text(s)
