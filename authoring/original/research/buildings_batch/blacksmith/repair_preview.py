from pathlib import Path
R=Path.cwd();Q=R/'research/buildings_batch/blacksmith';A=R/'art/buildings/blacksmith'
s=(A/'build_blacksmith.py').read_text();s=s.replace("(-2.1,-1.05,.54)","(-2.1,-3.42,.54)").replace("],-1.23,-.87,'shadow'", "],-3.60,-3.24,'shadow'")
s=s.replace("'front_access_corridor_m':1.7", "'front_access_corridor_m':1.3")
s=s.replace("    for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:reuv(o)","""    # Extra grounded tools sit on the exposed anvil so the role reads at game camera scale.
    box('anvil_hammer_handle',(-2.20,-3.42,1.275),(.44,.045,.05),'cedar',100)
    box('anvil_hammer_head',(-2.4,-3.42,1.325),(.12,.13,.10),'shadow',100)
    for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:reuv(o)""")
(A/'build_blacksmith.py').write_text(s)
# Persist repair in generator too, recipes remain reproducible.
g=(Q/'create_recipe.py').read_text().replace("(-2.1,-1.05,.54)","(-2.1,-3.42,.54)").replace("],-1.23,-.87,'shadow'", "],-3.60,-3.24,'shadow'")
g=g.replace("'front_access_corridor_m':1.7", "'front_access_corridor_m':1.3")
g=g.replace("    for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:reuv(o)","""    box('anvil_hammer_handle',(-2.20,-3.42,1.275),(.44,.045,.05),'cedar',100)
    box('anvil_hammer_head',(-2.4,-3.42,1.325),(.12,.13,.10),'shadow',100)
    for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:reuv(o)""")
(Q/'create_recipe.py').write_text(g)
