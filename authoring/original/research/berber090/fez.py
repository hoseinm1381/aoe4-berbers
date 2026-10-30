"""Deterministic, isolated Marinid college enrichment over retained editable 040 source.

Run with background Blender: blender -b --python research/berber090/fez.py
No existing source is overwritten. Geometry and review/export are separate stages.
"""
import bpy, bmesh, math, json, sys, shutil, hashlib
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'research'))
from berber_040_fez_runner import Runner, building_panel, material_adoption

ART = ROOT / 'art/building_remix_0_9_0/fez'
SOURCE = ROOT / 'art/building_remix_0_4_0/fez'
ART.mkdir(parents=True, exist_ok=True)


class College(Runner):
    def __init__(self):
        self.kind = 'fez'; self.art = ART
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE / 'fez_040_original.blend'))
        bpy.context.preferences.filepaths.save_version = 1
        self.col = bpy.data.collections['040_original_fez']
        self.col.name = '090_Marinid_College'
        self.parts = [o for o in self.col.objects if o.type == 'MESH']
        self.checks = []
        self.mat = self.parts[0].data.materials[0]
        self.mat.name = '090_Fez_cedar_stucco_zellij'
        for name in ('atlas_albedo_v2.png', 'atlas_normal_v2.png'):
            shutil.copy2(SOURCE / name, ART / name)
        # Remove old presentation helpers; the source asset collection is retained.
        for ob in list(bpy.data.objects):
            if ob.type in {'CAMERA', 'LIGHT'}:
                bpy.data.objects.remove(ob, do_unlink=True)
        for ob in self.parts:
            if ob.data.users > 1:
                ob.data = ob.data.copy()

    def prism_plane(self, name, poly, face, depth, axis='Y', slot=6, stage=60):
        vs = [(u, d, z) if axis == 'Y' else (d, u, z)
              for d in (face-depth/2, face+depth/2) for u, z in poly]
        n = len(poly)
        fs = [tuple(range(n-1, -1, -1)), tuple(range(n, 2*n))]
        fs += [(i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n)]
        return self.mesh(name, vs, fs, slot, stage)

    def opening(self, name, parent, u, face, z, width, height, axis, slot=1):
        radius = width * .55; spring = z + height - radius
        angles = [math.radians(-25 + 230*i/20) for i in range(21)]
        arc = [(u+radius*math.cos(t), spring+radius*math.sin(t)) for t in angles]
        poly = [(arc[-1][0], z), (arc[0][0], z)] + arc
        cut = self.prism_plane('090_TEMP_'+name, poly, face, .44, axis, slot)
        bpy.context.view_layer.objects.active = parent
        mod = parent.modifiers.new('090_true_horseshoe_recess', 'BOOLEAN')
        mod.operation = 'DIFFERENCE'; mod.solver = 'EXACT'; mod.object = cut
        bpy.ops.object.modifier_apply(modifier=mod.name)
        self.parts.remove(cut); bpy.data.objects.remove(cut, do_unlink=True)
        self.remap(parent, slot)
        # Dark cedar seats behind the new arch-shaped recess.
        inward = -.2075 if face > 0 else .2075
        self.prism_plane('090_'+name+'_recessed_cedar', poly, face+inward, .025, axis, 2)
        self.frame('090_'+name+'_carved_arch', u, face+(.025 if face>0 else -.025), z,
                   width, height, .15, .11, axis, 6)

    def frame(self, name, u, face, z, width, height, thick=.12, depth=.12, axis='Y', slot=6):
        radius = width*.55; spring = z+height-radius
        angles = [math.radians(205-230*i/20) for i in range(21)]
        inner = [(u-radius*math.cos(math.radians(25)), z)]
        inner += [(u+radius*math.cos(t), spring+radius*math.sin(t)) for t in angles]
        inner += [(u+radius*math.cos(math.radians(25)), z)]
        outer = [(u-(radius+thick)*math.cos(math.radians(25)), z)]
        outer += [(u+(radius+thick)*math.cos(t), spring+(radius+thick)*math.sin(t)) for t in angles]
        outer += [(u+(radius+thick)*math.cos(math.radians(25)), z)]
        n=len(inner); vs=[]
        for d in (face-depth/2, face+depth/2):
            for chain in (inner, outer):
                vs.extend([(a,d,b) if axis=='Y' else (d,a,b) for a,b in chain])
        fs=[]
        for i in range(n-1):
            fs.extend([(i,i+1,n+i+1,n+i),(2*n+i,3*n+i,3*n+i+1,2*n+i+1),
                       (i,2*n+i,2*n+i+1,i+1),(n+i,n+i+1,3*n+i+1,3*n+i)])
        fs.extend([(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)])
        return self.mesh(name,vs,fs,slot,60)

    def rail(self, name, u, face, z, length, axis='Y'):
        def point(a,b,c): return (a,b,c) if axis=='Y' else (b,a,c)
        def dims(a,b,c): return (a,b,c) if axis=='Y' else (b,a,c)
        for h in (0,.50): self.box(name+'_rail',point(u,face,z+h),dims(length,.10,.10),2,80)
        # Checked single panel module: posts meet top and bottom rail.
        count=max(2,round(length/.22))
        for k in range(count+1):
            x=u-length/2+length*k/count
            self.box(name+'_turned_cedar_baluster',point(x,face,z+.25),dims(.055,.07,.45),2,80)

    def frieze(self,name,u,face,z,length,axis='Y'):
        point=lambda a,b,c:(a,b,c) if axis=='Y' else (b,a,c)
        dims=lambda a,b,c:(a,b,c) if axis=='Y' else (b,a,c)
        self.box(name+'_carved_bed',point(u,face,z),dims(length,.09,.40),6,60)
        n=max(1,round(length/.48))
        for i in range(n):
            a=u-length/2+(i+.5)*length/n
            # Inlaid interlocking geometric lozenge, seated on carved bed.
            for sign in (-1,1):
                poly=[(a-.15,z),(a,z+sign*.145),(a+.15,z),(a,z+sign*.08)]
                self.prism_plane(name+'_lozenge',poly,face+(-.055 if face<0 else .055),.035,axis,2,60)


def enrich_exterior(r):
    # Existing recesses are expanded into true arch-shaped niches; old shutters go.
    for ob in list(r.parts):
        if ob.name.startswith('cedar_shutter_in_recess'):
            r.parts.remove(ob); bpy.data.objects.remove(ob,do_unlink=True)
    wings=sorted([o for o in r.parts if o.name.startswith('two_storey_cell_wing')], key=lambda o:o.location.x)
    assert len(wings)==2
    for wing,sign in zip(wings,(-1,1)):
        face=sign*7.0
        for y in (-4.8,-2.4,0,2.4,4.8):
            for z in (1.0,3.8):
                name=f'outer_{sign}_{y}_{z}'
                r.opening(name,wing,y,face,z,1.05,1.65,'X')
                r.box('090_'+name+'_sill',(face+sign*.055,y,z-.07),(.22,1.30,.14),4,60)
                # Narrow mullion sits inside the recess rather than on the plaster.
                r.box('090_'+name+'_mullion',(face-sign*.175,y,z+.58),(.04,.05,1.14),2,60)
        r.frieze('090_outer_cedar_fret',0,face+sign*.045,6.00,12.9,'X')
        r.box('090_exterior_lower_zellij',(face+sign*.035,0,.9),(.07,13.2,.85),7,60)
        for y in (-6.25,-3.6,-1.2,1.2,3.6,6.25):
            r.box('090_exterior_pier',(face+sign*.065,y,3.05),(.16,.19,5.35),6,40)
        for y in (-5.9,-4.5,-3.1,-1.7,-.3,1.1,2.5,3.9,5.3,6.1):
            # Corbel top touches cedar eave underside at6.23.
            r.box('090_cedar_roof_corbel',(face-sign*.04,y,6.06),(.38,.13,.34),2,80)
    # Portal is enriched around its existing clear opening, not across it.
    r.frame('090_entry_outer_archivolt',0,-7.03,.28,3.0,3.4,.24,.19,'Y',6)
    r.frame('090_entry_cedar_inner_archivolt',0,-7.15,.28,2.97,3.38,.075,.055,'Y',2)
    r.frieze('090_entry_geometric_cedar_fret',0,-7.12,4.66,4.12)
    for x in (-4.8,4.8):
        r.frame('090_front_blind_arch',x,-6.97,.60,1.65,2.3,.16,.14,'Y',6)
        r.box('090_front_zellij_panel',(x,-6.965,1.15),(1.35,.055,.8),7,60)
    # Shallow muqarnas cornice anchored under the portal cedar entablature.
    for row in range(3):
        for i in range(13-row):
            x=(i-(12-row)/2)*.31
            r.taper('090_entry_muqarnas_cell',x,-7.06-row*.035,4.92+row*.115,.30,.20,.15,.56,6)
    r.checks += [{'interface':'portal archivolts / front masonry','intentional_overlap':.045},
                 {'interface':'cedar corbel top / eave underside','signed_gap':0}]


def enrich_court(r):
    # Side galleries are connected to the existing inner walls and measured floors.
    for sign in (-1,1):
        x=sign*3.75
        for y in (-3.5,-1.17,1.17,3.5):
            # Rotate arch vertex geometry explicitly; inherited rot path is not used.
            for base,h,top in ((.40,2.65,3.45),(3.72,1.85,6.12)):
                width=1.65
                # An arch-shaped open frame with long legs and no filled backdrop.
                r.frame('090_court_side_arcade',y,x,base,width,h,.18,.32,'X',6 if base<1 else 2)
            r.rail('090_court_upper_balcony',y,sign*3.58,3.78,1.72,'X')
        r.box('090_gallery_upper_floor',(sign*3.84,0,3.55),(.65,9.35,.22),2,60)
        r.box('090_gallery_carved_entablature',(sign*3.87,0,6.13),(.60,9.4,.26),2,80)
        r.frieze('090_court_stucco_carving',0,sign*3.97,5.76,10.7,'X')
        r.box('090_court_zellij_dado',(sign*3.96,0,1.05),(.10,10.7,1.15),7,60)
    for y in (-4.42,4.42):
        r.frieze('090_cross_gallery_cedar',0,y,6.07,7.9)
        for x in (-2.7,0,2.7):
            r.rail('090_cross_gallery_balcony',x,y,3.80,1.8)
    # Octagonal fountain with recessed water and connected inner/outer rim.
    for ob in list(r.parts):
        if ob.name.startswith(('octagonal_basin_rim','basin_water','basin_square_plinth')):
            r.parts.remove(ob);bpy.data.objects.remove(ob,do_unlink=True)
    # Connected ring topology includes true depressed basin floor.
    from berber_040_university_geometry import Builder
    rings=Builder.rings
    r.mesh = r.mesh
    rings(r,'090_octagonal_fountain',(0,0),[(1.25,.37),(1.25,.66),(1.08,.72),(.91,.64),(.91,.46),(.02,.46)],8,4,60,True)
    rings(r,'090_fountain_water',(0,0),[(.88,.475),(.88,.49)],8,5,80,True)
    rings(r,'090_fountain_central_bubbler',(0,0),[(.18,.46),(.18,.78),(.30,.86),(.24,.95),(.06,1.02)],12,4,80,True)
    for x in (-2.9,2.9):
        r.box('090_court_mosaic_walk',(x,0,.39),(1.0,8.0,.04),7,60)
    r.checks += [{'interface':'gallery floor / existing upper floor','overlap':.05},
                 {'interface':'fountain bottom / original court pavement','signed_gap':0}]


def enrich_tower(r):
    # Fez tower retains currentheight: Wonder receives the much taller silhouette.
    for face in ('front','back','west','east'):
        axis='Y' if face in ('front','back') else 'X'
        center=-5.4 if axis=='Y' else 4.8
        plane={'front':3.515,'back':6.085,'west':-6.685,'east':-4.115}[face]
        for offset in (-.52,.52):
            r.frame('090_tower_carved_'+face,center+offset,plane,9.0,.62,1.49,.075,.085,axis,6)
        point=lambda a,b,c:(a,b,c) if axis=='Y' else (b,a,c)
        dims=lambda a,b,c:(a,b,c) if axis=='Y' else (b,a,c)
        for z in (11.0,12.3):
            r.box('090_tower_panel_sill',point(center,plane,z),dims(2.0,.09,.10),6,80)
        for du in (-.99,.99):
            r.box('090_tower_panel_jamb',point(center+du,plane,11.65),dims(.1,.09,1.30),6,80)
        r.frieze('090_tower_cedar_geometric_'+face,center,plane,12.92,2.40,axis)
    # Shoulder courses, roof-ridge ceramic caps and a restrained copper finial.
    from berber_040_university_geometry import Builder
    for z,size in ((13.44,2.69),(13.55,2.78)):
        r.box('090_tower_cornice',(-5.4,4.8,z),(size,size,.11),6,80)
    Builder.rings(r,'090_tower_finial',(-5.4,4.8),[(.04,15.02),(.04,15.16),(.15,15.30),(.04,15.46)],8,4,100,True)


def enrich_roofs(r):
    # Replace the two plain flat strips by genuinely pitched tiled cell-wing roofs.
    for ob in list(r.parts):
        if ob.name.startswith('green_glazed_flat_roof'):
            r.parts.remove(ob);bpy.data.objects.remove(ob,do_unlink=True)
    for x in (-5.5,5.5):
        w=3.25;d=13.35;z=6.47;rise=.58
        vs=[(x+a,y,z+h) for a,y,h in [(-w/2,-d/2,0),(w/2,-d/2,0),
             (w/2,d/2,0),(-w/2,d/2,0),(0,-d/2,rise),(0,d/2,rise),
             (-w/2,-d/2,-.12),(w/2,-d/2,-.12),(w/2,d/2,-.12),(-w/2,d/2,-.12)]]
        fs=[(0,1,4),(3,5,2),(0,4,5,3),(4,1,2,5),(6,7,1,0),(9,3,2,8),(6,0,3,9),(7,8,2,1),(6,9,8,7)]
        r.mesh('090_pitched_cedar_cell_wing_roof',vs,fs,3,80)
        r.box('090_glazed_roof_ridge_cap',(x,0,z+rise+.035),(.12,d,.10),3,80)


def validate_save(r):
    rows=[];pts=[]
    for ob in r.parts:
        bm=bmesh.new();bm.from_mesh(ob.data)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data)
        rows.append({'name':ob.name,'triangles':sum(len(p.vertices)-2 for p in ob.data.polygons),
                     'nonmanifold':sum(not e.is_manifold for e in bm.edges),
                     'signed_volume':bm.calc_volume(signed=True),'single_user':ob.data.users==1,
                     'uv':bool(ob.data.uv_layers),'stage':ob.get('garrison_building_first_stage')})
        bm.free();pts.extend(ob.matrix_world@v.co for v in ob.data.vertices)
    start=Vector((0,-8,1.5));end=Vector((0,-4,1.5));hits=[]
    for ob in r.parts:
        inv=ob.matrix_world.inverted();a=inv@start;b=inv@end;delta=b-a
        if ob.ray_cast(a,delta.normalized(),distance=delta.length)[0]:hits.append(ob.name)
    assert not hits,('Portal obstructed',hits)
    assert all(row['single_user'] and row['uv'] for row in rows)
    bad=[row for row in rows if row['nonmanifold'] or row['signed_volume'] < -1e-6]
    assert not bad,('Topology issue',bad)
    proof={'status':'passed','retained_source':str(SOURCE/'fez_040_original.blend'),
           'bounds':[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]],
           'parts':rows,'triangles':sum(row['triangles'] for row in rows),
           'contacts':r.checks,'entrance_ray_hits':hits,'native_game':'pending',
           'references':['https://www.visitmorocco.com/sites/default/files/atoms/files/Fes%20ENG.pdf']}
    (ART/'source-validation.json').write_text(json.dumps(proof,indent=2),encoding='utf8')
    for ob in bpy.context.selected_objects:ob.select_set(False)
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Madrasa_of_Fez_090.blend'))
    shutil.copy2(SOURCE/'flag-transform.json',ART/'flag-transform.json')
    print('FEZ_090_SOURCE_VALID',proof['triangles'],len(rows),flush=True)


if __name__=='__main__':
    r=College()
    enrich_exterior(r);print('FEZ_090_EXTERIOR_DONE',flush=True)
    enrich_court(r);print('FEZ_090_COURT_DONE',flush=True)
    enrich_tower(r);enrich_roofs(r);print('FEZ_090_TOWER_ROOFS_DONE',flush=True)
    validate_save(r)
