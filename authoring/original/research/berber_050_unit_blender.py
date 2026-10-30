"""Build a private textured donor/candidate Blender review file from native data.

Run in a separate Blender process, never in the user's open session. This is
authoring review only: no native cook, package, import or runtime claim.
"""
from __future__ import annotations

import json
import os
import re
import struct
import sys
from pathlib import Path

import bpy

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT.parent))
import garrison
garrison.register()
from garrison import game_library
from berber_050_unit_pipeline import _vertex_chunks, project, rc


def _positions(raw,groups):
    chunks=_vertex_chunks(rc.parse(raw))
    used=set()
    output=[]
    for group in groups:
        matches=[]
        for c in chunks:
            if c.offset in used:
                continue
            if struct.unpack_from('<4I',c.payload)==(len(group['positions']),0,28,0):
                matches.append(c)
        if len(matches)!=1:
            raise ValueError(f"Cannot map LOD native stream: {group['name']} {group['material']} ({len(matches)})")
        c=matches[0];used.add(c.offset)
        output.append([list(project(struct.unpack_from('<4e',c.payload,16+i*28))[:3]) for i in range(len(group['positions']))])
    return output


def _place(label,manifest,offset):
    root=bpy.data.objects.new(label,None)
    bpy.context.scene.collection.objects.link(root)
    result=game_library._apply_decoded_static(root,manifest,select_result=False,create_controls=False)
    result.name=label
    result.location.x=offset
    return result


def main():
    args=sys.argv[sys.argv.index('--')+1:]
    recipe_path=Path(args[0]).resolve()
    recipe=json.loads(recipe_path.read_text(encoding='utf8'))
    manifest_path=Path(recipe['manifest']).resolve()
    source=json.loads(manifest_path.read_text(encoding='utf8'))
    candidate=json.loads(manifest_path.read_text(encoding='utf8'))
    raw=(recipe_path.parent/(recipe['name']+'.rrgeom')).read_bytes()
    for group,positions in zip(candidate['geometry']['groups'],_positions(raw,candidate['geometry']['groups'])):
        group['positions']=positions
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj,do_unlink=True)
    scene=bpy.context.scene
    scene.name=f"{recipe['name']} donor and candidate"
    scene.garrison.asset_library_root=str(ROOT/'art/unit_remix_0_5_0/garrison-library')
    scene.garrison.game_asset_connection=str(Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/game-assets.local.json')
    scene.garrison.game_asset_index=str(Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/game-assets.sqlite3')
    donor=_place('Official donor textured',source,-1.4)
    art=_place('Berber candidate textured',candidate,1.4)
    preview_albedos=recipe.get('preview_albedos')
    if preview_albedos is None:
        palette=recipe_path.parent/recipe.get('preview_albedo','indigo-underrobe-albedo.png')
        preview_albedos={recipe.get('donor_albedo_texture_id','4030391217154354827'):str(palette)} if palette.is_file() else {}
    if preview_albedos:
        replacements={}
        for texture_id,value in preview_albedos.items():
            palette=Path(value)
            if not palette.is_absolute():
                palette=recipe_path.parent/palette
            if not palette.is_file():
                raise FileNotFoundError(f'Preview albedo missing: {palette}')
            replacements[texture_id]=bpy.data.images.load(str(palette),check_existing=True)
        replaced={key:0 for key in replacements}
        for obj in art.children_recursive:
            if obj.type!='MESH':
                continue
            for slot in obj.material_slots:
                if not slot.material:
                    continue
                material=slot.material.copy()
                slot.material=material
                for node in material.node_tree.nodes if material.use_nodes else []:
                    if node.type=='TEX_IMAGE' and node.image:
                        for texture_id,replacement in replacements.items():
                            if texture_id in node.image.name:
                                node.image=replacement
                                replaced[texture_id]+=1
                                break
        missing=[key for key,count in replaced.items() if not count]
        if missing:
            raise ValueError(f'Candidate albedo slots not found in decoded Blender material: {missing}')
    for obj in [donor,*donor.children_recursive,art,*art.children_recursive]:
        show=obj.type!='MESH' or re.search(r'lod[ _]?1(?:\.|$)',obj.name,re.IGNORECASE) is not None
        obj.hide_set(not show)
        obj.hide_render=not show
    output=recipe_path.parent/(recipe['name']+'.blend')
    bpy.ops.file.pack_all()
    unpacked=[image.name for image in bpy.data.images if image.source=='FILE' and not image.packed_file]
    if unpacked:
        raise ValueError(f'External texture dependency remains: {unpacked}')
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    report={'status':'saved_source_review_only','blend':str(output),'textures':'packed','donor':str(manifest_path),'candidate_rrgeom':str(recipe_path.parent/(recipe['name']+'.rrgeom')),'native_cook':'pending','native_match':'unverified'}
    (recipe_path.parent/'blender-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('BERBER_050_PRIVATE_BLEND_SAVED',output,flush=True)


if __name__=='__main__':
    main()
