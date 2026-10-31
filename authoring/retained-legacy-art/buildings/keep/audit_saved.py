import bpy,bmesh,math,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3];A=ROOT/'art/buildings/keep';O=ROOT/'output/buildings_batch/keep'
def bb(o):
    p=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(v[k] for v in p) for k in range(3)],[max(v[k] for v in p) for k in range(3)]]
def ray(o,origin,direction):
    inv=o.matrix_world.inverted();return o.ray_cast(inv@Vector(origin),inv.to_3x3()@Vector(direction))[0]
try:
    audits=[]
    for age in [3,4]:
        bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Keep_Age{age}.blend'))
        with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
            ob=list(bpy.context.scene.objects);walls=[x for x in ob if x.name.startswith('curtain_wall') or x.name in ['front_gate_wall','rear_wall']];walks=[x for x in ob if x.name.startswith('rampart_walk')];roofs=[x for x in ob if x.name.startswith('tower_roof')];towers=[x for x in ob if x.name.startswith('battered_square_tower')]
            gaps=[min(abs(bb(w)[0][2]-bb(p)[1][2]) for p in walls) for w in walks]
            roofgaps=[abs(bb(r)[1][2]-bb(walks[0])[1][2]) for r in roofs]
            clear_min=[-.75,-1.75,.23];clear_max=[.75,.25,1.80];court_blockers=[]
            for x in ob:
                if x.type!='MESH' or x.name.startswith(('arrow_','springald_','cannon_','oil_')):continue
                b=bb(x)
                if all(b[1][k]>clear_min[k]+1e-5 and b[0][k]<clear_max[k]-1e-5 for k in range(3)):court_blockers.append(x.name)
            join_overlaps=[1.8-(abs((bb(t)[0][0]+bb(t)[1][0])/2)-.86) for t in towers]
            gate=bpy.data.objects['front_gate_wall'];gate_void=not ray(gate,(0,-5,1.2),(0,1,0));solid_jamb=ray(gate,(1.4,-5,1.2),(0,1,0))
            slits=[not ray(t,(t.location.x if False else (bb(t)[0][0]+bb(t)[1][0])/2,-8,2.72),(0,1,0)) for t in towers]
            # Object-space world coordinates retained in custom battered mesh, not origin guess.
            packed={i.name:bool(i.packed_file) for i in bpy.data.images if i.name.startswith('Keep_')};actions=[]
            access=[];geometry=[]
            for x in ob:
                if x.type!='MESH':continue
                bm=bmesh.new();bm.from_mesh(x.data);nm=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-10 for f in bm.faces);volume=bm.calc_volume(signed=True);bm.free();geometry.append({'object':x.name,'nonmanifold':nm,'degenerates':deg,'signed_volume':volume,'uv_present':bool(x.data.uv_layers),'finite':all(math.isfinite(v) for p in x.data.vertices for v in p.co)})
                if x.name.startswith('tower_parapet'):
                    ax=0 if abs(abs(x.location.x)-1.87)<.01 else 1 if abs(abs(x.location.y)-1.87)<.01 else None
                    if ax is not None:
                        start=list(x.location);start[ax]-=2;direction=[0,0,0];direction[ax]=1;access.append(not ray(x,start,direction))
            manifest=json.loads((A/f'age{age}_construction.json').read_text());names={p['object'] for p in manifest['parts']};actual={x.name for x in ob if x.type=='MESH'}
            for x in ob:
                if x.name.startswith('gate_leaf_closed'):actions.append({'name':x.name,'hinge_x':x.location.x,'action':x.animation_data.action.name if x.animation_data and x.animation_data.action else None})
            d={'age':age,'geometry':geometry,'manifest_names_match':names==actual,'parapet_access_void_raycasts':access,'wall_to_walk_measured_gaps':gaps,'tower_roof_walk_measured_top_gaps':roofgaps,'wall_tower_top_plan_overlap':join_overlaps,'courtyard_clear_box':[clear_min,clear_max],'courtyard_clear_blockers':court_blockers,'gate_void_raycast':gate_void,'gate_jamb_raycast':solid_jamb,'slit_void_raycasts':slits,'packed_images':packed,'gate_actions':actions}
            assert names==actual and len(access)==8 and all(access) and all(not g['nonmanifold'] and not g['degenerates'] and g['signed_volume']>0 and g['finite'] and g['uv_present'] for g in geometry) and not court_blockers and min(join_overlaps)>0 and max(gaps)<1e-5 and max(roofgaps)<1e-5 and gate_void and solid_jamb and all(slits) and len(packed)>=5 and all(packed.values()) and all(x['action'] for x in actions),d
            audits.append(d)
    (O/'saved_source_audit.json').write_text(json.dumps({'passed':True,'ages':audits},indent=2))
except Exception:(O/'AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
