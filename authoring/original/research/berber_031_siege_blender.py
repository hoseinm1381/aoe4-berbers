"""Build editable, stock-derived siege workshop scenes and one-piece yard kits.

Run from Blender 5.2 in background mode with BERBER_SIEGE_AGE=3 or 4.
Each scene keeps donor projection meshes separately selectable. The private
work-yard kit is a single mesh and single PNG atlas for Garrison static export.
"""

import json
import math
import os
import shutil
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/building_remix_0_3_1/siege"
AGE = int(os.environ["BERBER_SIEGE_AGE"])
assert AGE in (3, 4)
STEM = f"siege_age0{AGE}"
SOURCE = json.loads((ART / f"{STEM}-remix-projection.json").read_text(encoding="utf-8"))

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for material in list(bpy.data.materials):
    bpy.data.materials.remove(material)

donor_collection = bpy.data.collections.new(f"STOCK_DERIVED_ABBASID_AGE_{AGE}")
kit_collection = bpy.data.collections.new(f"BERBER_SIEGE_YARD_KIT_AGE_{AGE}")
bpy.context.scene.collection.children.link(donor_collection)
bpy.context.scene.collection.children.link(kit_collection)


def flat_material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    return mat


donor_colors = [(0.58, 0.43, 0.28), (0.65, 0.50, 0.33), (0.72, 0.60, 0.42), (0.43, 0.31, 0.22), (0.74, 0.66, 0.52)]
for i, group in enumerate(SOURCE["geometry"]["groups"]):
    vertices = [tuple(v) for v in group["positions"]]
    faces = [tuple(reversed(face)) for face in group["triangles"]]
    mesh = bpy.data.meshes.new(group["name"])
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv_data = group.get("uv_layers", {}).get("UVMap")
    if uv_data and len(uv_data) == len(vertices):
        uv_layer = mesh.uv_layers.new(name="UVMap")
        for poly in mesh.polygons:
            for loop_index in poly.loop_indices:
                index = mesh.loops[loop_index].vertex_index
                uv_layer.data[loop_index].uv = tuple(uv_data[index])
    obj = bpy.data.objects.new(group["name"], mesh)
    donor_collection.objects.link(obj)
    obj.data.materials.append(flat_material(f"stock_part_{i}", donor_colors[i%len(donor_colors)]))
    obj["stock_donor"] = SOURCE["request"]["logical_path"]
    obj["native_geometry"] = str(ART / f"{STEM}.rrgeom")
    obj["geometry_group"] = i


SWATCH = {
    "earth": 0, "plaster": 1, "cedar": 2, "cloth": 3,
    "tile": 4, "iron": 5, "rope": 6, "accent": 7,
}
COLORS = (
    ((0.47,0.27,0.15),(0.71,0.59,0.43),(0.31,0.19,0.10),(0.71,0.43,0.19),(0.38,0.32,0.23),(0.19,0.17,0.14),(0.54,0.41,0.23),(0.13,0.35,0.36))
    if AGE == 3 else
    ((0.43,0.27,0.18),(0.82,0.75,0.60),(0.28,0.17,0.10),(0.55,0.37,0.21),(0.24,0.37,0.34),(0.18,0.18,0.17),(0.62,0.48,0.26),(0.22,0.49,0.47))
)


def make_atlas():
    path = ART / f"{STEM}-kit-atlas.png"
    width = 512
    image = bpy.data.images.new(f"{STEM}_KIT_ATLAS", width=width, height=width, alpha=True)
    pixels = [0.0] * (width*width*4)
    for y in range(width):
        swatch = min(7, y//64)
        color = COLORS[swatch]
        for x in range(width):
            i = 4*(y*width+x)
            grain = 0.94 + (((x*13+y*7) % 17)/17.0)*0.12
            if swatch == SWATCH["tile"] and y % 22 in (0,1):
                grain *= 0.79
            if swatch == SWATCH["cloth"] and x % 29 in (0,1):
                grain *= 0.87
            pixels[i:i+4] = [min(1.0, c*grain) for c in color] + [1.0]
    image.pixels[:] = pixels
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image, path


atlas, atlas_path = make_atlas()
material = bpy.data.materials.new(f"{STEM}_yard_atlas")
material.diffuse_color = (0.63,0.48,0.31,1.0)
material.use_nodes = True
nodes = material.node_tree.nodes
principled = nodes.get("Principled BSDF")
tex = nodes.new("ShaderNodeTexImage")
tex.image = atlas
material.node_tree.links.new(tex.outputs["Color"], principled.inputs["Base Color"])
principled.inputs["Roughness"].default_value = 0.84

extension_parent = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com"
sys.path.insert(0,str(extension_parent))
from garrison.material_adoption import adopt_material
material_contract = adopt_material(material)


def constant_map(name, rgb):
    path = ART / f"{STEM}-kit-{name}.png"
    image = bpy.data.images.new(f"{STEM}_{name}",width=512,height=512,alpha=True)
    image.pixels[:] = list((*rgb,1.0))*(512*512)
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return path


normal_path=constant_map("normal",(0.5,0.5,1.0))
rough_path=constant_map("roughness",(0.84,0.84,0.84))
metal_path=constant_map("metalness",(0.0,0.0,0.0))

verts = []
faces = []
face_swatches = []
interfaces = []


def add_faces(name, coordinates, polygons, swatch):
    base = len(verts)
    verts.extend(coordinates)
    for poly in polygons:
        faces.append(tuple(base+j for j in poly))
        face_swatches.append(SWATCH[swatch])
    return name


BOX_FACES = ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))


def box(name, lower, upper, swatch):
    x0,y0,z0 = lower
    x1,y1,z1 = upper
    assert x1>x0 and y1>y0 and z1>z0, name
    v = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
         (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    add_faces(name,v,BOX_FACES,swatch)


def sloped_panel(name, x0, x1, y0, y1, z_front, z_back, thickness, swatch):
    lower = [(x0,y0,z_front),(x1,y0,z_front),(x1,y1,z_back),(x0,y1,z_back)]
    upper = [(x,y,z+thickness) for x,y,z in lower]
    add_faces(name, lower+upper, BOX_FACES, swatch)


def wheel(name, cx,cy,cz, radius, depth, swatch):
    n=12
    vertices=[]
    for side in (-1,1):
        for rad in (radius*0.64, radius):
            for i in range(n):
                theta=2*math.pi*i/n
                vertices.append((cx+math.cos(theta)*rad, cy+side*depth/2, cz+math.sin(theta)*rad))
    polygons=[]
    for i in range(n):
        j=(i+1)%n
        polygons.extend(((i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),
                         (i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)))
    add_faces(name,vertices,polygons,swatch)


# Contact interface: rear canopy edge penetrates the donor inner north wall
# at y=1.32 by 0.12 m. Its near edge seats on the front timber posts.
rear_wall_y = 1.32
roof_rear_y = 1.44
roof_front_y = -0.10
roof_front_z = 2.44 if AGE == 3 else 2.53
roof_back_z = 2.92 if AGE == 3 else 3.15
roof_left,roof_right = -0.78,3.06
box("front_eave_beam",(-0.72,-0.14,roof_front_z-0.18),(2.96,0.08,roof_front_z+0.02),"cedar")
box("rear_wall_plate",(-0.72,1.25,roof_back_z-0.21),(2.96,1.47,roof_back_z+0.02),"cedar")
interfaces.append({"child":"rear_wall_plate","parent":"stock inner north wall","parent_plane_y":rear_wall_y,"child_overlaps_plane_m":round(roof_rear_y-rear_wall_y,3)})
for x in (-0.56,2.78):
    box(f"front_post_{x}",(x-0.11,-0.10,0.0),(x+0.11,0.11,roof_front_z-0.05),"cedar")
    box(f"post_foot_{x}",(x-0.19,-0.17,0.0),(x+0.19,0.18,0.17),"earth")
interfaces.append({"child":"front posts","parent":"front_eave_beam","overlap_m":0.13,"ground_contact_z":0.0})
for x in (-0.60,0.52,1.64,2.82):
    sloped_panel(f"rafter_{x}",x-0.07,x+0.07,-0.08,1.43,
                 roof_front_z-0.12,roof_back_z-0.12,0.10,"cedar")
sloped_panel("workshop_shelter_roof",roof_left,roof_right,roof_front_y,roof_rear_y,
             roof_front_z,roof_back_z,0.095,"cloth" if AGE == 3 else "tile")
interfaces.append({"child":"shelter roof","parent":"rafters and wall plate","rear_overlap_m":0.12,"front_beam_overlap_m":0.08})

# North/east edge remains a walkable work yard; the main siege exit is x<-1.2,
# y<-2.0 and receives no new mesh.
box("east_workbench_top",(2.16,-0.40,0.76),(2.88,0.70,0.90),"cedar")
for x in (2.27,2.73):
    for y in (-0.25,0.56):
        box(f"bench_leg_{x}_{y}",(x-0.065,y-0.065,0),(x+0.065,y+0.065,0.81),"cedar")
box("timber_stock_rack",(1.96,0.88,0.0),(2.94,1.13,0.36),"cedar")
box("saw_table",(2.15,-1.12,0.0),(2.85,-0.91,0.46),"cedar")
wheel("siege_wheel_1",2.52,0.84,0.51,0.40,0.10,"cedar")
wheel("siege_wheel_2",2.16,1.01,0.45,0.34,0.09,"cedar")
for x in (0.12,0.51):
    box(f"stacked_beam_{x}",(x,-0.19,0.0),(x+0.18,1.08,0.16),"cedar")
box("anvil_plinth",(1.44,0.64,0),(1.87,1.10,0.74),"earth")
box("anvil_top",(1.34,0.56,0.72),(1.99,1.17,0.86),"iron")

if AGE == 4:
    # Stone-and-cedar hoist tower in the rear corner: its legs pierce the
    # donor roof plane and its crossbeam visibly carries the pulley arm.
    tx0,tx1 = 2.28,3.15
    ty0,ty1 = 1.70,2.62
    for x in (tx0,tx1):
        for y in (ty0,ty1):
            box(f"hoist_corner_{x}_{y}",(x-0.10,y-0.10,2.48),(x+0.10,y+0.10,4.17),"plaster")
    box("hoist_architrave",(tx0-0.14,ty0-0.14,4.04),(tx1+0.14,ty1+0.14,4.25),"cedar")
    box("hoist_gable",(tx0-0.23,ty0-0.22,4.19),(tx1+0.23,ty1+0.22,4.56),"tile")
    box("cantilever_crane",(2.68,0.88,4.12),(2.87,1.83,4.25),"cedar")
    box("hoist_rope",(2.73,0.89,2.87),(2.79,0.95,4.18),"rope")
    interfaces.append({"child":"hoist tower legs","parent":"stock rear roof","pierces_roof_by_m":0.18})
else:
    box("hide_stretching_frame",(0.68,0.75,0.0),(1.25,1.02,1.49),"cedar")
    box("cloth_shade_extension",(-0.69,-0.13,2.49),(0.27,0.05,2.63),"accent")

mesh = bpy.data.meshes.new(f"{STEM}_one_piece_yard_mesh")
mesh.from_pydata(verts,[],faces)
mesh.update()
uv = mesh.uv_layers.new(name="UVMap")
for polygon, swatch in zip(mesh.polygons,face_swatches):
    for corner, loop_index in enumerate(polygon.loop_indices):
        uv.data[loop_index].uv=(0.12 if corner in (0,3) else 0.88,
                                (swatch+(0.12 if corner in (0,1) else 0.88))/8.0)
kit = bpy.data.objects.new(f"{STEM}_connected_yard_kit",mesh)
kit_collection.objects.link(kit)
mesh.materials.append(material)
kit["attached_to"]="stock inner north wall y=1.32 and grounded yard"
kit["clear_exit"]="x<-1.2 and y<-2.0 unobstructed"

blend = ART / f"Berber_Siege_Workshop_Age_{AGE}.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.object.select_all(action="DESELECT")
kit.select_set(True)
bpy.context.view_layer.objects.active=kit
fbx = ART / f"{STEM}-yard-kit.fbx"
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={"MESH"},
                         use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,
                         path_mode="AUTO",axis_forward="-Z",axis_up="Y",
                         apply_unit_scale=True,use_space_transform=True)
report = {
    "schema":"berber.siege-kit/v1","age":AGE,"blend":str(blend),
    "fbx":str(fbx),"source_albedo":str(atlas_path),
    "source_normal":str(normal_path),"source_roughness":str(rough_path),
    "source_metalness":str(metal_path),
    "donor_groups":len(SOURCE["geometry"]["groups"]),
    "kit_vertices":len(verts),"kit_faces":len(faces),
    "kit_materials":1,"kit_uv_layers":len(mesh.uv_layers),
    "interfaces":interfaces,"large_exit_clearance":{"x_less_than":-1.2,"y_less_than":-2.0,"kit_verts_in_exit":sum(1 for x,y,z in verts if x<-1.2 and y<-2.0)},
    "construction_damage_ruin":"preserved by coordinator stock stamps and attachment lists",
}
(ART/f"{STEM}-kit-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
asset_root=Path("F:/aoe_4_temp/b031siege") / f"sg{AGE}/Assets/Custom/b031/sg{AGE}"
source_root=asset_root / "source"
source_root.mkdir(parents=True,exist_ok=True)
canonical_fbx=source_root / "model.fbx"
shutil.copy2(fbx,canonical_fbx)
canonical_maps={}
material_dir=source_root / "materials" / material_contract["material_id"]
material_dir.mkdir(parents=True,exist_ok=True)
for semantic,source_file in {"albedo":atlas_path,"normal":normal_path,"roughness":rough_path,"metalness":metal_path}.items():
    destination=material_dir / f"{semantic}.png"
    shutil.copy2(source_file,destination)
    canonical_maps[semantic]=str(destination)
static_request={
    "schema":"garrison.custom-static-authoring-request/v2",
    "namespace":"b031","asset_id":f"sg{AGE}",
    "catalog_folder":"Berber/Siege Workshop","build_id":f"20261015T000000Z-sg{AGE}",
    "source":{"fbx":str(canonical_fbx)},
    "materials":[{
        "id":material_contract["material_id"],
        "source_name":material.name,"mesh_name":"geo_mat_main",
        "textures":canonical_maps,
        "bindings":material_contract["semantics"],
        "usage":{"objects":[kit.name],"faces":len(faces)},
    }],
    "blender_executable":bpy.app.binary_path,
    "template_project":str(Path(os.environ["LOCALAPPDATA"]) / "Garrison/Kit/template-project"),
    "asset_root":str(asset_root),
    "cook_editor":str(Path(os.environ["LOCALAPPDATA"]) / "Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe"),
}
(ART/f"{STEM}-garrison-static-request.json").write_text(json.dumps(static_request,indent=2)+"\n",encoding="utf-8")
print("SIEGE_BLEND_READY",AGE,len(verts),len(faces),blend,fbx)
