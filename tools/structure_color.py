"""Extend the existing native structure team layers; keep meshes and selectors."""
import argparse
from collections import defaultdict
import json
import re
import struct

import numpy as np

from owner_color import (
    ROOT,NATIVE,PREFIX,Textures,alter_mask,blocks,coverage,decode,encode,
    logical,mv,rc,sha,slots,store,surface,weights,
)


TEAM_ALBEDOS={'6708399669590286008_packed.rrtex','4043818863494013394_packed.rrtex'}


def donor_groups(mat, directory):
    geometries = [g for g in rc.walk(rc.parse(mat.with_suffix('.rrgeom').read_bytes()).roots) if g.tag==b'GEOM']
    rgm=rc.parse(mat.with_suffix('.rgm').read_bytes())
    collection=[c.children[0].payload for c in rc.walk(rgm.roots) if c.tag==b'MSCL']
    if len(collection)==1:
        raw=collection[0]
        effect=raw.rfind(rc.lp_string('structure_collection'))
        if effect>=8 and raw[effect-4:effect]==struct.pack('<I',1):
            names=[m for m,_ in blocks(mat.read_bytes()) if m.endswith('_collection')]
            pattern=b'|'.join(re.escape(rc.lp_string(n)) for n in names)
            if pattern:
                span_matches=[]
                for match in re.finditer(b'(?:'+pattern+b')+',raw[:effect-4]):
                    start,end=match.span()
                    if start<4:
                        continue
                    count=struct.unpack_from('<I',raw,start-4)[0]
                    if count==0 or count>len(names) or end+count*4!=effect-4:
                        continue
                    cursor=start
                    parsed=[]
                    for _ in range(count):
                        name,cursor=rc.read_lp_string(raw,cursor)
                        parsed.append(name)
                    if cursor!=end or not set(parsed)<=set(names):
                        continue
                    spans=struct.unpack_from('<'+'I'*count,raw,end)
                    if sum(spans)==len(geometries):
                        span_matches.append([n.removesuffix('_collection') for n,s in zip(parsed,spans) for _ in range(s)])
                if len(span_matches)==1:
                    return None,[(n,surface(g,(24,))) for n,g in zip(span_matches[0],geometries,strict=True)]
    if mat.stem.startswith('market_'):
        age=int(mat.stem[-2:])
        pattern=f'Berber_market_age{age:02}_0_3_1-projection.json'
    elif mat.stem=='mill_windmill':
        pattern='windmill/remix-projection.json'
    else:
        pattern=mat.stem+'*projection.json'
    files=[p for p in directory.rglob('*.json') if p.match(pattern)]
    for f in files:
        rows=json.loads(f.read_bytes())['geometry']['groups']
        if len(rows)!=len(geometries):
            continue
        good=True
        for row,g in zip(rows,geometries,strict=True):
            v,i=[x.payload for x in g.children if x.tag==b'GEOB']
            # The stock-derived projections retain the same native UV/index layout.
            n=row['vertex_count']
            stride=row['vertex_stride']
            if stride!=24 or len(v)!=16+n*stride or len(i)!=16+row['triangle_count']*3*row['index_stride']:
                good=False;break
            uv=np.ndarray((n,2),'<f2',v,28,(stride,2)).astype(np.float32)
            expected=np.array(row['uv_layers']['UVMap'])
            if not (np.array_equal(expected[:,0],uv[:,0]) and np.array_equal(expected[:,1],1.-uv[:,1])):
                good=False;break
            native=np.frombuffer(i,'<u'+str(row['index_stride']),offset=16).reshape(-1,3)
            projected=np.asarray(row['triangles'])
            if not np.array_equal(np.sort(native,axis=1),np.sort(projected,axis=1)):
                good=False;break
        if good:
            return f,[(r['preview_material'],surface(g,(24,))) for r,g in zip(rows,geometries,strict=True)]
    raise ValueError('No matching structure projection')


def team_slot(t, params):
    opt=params.get('options',{}).get('values',['0'])
    bits=int(float(opt[0]))
    for layer in (5,6,7):
        if (bits & (1<<(layer-1)) and logical(t.get('albedoTex'+str(layer),'')).split('/')[-1] in TEAM_ALBEDOS
                and t.get('maskTex5') not in ('','__default',None)):
            return layer-5,logical(t['maskTex5'])
    return None


def building(out,mat,tx,projections,apply):
    name=mat.relative_to(NATIVE).as_posix()
    raw=mat.read_bytes()
    material_blocks=dict(blocks(raw))
    entries={m:slots(b) for m,b in material_blocks.items()}
    active={m:pair for m,e in entries.items() if not m.endswith('_collection')
            if (pair:=team_slot(e['textures'],e['parameters']))}
    if not active:
        raise ValueError('No verified stock team layer 5–7')
    projection,groups=donor_groups(mat,projections)
    data=defaultdict(list)
    for material,group in groups:
        data[material].append(group)
    total=sum(float(p[1].sum()) for _,p in groups)
    result={}
    proposals=[]
    for m,(chan,mask_path) in active.items():
        if m not in data:
            continue
        image=tx.image(mask_path)
        wt=weights(image.shape,data[m])
        cv=coverage(image[:,:,chan],wt)
        proposals.append((m,chan,mask_path,float(wt.sum()),cv))
    orig=sum(row[3]*row[4] for row in proposals)/total
    achieved=orig
    if apply and not .075<=orig<=.22:
        # Only move existing owner patterns. Process the largest confirmed dye
        # materials first and keep the changes close to the authored outline.
        for m,ch,path,area,cv in sorted(proposals,key=lambda p:p[3]*p[4],reverse=True):
            if .075<=achieved<=.22:
                break
            if area==0:
                continue
            origmask=tx.image(path)
            wt=weights(origmask.shape,data[m])
            dye=np.zeros_like(origmask);dye[:,:,0]=origmask[:,:,ch]
            goal=np.clip(cv+(.105-achieved)*total/area,.0,.75)
            paint=alter_mask(dye,wt,goal)
            dst=origmask.copy()
            dst[:,:,ch]=paint[:,:,0]
            key=PREFIX+'structure_'+sha(dst.tobytes())[:20]+'.rrtex'
            encoded=encode(tx.raw(path),key,dst)
            decoded=decode(encoded)
            new=coverage(decoded[:,:,ch],wt)
            if abs(.105-(achieved+(new-cv)*area/total))>=abs(.105-achieved):
                continue
            paired=m+'_collection'
            if paired in entries and team_slot(entries[paired]['textures'],entries[paired]['parameters'])!=(ch,path):
                continue
            store(out,key,encoded)
            for target in (m,paired):
                if target in material_blocks:
                    newmat=mv.rewrite_material(rc.pack_document([material_blocks[target]]),{'maskTex5':key.replace('/','\\')},{})
                    result[target]=next(blocks(newmat))[1]
            achieved+=(new-cv)*area/total
    if result:
        store(out,name,rc.pack_document([result.get(m,b) for m,b in material_blocks.items()]))
    return dict(model=name,projection=projection.relative_to(ROOT).as_posix() if projection else 'native RGM collection table',
                baseline=round(orig,4),updated=round(achieved,4),changed=list(result),
                sample='all decoded collection surfaces, including dormant states')


def main():
    from pathlib import Path
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('out',type=Path)
    p.add_argument('--apply',action='store_true')
    a=p.parse_args()
    tx=Textures()
    rows=[]
    root=NATIVE/'art/scenario/garrison'
    for mat in sorted(root.rglob('*.rrmaterial')):
        if not mat.with_suffix('.rrgeom').exists() or any(x in mat.parts for x in ('berber_units_050','tuareg_refined_art')):
            continue
        try:
            row=building(a.out/'overlay',mat,tx,ROOT/'authoring/original/art',a.apply)
        except (AssertionError,ValueError,KeyError) as exc:
            row=dict(model=mat.relative_to(NATIVE).as_posix(),skipped=str(exc))
        rows.append(row)
        print(mat.parent.name,row.get('baseline'),row.get('updated'),row.get('skipped',''),flush=True)
    (a.out/'structures.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
