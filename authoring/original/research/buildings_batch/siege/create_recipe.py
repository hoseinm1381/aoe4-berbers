from pathlib import Path
R=Path(__file__).resolve().parents[3]
s=(R/'art/buildings/market/build_market.py').read_text()
p=s[:s.index('def build(age):')].replace('/market','/siege').replace('Market','Siege')
p=p.replace("('straw',(.52,.40,.22),0)]", "('straw',(.52,.40,.22),0),('iron',(.12,.13,.14),0),('unused_a',(.2,.2,.2),0),('unused_b',(.2,.2,.2),0),('unused_c',(.2,.2,.2),0)]")
p=p.replace('height=256','height=384').replace('for y in range(256)','for y in range(384)')
# Flat auxiliary maps are source defaults: metal atlas tile is the stone tile.
p=p.replace("for mapname in ('albedo','pattern'):","for mapname in ('albedo','pattern','roughness','normal','metal'):")
p=p.replace("rgb=(owner,0,0) if mapname=='pattern' else tuple(v*variation for v in c)","rgb={'pattern':(owner,0,0),'roughness':((.45,.45,.45) if slot==8 else (.85,.85,.85)),'normal':(.5,.5,1),'metal':((.8,.8,.8) if slot==8 else (0,0,0))}.get(mapname,tuple(v*variation for v in c))")
# Project each polygon locally with nonzero extents, eliminating wrap-collapsed UV faces.
a=p.index('    for p in o.data.polygons:');b=p.index('    bm=bmesh.new()',a)
p=p[:a]+'''    for face in o.data.polygons:
        axis=max(range(3),key=lambda k:abs(face.normal[k]));axes=[k for k in range(3) if k!=axis]
        co=[o.data.vertices[o.data.loops[li].vertex_index].co for li in face.loop_indices]
        lo=[min(v[k] for v in co) for k in axes];hi=[max(v[k] for v in co) for k in axes]
        for li,v in zip(face.loop_indices,co):
            uv.data[li].uv=((slot%4+.08+.84*(v[axes[0]]-lo[0])/max(hi[0]-lo[0],1e-8))/4,(slot//4+.08+.84*(v[axes[1]]-lo[1])/max(hi[1]-lo[1],1e-8))/3)
'''+p[b:]
body=(Path(__file__).parent/'build_body.txt').read_text()
t=s[s.index('    bpy.context.view_layer.update();objects='):].replace('Market','Siege').replace('MARKET','SIEGE').replace('market','siege')
t=t.replace('>=-4.001','>=-3.001').replace('<=4.001','<=3.001').replace("'footprint_m':[8,8]","'footprint_m':[6,6]").replace("'clear_gateway_m':1.8","'clear_gateway_m':4.54").replace("'central_transit_corridor_m':1.8","'central_transit_corridor_m':2.0").replace('cam.data.ortho_scale=12.2','cam.data.ortho_scale=9.5').replace('scene.cycles.samples=4','scene.cycles.samples=8')
t=t.replace('Abbasid Age II siege','Abbasid Age III siege').replace('Age2_Reference','Age3_Reference').replace('x=8 y=8','x=6 y=6').replace('for age in [2,3,4]','for age in [3,4]').replace("'ages':[2,3,4]","'ages':[3,4]")
t=t.replace('for age in [3,4]:build(age)',"for age in [int(n) for n in os.environ.get('BER_SIEGE_AGES','3,4').split(',')]:build(age)")
p=p.replace('import bpy,bmesh,math,json,traceback','import bpy,bmesh,math,json,traceback,os')
t=t.replace("bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Siege_Age{age}.blend'))", "bpy.ops.object.light_add(type='AREA',location=(0,-5,3));bpy.context.object.data.energy=420;bpy.context.object.data.size=4\n    bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Siege_Age{age}.blend'))")
(R/'art/buildings/siege/build_siege.py').write_text(p+body+t)
