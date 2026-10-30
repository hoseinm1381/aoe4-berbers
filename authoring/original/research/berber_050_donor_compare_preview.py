"""Render disposable, private previews of cached stock candidates only."""
from __future__ import annotations
import importlib.util, json, os, sys
import re
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT))
spec=importlib.util.spec_from_file_location('garrison_shared',str(EXT/'garrison_shared.cp313-win_amd64.pyd'))
shared=importlib.util.module_from_spec(spec);sys.modules['garrison_shared']=shared;spec.loader.exec_module(shared)
sys.path.insert(0,str(EXT.parent));import garrison;sys.modules['garrison.garrison_shared']=shared
from garrison.decode_projection import _apply_decoded_static

OUT=ROOT/'output/berber_update_0_5_0/donor_previews';OUT.mkdir(parents=True,exist_ok=True)

def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=1000;scene.render.resolution_y=900;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
    scene.view_settings.view_transform='Standard'
    world=bpy.data.worlds.new('Preview World');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.16,0.16,0.16,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=0.7;scene.world=world
    for name,loc,power,size in [('Key',(4,-7,7),1100,5),('Fill',(-5,-4,3),700,4),('Rim',(1,5,5),900,3)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
        obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=loc;obj.rotation_euler=(Vector((0,0,1.1))-obj.location).to_track_quat('-Z','Y').to_euler()
    return scene

def add_model(manifest_path,label,x):
    data=json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    proxy=bpy.data.objects.new(label+' source',None);bpy.context.scene.collection.objects.link(proxy)
    proxy['garrison_decode_manifest']=str(manifest_path);proxy['garrison_logical_path']=data['request']['logical_path'];proxy['garrison_display_name']=label
    root=_apply_decoded_static(proxy,data,create_controls=False);root.name=label
    meshes=[o for o in root.children_recursive if o.type=='MESH']
    # Garrison's projection may return a collection-like root whose children
    # are not parented to it. Offset actual decoded mesh world transforms so
    # each candidate remains separated in the render either way.
    root.location.x=0
    for obj in meshes:
        mat=obj.matrix_world.copy();mat.translation.x+=x;obj.matrix_world=mat
    lod1=[o for o in meshes if re.search(r'lod[ _]?1(?:\.|$)',o.name,re.IGNORECASE)]
    if lod1:
        for obj in meshes:obj.hide_render=obj not in lod1
    print('PREVIEW_MESHES',label,[(o.name,o.hide_render) for o in meshes],flush=True)
    return meshes

def render_compare(rows,out_path):
    scene=setup_scene();meshes=[]
    for i,(label,manifest) in enumerate(rows):meshes.extend(add_model(manifest,label,(i-(len(rows)-1)/2)*2.2))
    lo=[min((o.matrix_world@Vector(c))[i] for o in meshes for c in o.bound_box) for i in range(3)]
    hi=[max((o.matrix_world@Vector(c))[i] for o in meshes for c in o.bound_box) for i in range(3)]
    center=Vector(tuple((a+b)/2 for a,b in zip(lo,hi)));camera_data=bpy.data.cameras.new('Review Camera');camera_data.type='ORTHO';camera_data.ortho_scale=max(hi[0]-lo[0],hi[2]-lo[2])*1.18
    camera=bpy.data.objects.new('Review Camera',camera_data);scene.collection.objects.link(camera);camera.location=center+Vector((0,-14,1.5));camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();scene.camera=camera
    scene.render.filepath=str(out_path);bpy.ops.render.render(write_still=True)

def main():
    # JSON maps preview filename to [[label, decoded-static.json], ...].
    jobs=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text(encoding='utf-8'))
    for filename,rows in jobs.items():render_compare(rows,OUT/filename)
    print('DONOR_PREVIEWS_RENDERED',len(jobs),flush=True)

if __name__=='__main__':main()
