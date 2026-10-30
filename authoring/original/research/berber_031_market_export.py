"""Prepare one Berber market courtyard kit with installed Garrison static route.

No cook, mod-project mutation, or archive integration occurs here.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import bpy

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/"art/building_remix_0_3_1/market"
OUT=ROOT/"output/berber_update_0_3_1/market-static-prep/Assets/Custom/b031"
EXT=Path(os.environ["APPDATA"])/"Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
sys.path.insert(0,str(EXT.parent))
import garrison
from garrison.material_adoption import adopt_material


def constant_image(target,color):
    image=bpy.data.images.new(target.stem,width=64,height=64,alpha=True)
    image.generated_color=color
    image.filepath_raw=str(target)
    image.file_format="PNG"
    image.save()
    bpy.data.images.remove(image)


def main():
    selected=sys.argv[sys.argv.index("--")+1] if "--" in sys.argv else "age02"
    assert selected in ("age02","age03","age04")
    age=int(selected[-2:])
    asset_id=f"m{age}"
    bpy.ops.wm.open_mainfile(filepath=str(ART/f"Berber_market_{selected}_0_3_1.blend"))
    collection=bpy.data.collections[f"AGE {age:02} CONNECTED FUNDUQ ARCHITECTURE - EXPORT"]
    meshes=[o for o in collection.objects if o.type=="MESH"]
    assert meshes
    material_names=sorted({o.data.materials[0].name for o in meshes})
    source=OUT/asset_id/"source"
    source.mkdir(parents=True,exist_ok=True)
    records=[]
    joined=[]
    bpy.ops.object.select_all(action="DESELECT")
    for material_name in material_names:
        group=[o for o in collection.objects if o.type=="MESH" and o.data.materials[0].name==material_name]
        for o in group:
            assert len(o.data.materials)==1 and o.data.uv_layers.active is not None
            o.select_set(True)
        bpy.context.view_layer.objects.active=group[0]
        if len(group)>1: bpy.ops.object.join()
        obj=bpy.context.object
        role="earth" if "earthen" in material_name else "stone" if "stone" in material_name else "cedar"
        obj.name=f"geo_mat_market_{selected}_{role}"
        mat=obj.data.materials[0]
        adopt=adopt_material(mat)
        mid=f"market_{selected}_{role}"
        folder=source/"materials"/mid
        folder.mkdir(parents=True,exist_ok=True)
        image=next(node.image for node in mat.node_tree.nodes if node.type=="TEX_IMAGE" and node.image is not None)
        shutil.copy2(Path(bpy.path.abspath(image.filepath)),folder/"albedo.png")
        constant_image(folder/"normal.png",(0.5,0.5,1,1))
        constant_image(folder/"roughness.png",(0.86,0.86,0.86,1))
        constant_image(folder/"metalness.png",(0,0,0,1))
        records.append({"id":mid,"source_name":material_name,"mesh_name":obj.name,"textures":{slot:str(folder/(slot+".png")) for slot in ("albedo","normal","roughness","metalness")},"bindings":adopt["semantics"],"usage":{"objects":[obj.name],"faces":len(obj.data.polygons)}})
        joined.append(obj)
        bpy.ops.object.select_all(action="DESELECT")
    for obj in joined: obj.select_set(True)
    bpy.context.view_layer.objects.active=joined[0]
    fbx=source/"model.fbx"
    result=bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={"MESH"},use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,path_mode="AUTO",axis_forward="-Z",axis_up="Y",apply_unit_scale=True,use_space_transform=True)
    assert "FINISHED" in result
    request={"schema":"garrison.custom-static-authoring-request/v2","namespace":"b031","asset_id":asset_id,"catalog_folder":"Custom/Berber/Buildings","build_id":f"20261015T03020{age-2}Z-m{age}","source":{"fbx":str(fbx)},"materials":records,"blender_executable":str(Path(bpy.app.binary_path).resolve(strict=True)),"template_project":"C:/Users/RS/AppData/Local/Garrison/Kit/template-project","asset_root":str(OUT/asset_id),"cook_editor":"C:/Users/RS/AppData/Local/Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe"}
    request_path=OUT/asset_id/".garrison/requests"/f"berber-031-market-{selected}.json"
    request_path.parent.mkdir(parents=True,exist_ok=True)
    request_path.write_text(json.dumps(request,indent=2)+"\n",encoding="utf-8")
    (ART/f"market_{selected}-garrison-authoring.json").write_text(json.dumps({"request":str(request_path),"asset_root":str(OUT/asset_id),"source_fbx":str(fbx),"materials":records,"status":"source prepared; run garrison-core static prepare then coordinator cook"},indent=2)+"\n",encoding="utf-8")
    print("BERBER_031_MARKET_GARRISON_REQUEST",selected,request_path,flush=True)


if __name__=="__main__":
    main()
