from pathlib import Path
p=Path('art/buildings/tc/build_tc.py');s=p.read_text()
needle="            x,y,z=v.co;v.co=(y,x,z)\n"
patch="""        bm=bmesh.new();bm.from_mesh(cutter.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
        bm.to_mesh(cutter.data);bm.free();cutter.data.update();bpy.context.view_layer.update()
"""
assert needle in s;s=s.replace(needle,needle+patch)
needle2="    assert all(c.get('pass',True) for c in CONTACTS),CONTACTS"
patch2="""    arcade_volume=next(c['positive_volume'] for c in checks if c['object']=='courtyard_arcade_wall')
    uncut_arcade_volume=.32*3.5*(h-.50)*(8/9.6)*(8/8.8)
    assert arcade_volume<uncut_arcade_volume*.80,('arcade openings absent',arcade_volume,uncut_arcade_volume)
"""
s=s.replace(needle2,patch2+needle2);p.write_text(s)
