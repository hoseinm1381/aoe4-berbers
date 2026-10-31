import bpy,sys,os,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'output/tuareg_refined_trial'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT.parent));import garrison;garrison.register()
from garrison import game_library
path=next((ROOT/'output/tuareg_shield_test/decoded/age1').rglob('decoded-static.json'))
p=bpy.data.objects.new('Reference',None);bpy.context.scene.collection.objects.link(p)
root=game_library._apply_decoded_static(p,json.loads(path.read_text()),select_result=False,create_controls=False)
mesh=next(o for o in root.children_recursive if o.type=='MESH' and 'lod1' in o.name)
mat=mesh.data.materials[0]
data={'material':mat.name,'properties':{k:str(mat[k]) for k in mat.keys()},'uvs':list(mesh.data.uv_layers.keys()),'nodes':[{'name':n.name,'type':n.bl_idname,'image':n.image.filepath if n.type=='TEX_IMAGE' and n.image else None,'inputs':[(s.name,str(s.default_value)) for s in n.inputs if hasattr(s,'default_value') and not s.is_linked]} for n in mat.node_tree.nodes]}
(WORK/'stock-material-inspection.json').write_text(json.dumps(data,indent=2));print('REFERENCE_INSPECTED',flush=True)
