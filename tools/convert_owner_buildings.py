"""Integrate cooked Tribal Tent shaders without replacing lifecycle records."""
import argparse
import json
from pathlib import Path
import struct

import numpy as np
from PIL import Image
from runtime import stock_game
from owner_color import (
    NATIVE,PREFIX,alter_mask,blocks,coverage,decode,encode,logical,mv,rc,sha,slots,store,surface,weights,
)

REL=Path('art/scenario/garrison/berber_tent_art_020/buildings')
OLD=rc.lp_string('object_collection')
NEW=rc.lp_string('structure_collection')


def geometry(raw):
    doc=rc.parse(raw)
    def replace(c):
        if c.tag!=b'GEOM':
            return None
        header=next(x for x in c.children if x.tag==b'GOHD')
        assert OLD+rc.lp_string('ObjectCollectionDataStream') in header.payload
        vh,vb,ih,ib=[x for x in c.children if x.tag in (b'GEOB',b'GEOC')]
        assert len(vh.payload)==2116
        meta=bytearray(vh.payload)
        # Exact stream declaration fields verified against all four real cooks.
        for pos,src,dst in ((972,16,20),(1552,30,13),(1556,0,4),(1560,0,16)):
            assert meta[pos:pos+4]==struct.pack('<I',src),(pos,meta[pos:pos+4])
            meta[pos:pos+4]=struct.pack('<I',dst)
        n,zero,stride,unknown=struct.unpack_from('<4I',vb.payload)
        assert stride==20 and len(vb.payload)==16+n*20
        v=np.frombuffer(vb.payload,np.uint8,offset=16).reshape(-1,20)
        buf=np.concatenate([v[:,:16],v[:,12:16],v[:,16:]],axis=1).tobytes()
        replacements={
            header.offset:header.payload.replace(OLD+rc.lp_string('ObjectCollectionDataStream'),
                    NEW+rc.lp_string('StructureCollectionPositionDataStream')),
            vh.offset:bytes(meta),vb.offset:struct.pack('<4I',n,zero,24,unknown)+buf,
        }
        return b''.join(rc.pack_chunk(x.kind,x.tag,replacements.get(x.offset,x.payload),
                    version=x.version,name=x.name) for x in c.children)
    return rc.rebuild(doc,replace)


def replace_effect(raw):
    doc=rc.parse(raw)
    [data]=[c.children[0] for c in rc.walk(doc.roots) if c.tag==b'MSCL']
    assert data.payload.count(OLD)==1
    return rc.rebuild(doc,lambda c:data.payload.replace(OLD,NEW) if c.offset==data.offset else None)


def make_texture(out,template,key,data):
    name=PREFIX+key+'_'+sha(data.tobytes())[:20]+'.rrtex'
    raw=encode(template,name,data)
    store(out,name,raw)
    return name,decode(raw)


def integrate(out,stem,cooked,template_stem,kind):
    old=NATIVE/stem
    old_geo=old.with_suffix('.rrgeom').read_bytes()
    generated=geometry(old_geo)
    old_rgm=old.with_suffix('.rgm').read_bytes()
    new_rgm=replace_effect(old_rgm)
    template_rrmat=template_stem.with_suffix('.rrmaterial').read_bytes()
    if cooked is not None:
        assert generated==cooked.with_suffix('.rrgeom').read_bytes(),stem
        a,b=(next(c.children[0].payload for c in rc.walk(rc.parse(x).roots) if c.tag==b'MSCL')
             for x in (new_rgm,cooked.with_suffix('.rgm').read_bytes()))
        assert a==b,stem
    geoms=[c for c in rc.walk(rc.parse(generated).roots) if c.tag==b'GEOM']
    areas=[surface(c,(24,)) for c in geoms]
    original_slots=dict(blocks(old.with_suffix('.rrmaterial').read_bytes()))
    basemap=slots(next(iter(original_slots.values())))['textures']
    albedo=logical(basemap['albedoTexture'])
    source=decode((NATIVE/albedo).read_bytes())
    tpl=(template_stem.parent/'mask.rrtex').read_bytes()
    authored=cooked is not None
    base=decode((cooked.parent/'mask.rrtex').read_bytes()) if authored else np.zeros((*source.shape[:2],4),np.uint8)
    red=np.zeros_like(base);red[:,:,0]=base[:,:,2]
    wt=weights(base.shape,areas)
    initial=coverage(red[:,:,0],wt)
    target=.18 if initial>.24 else max(.10,initial)
    dye=alter_mask(red,wt,target,source)
    if not authored:
        dye=alter_mask(red,wt,.12,source)
    base[:,:,2]=dye[:,:,0]
    mask,readback=make_texture(out,tpl,'building_mask',base)
    value=coverage(readback[:,:,2],wt)
    assert .05<=value<=.25,(stem,initial,value)
    # The team layer uses neutral source luminance, as in Chagatai's owner
    # cloth fix. Preserve the original atlas as the base layer.
    luminance=np.clip(source[:,:,:3].astype(float) @ np.array([.2126,.7152,.0722])*.68,18,140)
    neutral=source.copy()
    neutral[:,:,:3]=np.rint(luminance)[:,:,None].astype(np.uint8)
    dye_albedo,_=make_texture(out,tpl,'building_dye_albedo',neutral)
    templates=dict(blocks(template_rrmat))
    rewritten=[]
    for name,block in original_slots.items():
        is_collection=name.endswith('_collection')
        template_block=next(b for n,b in templates.items() if n.endswith('_collection')==is_collection)
        original=slots(block)['textures']
        editable=slots(template_block)
        maps={}
        for key,val in editable['textures'].items():
            if key=='__default':
                continue
            if key=='maskTex5':
                val=mask
            elif key=='albedoTex7':
                val=dye_albedo
            elif key.startswith('albedoTex'):
                val=albedo
            elif key.startswith('normalMap'):
                val=logical(original['normalMap'])
            elif key.startswith('metalTex'):
                val=logical(original['metalTex'])
            else:
                # Shared stock blank textures from the cooked template; store
                # each one under its exact baked reference path.
                path=logical(val)
                if path!='__default':
                    target=next(template_stem.parent.rglob(Path(path).name),None)
                    if target:
                        store(out,path,target.read_bytes())
            maps[key]=val.replace('/','\\')
        params={k:['0.5','0.5','0.5','1'] for k in editable['parameters']
                if k.startswith(('highlightColor','midtoneColor','shadowColor'))}
        params['options']=['64','0','0','8']
        for key in ('mask23LevelMinMax','mask45LevelMinMax','mask67LevelMinMax'):
            if key in editable['parameters']:
                params[key]=['0','1','0','1']
        raw=mv.rewrite_material(rc.pack_document([template_block]),maps,params)
        doc=rc.parse(raw)
        raw=rc.rebuild(doc,lambda c:rc.Rename(name.encode()+b'\0') if c.tag==b'GMat' else None)
        assert next(blocks(raw))[0]==name
        rewritten.append(next(blocks(raw))[1])
    for suffix,data in (('.rgm',new_rgm),('.rrgeom',generated),('.rrmaterial',rc.pack_document(rewritten))):
        store(out,stem.with_suffix(suffix).as_posix(),data)
    return {'model':stem.as_posix(),'family':kind,'old_shader':'object_collection',
            'new_shader':'structure_collection','coverage':round(value,4),'mask':mask,
            'initial_authored_mask_coverage':round(initial,4) if authored else None,
            'native_recook_geometry_equal':authored,'position_uv0_tangent_index_bytes_preserved':True,
            'selectors_and_rgo_preserved':True}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('work',type=Path)
    p.add_argument('--readback',type=Path,required=True)
    a=p.parse_args()
    rows=[]
    root=a.work/'overlay'
    template=a.readback/REL/'berber_tent_age1/model'
    for age in range(1,5):
        stem=REL/f'berber_tent_age{age}'/'model'
        rows.append(integrate(root,stem,a.readback/stem,a.readback/stem,'tribal tent'))
    # All additional object-collection landmarks use the same stream contract.
    for key in ('funduq_lod0','ribat_lod0','fez_lod0','grand_keep_lod0','koutoubia_lod0'):
        [geo]=list((NATIVE/'art').rglob(f'{key}/model.rrgeom'))
        stem=geo.with_suffix('').relative_to(NATIVE)
        try:
            rows.append(integrate(root,stem,None,template,key))
        except (AssertionError,ValueError) as exc:
            rows.append({'model':stem.as_posix(),'skipped':str(exc)})
    (a.work/'converted-buildings.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    for row in rows:
        print(row['model'],row.get('coverage'),row.get('skipped',''),flush=True)


if __name__=='__main__':
    main()
