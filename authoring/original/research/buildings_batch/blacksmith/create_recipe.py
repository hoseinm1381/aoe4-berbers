from pathlib import Path
R=Path.cwd();A=R/'art/buildings/blacksmith';Q=R/'research/buildings_batch/blacksmith'
s=(R/'art/buildings/market/build_market.py').read_text();p=s[:s.index('def build(age):')].replace('market','blacksmith').replace('Market','Blacksmith')
p=p.replace("('stone',(.37,.31,.23),0)","('stone',(.37,.31,.23),0)")
# shadow is iron tile, serves cold metal tools and anvil
p=p.replace("('shadow',(.065,.04,.022),0)","('shadow',(.10,.115,.125),0)")
a=p.index('    for p in o.data.polygons:');b=p.index('    bm=bmesh.new()',a)
p=p[:a]+'''    for face in o.data.polygons:
        axis=max(range(3),key=lambda k:abs(face.normal[k]));axes=[k for k in range(3) if k!=axis]
        co=[o.data.vertices[o.data.loops[li].vertex_index].co for li in face.loop_indices]
        lo=[min(v[k] for v in co) for k in axes];hi=[max(v[k] for v in co) for k in axes]
        for li,v in zip(face.loop_indices,co):
            uv.data[li].uv=((slot%4+.07+.86*(v[axes[0]]-lo[0])/max(hi[0]-lo[0],1e-8))/4,(slot//4+.07+.86*(v[axes[1]]-lo[1])/max(hi[1]-lo[1],1e-8))/2)
'''+p[b:]
p=p.replace("for mapname in ('albedo','pattern'):","for mapname in ('albedo','pattern','roughness','metal','normal'):")
p=p.replace("rgb=(owner,0,0) if mapname=='pattern' else tuple(v*variation for v in c)","rgb={'pattern':(owner,0,0),'normal':(.5,.5,1),'metal':((.85,.85,.85) if slot==5 else (0,0,0)),'roughness':((.4,.4,.4) if slot==5 else (.85,.85,.85))}.get(mapname,tuple(v*variation for v in c))")
body='''
def beam(name,a,b,w,mat='cedar',stage=60):
    v=Vector(b)-Vector(a);o=box(name,(Vector(a)+Vector(b))/2,(w,w,v.length),mat,stage);o.rotation_euler=v.to_track_quat('Z','Y').to_euler();return o

def reuv(o):
    uv=o.data.uv_layers.active;slot=MATS[o['ber_material_role']][1]
    for p in o.data.polygons:
        ax=max(range(3),key=lambda k:abs(p.normal[k]));axes=[k for k in range(3) if k!=ax];vs=[o.data.vertices[o.data.loops[i].vertex_index].co for i in p.loop_indices];lo=[min(v[k] for v in vs) for k in axes];hi=[max(v[k] for v in vs) for k in axes]
        for i,v in zip(p.loop_indices,vs):uv.data[i].uv=((slot%4+.07+.86*(v[axes[0]]-lo[0])/max(hi[0]-lo[0],1e-8))/4,(slot//4+.07+.86*(v[axes[1]]-lo[1])/max(hi[1]-lo[1],1e-8))/2)

def build(age):
    global PARTS,CONTACTS
    ctx=reset_scene();PARTS=[];CONTACTS=[];MATS.clear();setup_maps();wall='earth' if age==2 else 'lime';h=2.1+.25*(age-2)
    box('foundation',(0,0,.08),(8,8,.16),'stone',0);box('court_floor',(0,0,.175),(7.8,7.8,.03),'earth',0)
    # Hollow east workshop with a physically open doorway, separate store walls and roof.
    box('store_back',(1.95,3.18,.19+h/2),(3.5,.24,h),wall,40)
    for x in [.32,3.58]:box('store_side',(x,2.10,.19+h/2),(.24,1.92,h),wall,40)
    for x,w in [(.775,1.15),(3.00,1.40)]:box('store_front_jamb',(x,1.02,.19+.8),(w,.24,1.6),wall,40)
    box('store_open_lintel',(1.95,1.02,.19+1.6+(h-1.6)/2),(3.5,.24,h-1.6),wall,40)
    box('store_roof',(1.95,2.10,.19+h+.06),(3.74,2.40,.12),'earth',60);contact('store_roof','store_back')
    for yy in [.96,3.24]:box('store_parapet',(1.95,yy,.19+h+.30),(3.74,.12,.36),wall,80)
    for xx in [.14,3.76]:box('store_end_parapet',(xx,2.10,.19+h+.30),(.12,2.16,.36),wall,80)
    # Open forge mouth, hearth sides and back, hood with shaft void, chimney four shell walls.
    fx=-2.3;fy=1.35
    box('hearth_base',(fx,fy,.19+.27),(1.8,1.5,.54),'stone',40);contact('hearth_base','court_floor')
    for xx in [fx-.78,fx+.78]:box('forge_side',(xx,fy,1.26),(.24,1.5,1.06),wall,40)
    box('forge_back',(fx,fy+.63,1.26),(1.32,.24,1.06),wall,40)
    # hollow hood: four perimeter beams form real opening into square flue
    for xx in [fx-.68,fx+.68]:box('hood_side',(xx,fy,1.88),(.44,1.5,.18),'stone',60)
    for yy in [fy-.59,fy+.59]:box('hood_front_back',(fx,yy,1.88),(.92,.32,.18),'stone',60)
    ch=1.30+.35*(age-2);base=1.97
    for xx in [fx-.38,fx+.38]:box('chimney_side',(xx,fy,base+ch/2),(.16,.86,ch),wall,60)
    for yy in [fy-.35,fy+.35]:box('chimney_front_back',(fx,yy,base+ch/2),(.60,.16,ch),wall,60)
    # ring coping remains genuinely open; six side inspection exposes the flue
    for xx in [fx-.41,fx+.41]:box('chimney_coping',(xx,fy,base+ch+.05),(.20,1.00,.10),'stone',80)
    for yy in [fy-.40,fy+.40]:box('chimney_coping_cross',(fx,yy,base+ch+.05),(.62,.20,.10),'stone',80)
    for j in range(7):tube('cold_charcoal',(fx-.5+j*.15,fy-.15,.77),.075,.08,'shadow')
    # Bellows support stand and leather wedge; nozzle physically seats against forge side.
    box('bellows_stand',(-.92,fy,.64),(.70,.65,.90),'cedar',40);contact('bellows_stand','court_floor')
    prism('bellows_leather',[(-1.53,1.02),(-.38,.98),(-.38,1.36),(-1.53,1.16)],fy-.29,fy+.29,'clay',80)
    beam('bellows_handle',(-.38,fy,1.33),(-.12,fy,1.50),.06)
    box('bellows_nozzle',(-1.62,fy,1.08),(.20,.14,.14),'shadow',80)
    # Timber forge shelter with slopes seated on actual eaves; chimney outside rear roof edge.
    eave=2.15+.15*(age-2);ridge=eave+.42
    for xx in [-3.53,-.72]:
        for yy in [-2.9,.35]:box('shelter_post',(xx,yy,.19+(eave-.19)/2),(.14,.14,eave-.19),'cedar',20)
    for yy in [-2.9,.35]:box('shelter_crossbeam',(-2.125,yy,eave),(3.09,.16,.16),'cedar',60)
    for yy in [-2.9,.35]:
        for xx in [-3.53,-.72]:beam('roof_rafter',(xx,yy,eave+.08),(-2.125,yy,ridge),.11)
    for side in [-1,1]:prism('pitched_roof',[(-2.125,ridge+.10),(-2.125+side*1.65,eave+.02),(-2.125+side*1.65,eave-.05),(-2.125,ridge+.03)],-3.07,.47,'cedar',80)
    for xx in [-3.0,-2.12,-1.24]:box('owner_roof_stripe',(xx,-3.082,eave-.05),(.38,.026,.25),'owner_cloth',100)
    # Anvil integral silhouette with horn on a seated stump.
    tube('anvil_stump',(-2.1,-3.42,.54),.32,.70,'cedar',60);contact('anvil_stump','court_floor')
    prism('anvil',[(-2.65,.89),(-1.60,.89),(-1.82,1.01),(-1.78,1.12),(-1.45,1.14),(-1.26,1.25),(-2.62,1.25),(-2.52,1.05)],-3.60,-3.24,'shadow',80);contact('anvil','anvil_stump')
    # Actual open quenching trough assembled as floor plus four rim walls.
    tx=1.7;ty=-1.55
    box('trough_bottom',(tx,ty,.245),(1.35,1.9,.11),'stone',40);contact('trough_bottom','court_floor')
    for xx in [tx-.60,tx+.60]:box('trough_side',(xx,ty,.52),(.15,1.9,.44),'stone',80)
    for yy in [ty-.875,ty+.875]:box('trough_end',(tx,yy,.52),(1.05,.15,.44),'stone',80)
    box('quench_water',(tx,ty,.40),(1.05,1.60,.04),'shadow',100)
    # Tool bench/rack and stocked workshop; every bench foot grounded.
    for xx in [.58,3.12]:box('bench_leg',(xx,2.6,.595),(.12,.62,.81),'cedar',60)
    box('bench_top',(1.85,2.6,1.04),(2.84,.76,.08),'cedar',80);contact('bench_top','bench_leg')
    box('tool_rack',(1.85,3.04,1.58),(2.80,.10,.12),'cedar',80)
    for xx in [.65,1.2,1.75,2.3,2.85]:
        box('hammer_handle',(xx,2.96,1.36),(.045,.045,.47),'cedar',100);box('hammer_head',(xx,2.96,1.59),(.24,.10,.10),'shadow',100)
    for xx in [.8,1.3,1.8,2.3,2.8]:box('steel_billet',(xx,2.6,1.125),(.32,.12,.09),'shadow',100)
    box('owner_workshop_band',(1.95,.882,1.98),(2.9,.026,.18),'owner_cloth',100)
    if age>=3:
        for xx in [.38,3.52]:
            for zz in [.36,.70,1.04,1.38,1.72]:box('workshop_quoin',(xx,.882,zz),(.22,.035,.17),'stone',80)
        for xx in [.63,3.28]:box('roof_drain',(xx,3.44,.19+h+.1),(.13,.45,.09),'cedar',80)
        for i in range(4):box('charcoal_sack',(3.3,.1+i*.32,.40),(.46,.26,.42),'straw',100)
    if age==4:
        for xx in [.70,1.15,2.70,3.15]:
            o=box('geometric_inlay',(xx,.858,2.24),(.12,.025,.12),'earth',100);o.rotation_euler.y=math.pi/4
        for xx in [-3.55,-.75]:box('forge_masonry_post_base',(xx,-2.9,.36),(.30,.30,.34),'stone',40)
        box('workshop_roof_monitor',(2.75,2.30,.19+h+.39),(1.15,.94,.66),wall,80)
        box('monitor_cap',(2.75,2.30,.19+h+.77),(1.27,1.06,.10),'lime',80);contact('monitor_cap','workshop_roof_monitor')
        for xx in [2.4,2.75,3.1]:box('monitor_vent',(xx,1.819,.19+h+.40),(.15,.024,.26),'cedar',100)
    # Source markers only. Preserve inherited native placements during later integration.
    for name,loc in [('entry',(0,-4,0)),('forge_work',(-2.1,-1.8,.19)),('workshop_entry',(1.95,.88,.19))]:
        o=bpy.data.objects.new('AUTHOR_'+name,None);bpy.context.scene.collection.objects.link(o);o.location=loc;o['native_binding']='pending'
    box('anvil_hammer_handle',(-2.20,-3.42,1.275),(.44,.045,.05),'cedar',100)
    box('anvil_hammer_head',(-2.4,-3.42,1.325),(.12,.13,.10),'shadow',100)
    for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:reuv(o)
'''
t=s[s.index('    bpy.context.view_layer.update();objects='):].replace('market','blacksmith').replace('Market','Blacksmith').replace('MARKET','BLACKSMITH')
t=t.replace("'clear_gateway_m':1.8,'central_transit_corridor_m':1.8", "'store_clear_door_width_m':.95,'front_access_corridor_m':1.3,'flue_clear_m':[.60,.54],'forge_mouth_clear_m':[1.32,1.06]")
t=t.replace("Abbasid Age II blacksmith", "Abbasid Age II blacksmith")
t=t.replace("bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Blacksmith_Age{age}.blend'))", "bpy.ops.object.light_add(type='AREA',location=(0,-5,3));bpy.context.object.data.energy=500;bpy.context.object.data.size=4\n    bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Blacksmith_Age{age}.blend'))")
(A/'build_blacksmith.py').write_text(p+body+t)
# copy task-local launcher
run=(R/'research/buildings_batch/siege/run_hidden.py').read_text().replace('siege','blacksmith');(Q/'run_hidden.py').write_text(run)
