from pathlib import Path
R=Path.cwd();Q=R/'research/buildings_batch/palisade_bastion'
s=(R/'art/buildings/palisade_bastion/build_palisade_bastion.py').read_text()
s=s.replace('\n donor()\n','\n # donor reference retained\n').replace(' for age in range(1,5):build(age)',' for age in [3,4]:build(age)')
(Q/'repair_render.py').write_text(s)
s=(Q/'run_hidden.py').read_text().replace("ROOT/'art/buildings/palisade_bastion/build_palisade_bastion.py'","ROOT/'research/buildings_batch/palisade_bastion/repair_render.py'").replace("'blender.log'","'repair_render.log'")
(Q/'run_repair.py').write_text(s)
