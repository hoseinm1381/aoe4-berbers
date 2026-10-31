"""Bake multiple authored/stock-preview materials into one unique unit atlas.

Keeps source UVs and skin weights; Blender performs colour/data/normal baking.
"""
import bpy,math
from pathlib import Path
def pin_uv(material,name='UVMap'):
    tree=material.node_tree
    uv=tree.nodes.new('ShaderNodeUVMap');uv.uv_map=name
    for n in list(tree.nodes):
        if n.type=='TEX_IMAGE' and not n.inputs['Vector'].is_linked:tree.links.new(uv.outputs['UV'],n.inputs['Vector'])
def bake(obj,output,resolution=1024):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    for o in bpy.context.selected_objects:o.select_set(False)
    obj.hide_set(False);obj.hide_render=False;obj.select_set(True);bpy.context.view_layer.objects.active=obj
    original=[m for m in obj.data.materials if m]
    for m in original:pin_uv(m)
    uv=obj.data.uv_layers.new(name='TuaregAtlas');obj.data.uv_layers.active=uv
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(70),island_margin=.018,area_weight=.2,correct_aspect=True,scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8
    scene.render.bake.use_selected_to_active=False;scene.render.bake.margin=12
    material_nodes={}
    for m in original:
        out=next(n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
        p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        target=m.node_tree.nodes.new('ShaderNodeTexImage')
        material_nodes[m]=(out,p,target)
    paths={};images={}
    for role in ['albedo','roughness','metalness','pattern','normal']:
        im=bpy.data.images.new(obj.name+' '+role,width=resolution,height=resolution,alpha=True)
        if role!='albedo':im.colorspace_settings.name='Non-Color'
        temporary=[];restores=[]
        for m,(out,p,target) in material_nodes.items():
            tree=m.node_tree;target.image=im;tree.nodes.active=target
            if role=='normal':continue
            surface=out.inputs['Surface'];previous=surface.links[0].from_socket
            em=tree.nodes.new('ShaderNodeEmission');temporary.append((tree,em));em.inputs['Strength'].default_value=1
            if role=='pattern':em.inputs['Color'].default_value=(float(m.get('tuareg_owner_mask',0)),0,0,1)
            else:
                socket=p.inputs[{'albedo':'Base Color','roughness':'Roughness','metalness':'Metallic'}[role]]
                if socket.is_linked:tree.links.new(socket.links[0].from_socket,em.inputs['Color'])
                else:
                    value=socket.default_value
                    em.inputs['Color'].default_value=tuple(value) if role=='albedo' else (value,value,value,1)
            tree.links.new(em.outputs[0],surface);restores.append((tree,surface,previous))
        try:
            bpy.ops.object.bake(type='NORMAL' if role=='normal' else 'EMIT',normal_space='TANGENT',use_clear=True)
        finally:
            for tree,surface,previous in restores:tree.links.new(previous,surface)
            for tree,n in temporary:tree.nodes.remove(n)
        im.filepath_raw=str(output/(role+'.png'));im.file_format='PNG';im.save();images[role]=im;paths[role]=im.filepath_raw
        print('ATLAS_BAKED',obj.name,role,flush=True)
    m=bpy.data.materials.new(obj.name+' baked atlas');m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF')
    texcoord=m.node_tree.nodes.new('ShaderNodeUVMap');texcoord.uv_map='TuaregAtlas'
    for role,input_name in [('albedo','Base Color'),('roughness','Roughness'),('metalness','Metallic')]:
        n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=images[role];m.node_tree.links.new(texcoord.outputs['UV'],n.inputs['Vector']);m.node_tree.links.new(n.outputs['Color'],p.inputs[input_name])
    n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=images['normal'];normal=m.node_tree.nodes.new('ShaderNodeNormalMap');normal.uv_map='TuaregAtlas'
    m.node_tree.links.new(texcoord.outputs['UV'],n.inputs['Vector']);m.node_tree.links.new(n.outputs['Color'],normal.inputs['Color']);m.node_tree.links.new(normal.outputs['Normal'],p.inputs['Normal'])
    obj.data.materials.clear();obj.data.materials.append(m)
    for poly in obj.data.polygons:poly.material_index=0
    for material,(out,p,target) in material_nodes.items():material.node_tree.nodes.remove(target)
    return m,paths
