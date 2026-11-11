"""Isolated native structure-shader cook for the original Berber tent meshes."""
import argparse
from copy import deepcopy
import os
import re
import shutil
import subprocess
import sys
import types
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image
from runtime import EXT,ROOT
from owner_color import NATIVE, blocks, decode, logical, rc, slots

REL='art/scenario/garrison/berber_tent_art_020/buildings'
ORIGINAL=ROOT/'authoring/retained-legacy-art/tribal_tent/garrison_library_0_2_1/Mods/berber_tent_art_020/project'
MASKS=ROOT/'authoring/retained-legacy-art/buildings_shared/player_colour/tent_masks'
DONOR=next(NATIVE.rglob('barracks_age1.rrmaterial'))


def add_uv2(path, scripts):
    # Duplicate only the UV layer, preserving native FBX object/selector IDs.
    pkg=types.ModuleType('_berber_fbx')
    pkg.__path__=[str(scripts)]
    sys.modules[pkg.__name__]=pkg
    from _berber_fbx import parse_fbx,encode_bin
    tree,version=parse_fbx.parse(str(path))
    method=dict(zip('ZYBCIFDLRSifdlbc',(
        'int8','int16','bool','char','int32','float32','float64','int64','bytes','string',
        'int32_array','float32_array','float64_array','int64_array','bool_array','byte_array'),strict=True))
    def clone(node):
        result=encode_bin.FBXElem(node.id)
        for value,kind in zip(node.props,node.props_type,strict=True):
            getattr(result,'add_'+method[chr(kind)])(value)
        result.elems.extend(clone(child) for child in node.elems)
        return result
    root=clone(tree)
    objects=next(n for n in root.elems if n.id==b'Objects')
    def element(id, value=None, kind=None):
        n=encode_bin.FBXElem(id)
        if kind:
            getattr(n,'add_'+kind)(value)
        return n
    for geometry in (n for n in objects.elems if n.id==b'Geometry'):
        [old]=[n for n in geometry.elems if n.id==b'LayerElementUV']
        new=element(b'LayerElementUV',1,'int32')
        new.elems=[element(b'Name',b'UV2','string') if n.id==b'Name' else deepcopy(n) for n in old.elems]
        geometry.elems.append(new)
        layer=element(b'Layer',1,'int32')
        ref=element(b'LayerElement')
        ref.elems=[element(b'Type',b'LayerElementUV','string'),element(b'TypedIndex',1,'int32')]
        layer.elems=[element(b'Version',100,'int32'),ref]
        geometry.elems.append(layer)
    encode_bin.write(str(path),root,version)


def main():
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('out',type=Path)
    parser.add_argument('--fbx-sdk',type=Path,default=Path(os.environ.get('BERBER_BLENDER_FBX_SDK','E:/Blender5.2/5.2/scripts/addons_core/io_scene_fbx')))
    a=parser.parse_args()
    dest=a.out/'project'
    shutil.copytree(ORIGINAL,dest)
    source=dest/'source'
    # Start with the exact authored mesh and stage selection source. Regenerate
    # the missing original albedo PNG from the shipped native texture.
    for age in range(1,5):
        folder=source/REL/f'berber_tent_age{age}'
        add_uv2(folder/'model.fbx',a.fbx_sdk)
        native=NATIVE/folder.relative_to(source)
        current=dict(blocks((native/'model.rrmaterial').read_bytes()))
        p=logical(slots(next(iter(current.values())))['textures']['albedoTexture'])
        pixels=decode((NATIVE/p).read_bytes())[::-1].copy()
        Image.fromarray(pixels).save(folder/'albedo.png')
        mask=np.asarray(Image.open(MASKS/f'tent_age{age}_pattern.png').convert('RGB')).copy()
        blue=np.zeros_like(mask);blue[:,:,2]=mask[:,:,0]
        Image.fromarray(blue).save(folder/'mask.png')
        Image.new('RGB',(4,4)).save(folder/'black.png')
        Image.new('RGB',(4,4),'white').save(folder/'white.png')
        mat=ET.Element('materialSet')
        block=ET.SubElement(mat,'material',name=next(iter(current)),type='shader',source='structure')
        d=dict(blocks(DONOR.read_bytes()))['main']
        for key in slots(d)['textures']:
            if key=='__default':
                continue
            if key=='maskTex5': image='mask'
            elif key=='maskAlpha': image='white'
            elif key.startswith('albedoTex'): image='albedo'
            elif key.startswith('normalMap'): image='normal'
            elif key.startswith('metalTex'): image='metalness'
            else: image='black'
            ET.SubElement(block,'param',name=key,type='tex2D',value=str((folder/(image+'.png')).relative_to(source)))
        ET.SubElement(block,'param',name='roughnessTex',type='tex2D',value=str((folder/'roughness.png').relative_to(source)))
        ET.ElementTree(mat).write(folder/'model.material',encoding='utf-8',xml_declaration=True)
    burn=source/'_default.burnproj'
    text=burn.read_text(encoding='utf-8-sig')
    # Reuse the same native model/material/texture/RGO scopes. Non-art entries
    # are outside this isolated pilot.
    text=re.sub(r'<BurnRule>.*?</BurnRule>',lambda m:m[0] if 'berber_tent_age' in m[0] else m[0].replace('<IsEnabled>true','<IsEnabled>false'),text,flags=re.S)
    burn.write_text(text,encoding='utf-8')
    editor=Path.home()/'AppData/Local/Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe'
    core=EXT/'bin/core/garrison-core.exe'
    with (a.out/'cook.log').open('w') as log:
        subprocess.run([core,'essence','build-mod','--editor',editor,'--mod',next(dest.glob('*.aoe4mod')),
                        '--run-root',a.out/'run','--timeout','110','--console-burn-log'],stdout=log,stderr=subprocess.STDOUT,check=True)


if __name__=='__main__':
    main()
