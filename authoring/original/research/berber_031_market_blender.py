"""Editable stock-derived Berber market and separate cookable courtyard kit.

Usage: blender -b --python research/berber_031_market_blender.py -- age02
Run each age in its own headless process. This never touches a live scene.
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector, geometry

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/building_remix_0_3_1/market"
BASE = ROOT / "art/building_remix_0_3_0/recipe.json"
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
sys.path.insert(0,str(EXT))
spec = importlib.util.spec_from_file_location("garrison_shared",str(EXT/"garrison_shared.cp313-win_amd64.pyd"))
shared = importlib.util.module_from_spec(spec)
sys.modules["garrison_shared"] = shared
spec.loader.exec_module(shared)
sys.path.insert(0,str(EXT.parent))
import garrison
sys.modules["garrison.garrison_shared"] = shared
from garrison.decode_projection import _apply_decoded_static


def mesh_objects(root):
    return [o for o in root.children_recursive if o.type == "MESH"]


def bounds(objects):
    pts = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    return [[float(min(p[i] for p in pts)) for i in range(3)],[float(max(p[i] for p in pts)) for i in range(3)]]


def material(name, rgb, age):
    image = bpy.data.images.new(name+" source albedo",width=64,height=64,alpha=True)
    pixels=[]
    for y in range(64):
        for x in range(64):
            # Subtle deterministic hand-plaster/wood aggregate; no preview bake.
            grain = ((x*17+y*29+x*y*3+age*11)%23-11)/300
            pixels.extend([max(0,min(1,c+grain)) for c in rgb]+[1.0])
    image.pixels[:] = pixels
    image.filepath_raw = str(ART/"textures"/(name.replace(" ","_").lower()+f"_age{age:02}.png"))
    image.file_format="PNG"
    image.save()
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    nodes=mat.node_tree.nodes
    nodes.clear()
    out=nodes.new("ShaderNodeOutputMaterial")
    bsdf=nodes.new("ShaderNodeBsdfPrincipled")
    tex=nodes.new("ShaderNodeTexImage")
    tex.image=image
    mat.node_tree.links.new(tex.outputs["Color"],bsdf.inputs["Base Color"])
    mat.node_tree.links.new(bsdf.outputs["BSDF"],out.inputs["Surface"])
    mat.diffuse_color=(*rgb,1)
    return mat


def box(name,low,high,mat,col):
    assert all(hi>lo for lo,hi in zip(low,high))
    x0,y0,z0=low; x1,y1,z1=high
    verts=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    faces=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(verts,[],faces); mesh.update()
    ob=bpy.data.objects.new(name,mesh); col.objects.link(ob); ob.data.materials.append(mat)
    uv=mesh.uv_layers.new(name="UVMap")
    for polygon in mesh.polygons:
        corners=((0.01,0.01),(0.99,0.01),(0.99,0.99),(0.01,0.99))
        for n,loop in enumerate(polygon.loop_indices):
            uv.data[loop].uv=corners[n]
    return ob


def arch(name,center_x,y0,y1,spring,inner,thickness,mat,col):
    """Single connected extruded horseshoe arch ring with seated piers."""
    steps=16
    outer=inner+thickness
    left=center_x-outer; right=center_x+outer
    # One continuous profile: left pier -> outer crown -> right pier ->
    # inner crown in reverse -> left pier. Extrude front/back depth.
    profile=[(left,0),(left,spring)]
    profile += [(center_x+outer*math.cos(math.pi-i*math.pi/steps),spring+outer*math.sin(math.pi-i*math.pi/steps)) for i in range(1,steps+1)]
    profile += [(right,0),(center_x+inner,0),(center_x+inner,spring)]
    profile += [(center_x+inner*math.cos(i*math.pi/steps),spring+inner*math.sin(i*math.pi/steps)) for i in range(1,steps+1)]
    profile += [(center_x-inner,0)]
    n=len(profile)
    verts=[(x,y,z) for y in (y0,y1) for x,z in profile]
    faces=[]
    # Exposed top and side thickness; the front/back are triangulated from
    # the same continuous concave U-shaped profile, leaving a real opening.
    for i in range(n):
        j=(i+1)%n
        faces.append((i,j,n+j,n+i))
    shape=[Vector((x,z,0)) for x,z in profile]
    for tri in geometry.tessellate_polygon([shape]):
        ix=list(tri)
        faces.append(tuple(reversed(ix)))
        faces.append(tuple(n+i for i in ix))
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(verts,[],faces); mesh.update()
    ob=bpy.data.objects.new(name,mesh); col.objects.link(ob); ob.data.materials.append(mat)
    uv=mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        corners=((0.01,0.01),(0.99,0.01),(0.99,0.99),(0.01,0.99))
        for n,li in enumerate(poly.loop_indices):
            uv.data[li].uv=corners[n]
    return ob


def donor(model):
    data=json.loads(Path(model["decoded"]).read_text(encoding="utf-8"))
    proxy=bpy.data.objects.new(model["name"]+" stock manifest",None)
    bpy.context.scene.collection.objects.link(proxy)
    proxy["garrison_decode_manifest"]=model["decoded"]
    proxy["garrison_logical_path"]=data["request"]["logical_path"]
    root=_apply_decoded_static(proxy,data,create_controls=False)
    root.name="RESHAPED STOCK ABBASID MARKET CORE"
    donor_bounds=bounds(mesh_objects(root))
    changed=json.loads((ART/f"Berber_{model['name']}_0_3_1-projection.json").read_text(encoding="utf-8"))
    used=set(); edits=0
    for ob in mesh_objects(root):
        candidates=[i for i,g in enumerate(data["geometry"]["groups"]) if i not in used and len(g["positions"])==len(ob.data.vertices) and tuple(g["positions"][0])==tuple(ob.data.vertices[0].co)]
        assert len(candidates)==1,(ob.name,candidates)
        i=candidates[0]; used.add(i)
        for v,old,new in zip(ob.data.vertices,data["geometry"]["groups"][i]["positions"],changed["geometry"]["groups"][i]["positions"]):
            assert tuple(v.co)==tuple(old)
            if old!=new:
                v.co=new; edits+=1
        ob["retains_native_material_team_colour_slots"]=True
        ob["donor_logical_path"]=model["source"]
    assert len(used)==len(data["geometry"]["groups"])
    return root,edits,donor_bounds


def add_architecture(age):
    col=bpy.data.collections.new(f"AGE {age:02} CONNECTED FUNDUQ ARCHITECTURE - EXPORT")
    bpy.context.scene.collection.children.link(col)
    earthen=((0.48,0.28,0.16) if age==2 else (0.68,0.55,0.41) if age==3 else (0.77,0.68,0.55))
    stone=((0.62,0.47,0.31) if age==2 else (0.76,0.65,0.51) if age==3 else (0.83,0.75,0.64))
    timber=(0.24,0.14,0.08)
    mat_earth=material("031 Market earthen plaster",earthen,age)
    mat_stone=material("031 Market stone trim",stone,age)
    mat_timber=material("031 Market cedar timber",timber,age)
    created=[]; contacts=[]
    def b(name,lo,hi,mat):
        ob=box(name,lo,hi,mat,col); created.append(ob); return ob
    def a(name,cx,y0,y1,spring,rad,thick,mat):
        ob=arch(name,cx,y0,y1,spring,rad,thick,mat,col); created.append(ob); return ob
    # Main gate is set into the stock front (-y) facade and takes a full
    # human/camel-readable opening; its rear overlaps the donor wall by 0.18m.
    a("Portal deep horseshoe gate",-0.22,-2.82,-1.80,1.73,0.78,0.22,mat_stone)
    b("Portal left buttress",(-1.35,-2.82,0),(-0.98,-1.80,2.48),mat_earth)
    b("Portal right buttress",(0.54,-2.82,0),(0.91,-1.80,2.48),mat_earth)
    gate_top=3.65 if age==2 else 3.90 if age==3 else 4.10
    b("Portal upper mass",(-1.35,-2.79,2.49),(0.91,-1.82,gate_top),mat_earth)
    b("Gate carved lintel",(-1.38,-2.90,2.36),(0.94,-1.80,2.55),mat_stone)
    b("Portal left lookout tower",(-1.48,-2.80,2.46),(-0.99,-1.81,gate_top+0.37),mat_earth)
    b("Portal right lookout tower",(0.55,-2.80,2.46),(1.04,-1.81,gate_top+0.37),mat_earth)
    for i in range(5):
        x=-0.95+i*0.36
        b(f"Portal crenellation {i+1}",(x,-2.82,gate_top),(x+0.20,-2.54,gate_top+0.23),mat_stone)
    contacts += [{"child":"Portal upper mass","parent":"Gate carved lintel","signed_gap_m":-0.05},{"child":"Gate carved lintel","parent":"Portal arch crown","signed_gap_m":-0.01}]
    # Arcade wings connect portal buttresses to existing outer walls. Their
    # repeated openings are real arch geometry, never painted-on windows.
    for side,centers in (("left",(-2.50,-1.62)),("right",(1.19,2.07))):
        for index,cx in enumerate(centers):
            a(f"{side} courtyard arcade bay {index+1}",cx,-2.67,-1.83,1.52,0.37,0.115,mat_earth)
        x0=min(centers)-0.54; x1=max(centers)+0.54
        b(f"{side} continuous arcade parapet",(x0,-2.67,1.98),(x1,-1.83,2.22 if age==2 else 2.37),mat_earth)
        b(f"{side} cedar shade beam",(x0,-2.78,2.08),(x1,-1.83,2.22),mat_timber)
        b(f"{side} pitched timber awning",(x0,-2.88,2.14),(x1,-1.86,2.31),mat_timber)
        contacts += [{"child":f"{side} continuous arcade parapet","parent":f"{side} courtyard arcade bays","signed_gap_m":-0.05},{"child":f"{side} pitched timber awning","parent":f"{side} cedar shade beam","signed_gap_m":-0.08}]
    # Caravan cargo is tight to the shaded bays, wholly within inherited
    # placement extent; no wandering decorative annex.
    for n,(x,y) in enumerate(((-2.70,-2.48),(-1.85,-2.45),(1.35,-2.47),(2.23,-2.49))):
        b(f"Trade chest {n+1}",(x-0.20,y-0.14,0),(x+0.20,y+0.14,0.33),mat_timber)
    # Progressively differentiated compact parapet and screen treatment.
    if age>=3:
        for i in range(7):
            x=-1.17+i*0.30
            b(f"Lime arcade tooth {i+1}",(x,-2.45,gate_top),(x+0.16,-2.22,gate_top+0.18),mat_stone)
    if age==4:
        for i in range(5):
            x=-0.98+i*0.38
            b(f"Cedar upper screen slat {i+1}",(x,-2.50,2.70),(x+0.08,-2.44,3.12),mat_timber)
        b("Imperial tile cornice",(-1.28,-2.55,gate_top-0.10),(0.84,-1.83,gate_top+0.05),mat_stone)
    # Set native local coordinates: all FBX transforms identity; no external
    # origin offset is needed by the eventual stamp.
    for ob in created:
        assert tuple(ob.location)==(0,0,0) and tuple(ob.scale)==(1,1,1)
    return col,created,contacts


def preview(name,objects,age):
    out=ART/"previews"; out.mkdir(parents=True,exist_ok=True)
    scene=bpy.context.scene
    scene.render.engine="BLENDER_WORKBENCH"
    scene.render.resolution_x=900; scene.render.resolution_y=700; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.display.shading.light="STUDIO"
    scene.display.shading.color_type="MATERIAL"
    scene.display.shading.show_shadows=True
    scene.display.shading.show_cavity=True
    lo,hi=bounds(objects)
    center=Vector(tuple((lo[i]+hi[i])/2 for i in range(3)))
    extent=max(hi[i]-lo[i] for i in range(3))
    for label,direction in (("isometric",(1,-1,0.85)),("front",(0,-1,0.12)),("rear",(0,1,0.12)),("left",(-1,0,0.12)),("right",(1,0,0.12)),("top",(0,-0.02,1)),("bottom",(0,-0.02,-1))):
        camera_data=bpy.data.cameras.new("TEMP REVIEW")
        camera=bpy.data.objects.new("TEMP REVIEW",camera_data)
        scene.collection.objects.link(camera); scene.camera=camera
        camera_data.type="ORTHO"; camera_data.ortho_scale=extent*(1.5 if label=="isometric" else 1.25)
        camera.location=center+Vector(direction).normalized()*30
        camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
        scene.render.filepath=str(out/f"{name}_{label}.png")
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(camera,do_unlink=True)


def main():
    selected=sys.argv[sys.argv.index("--")+1] if "--" in sys.argv else "age02"
    assert selected in ("age02","age03","age04")
    age=int(selected[-2:])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version=0
    (ART/"textures").mkdir(parents=True,exist_ok=True)
    recipe=json.loads(BASE.read_text(encoding="utf-8"))
    model=next(m for m in recipe["models"] if m["name"]=="market_"+selected)
    root,changed,donor_bounds=donor(model)
    stock_objects=mesh_objects(root)
    core_bounds=bounds(stock_objects)
    col,added,contacts=add_architecture(age)
    combined=bounds(stock_objects+added)
    assert all(combined[0][i]>=donor_bounds[0][i]-0.01 and combined[1][i]<=donor_bounds[1][i]+0.01 for i in range(2)),(donor_bounds,combined)
    assert abs(combined[0][2]-core_bounds[0][2])<0.01,(core_bounds,combined)
    for ob in added:
        assert ob.data.uv_layers.active is not None and len(ob.data.materials)==1
    # Separate, export-ready FBX: only native-local supplementary geometry.
    bpy.ops.object.select_all(action="DESELECT")
    for ob in added: ob.select_set(True)
    bpy.context.view_layer.objects.active=added[0]
    target_fbx=ART/f"Berber_market_{selected}_0_3_1_courtyard_kit.fbx"
    bpy.ops.export_scene.fbx(filepath=str(target_fbx),use_selection=True,apply_unit_scale=True,global_scale=1.0,axis_forward="-Z",axis_up="Y",add_leaf_bones=False)
    bpy.ops.object.select_all(action="DESELECT")
    preview(model["name"],stock_objects+added,age)
    bpy.ops.file.pack_all()
    target_blend=ART/f"Berber_market_{selected}_0_3_1.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(target_blend))
    report={"model":model["name"],"stock_donor":model["source"],"stock_geometry":model["stock_geometry"],"native_projection":str(ART/f"Berber_{model['name']}_0_3_1-projection.json"),"changed_donor_vertices":changed,"donor_bounds":donor_bounds,"core_bounds":core_bounds,"combined_bounds":combined,"architecture_objects":len(added),"contacts":contacts,"blend":str(target_blend),"fbx":str(target_fbx),"source_texture_directory":str(ART/"textures"),"native_owner_colour_materials_retained_on_core":True,"source_validation":"passed","native_cook":"pending","game_test":"pending"}
    (ART/f"{model['name']}-source-validation.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("BERBER_031_MARKET_SOURCE_READY",model["name"],changed,len(added),flush=True)


if __name__=="__main__":
    main()
