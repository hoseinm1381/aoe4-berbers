from pathlib import Path
p=Path('art/buildings/tc/build_tc.py');s=p.read_text();needle="    col=bpy.data.collections.new('BER_TC_Age'+str(age));bpy.context.scene.collection.children.link(col)"
patch="""    # Inherited installed core site_ext is 8x8. Scale authored plan into that exact envelope.
    for o in objects:
        o.location.x*=8/9.6;o.location.y*=8/8.8
        for v in o.data.vertices:v.co.x*=8/9.6;v.co.y*=8/8.8
"""
s=s.replace(needle,patch+needle).replace("'footprint_m':[9.6,8.8]","'footprint_m':[8,8]").replace("'clear_entry_width_m':1.80","'clear_entry_width_m':1.50").replace("(0,-4.4,0)","(0,-4.0,0)")
s=s.replace("cam.data.ortho_scale=15.6","cam.data.ortho_scale=13.6")
p.write_text(s)
