"""Build and check private Berber owner masks against shipped mesh UVs."""
import argparse
from collections import defaultdict
from functools import lru_cache
from io import BytesIO
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import struct
import zlib

import numpy as np
from PIL import Image
from scipy import ndimage

from runtime import ROOT, stock_game
from garrison_shared import model_variants as mv, relic_chunky as rc, rrtex_decoder as rr

NATIVE = Path(os.environ.get('BERBER_COLOR_BASELINE', ROOT / 'inputs/native'))
PREFIX = 'art/scenario/berbers_owner_013/'
INDEX = Path.home() / 'AppData/Local/Garrison/Kit/game-assets.sqlite3'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def logical(path):
    return path.replace('\\', '/').lower()


def blocks(raw):
    doc = rc.parse(raw)
    for i, chunk in enumerate(doc.roots):
        end = doc.roots[i+1].offset if i+1 < len(doc.roots) else len(raw)
        yield chunk.decoded_name, raw[chunk.offset:end]


def slots(block):
    return mv.material_slots(rc.pack_document([block]))


def decode(raw):
    doc = rc.parse(raw)
    chunks = {c.tag: c for c in rc.walk(doc.roots)}
    manifest = chunks[b'TMAN'].payload
    stream = chunks[b'TDAT'].payload
    rr._validate_stream_table(manifest, stream)
    _, levels = rr._decode_mips(stream)
    fmt = struct.unpack_from('<I', manifest, 20)[0]
    levels.sort(key=lambda m: m.level)
    # Use the SDK's format detection and keep file-space orientation.
    dxgi, _ = rr._select_dxgi(fmt, chunks[b'TXTR'].decoded_name, levels[0])
    # Pillow reads BC3 via its UNORM enum; block decoding is identical for sRGB.
    return np.asarray(Image.open(BytesIO(rr._dds(levels, 77 if dxgi==78 else dxgi))).convert('RGBA')).copy()


def encode(template, name, rgba):
    # Native v6 BC3 stream, same contract used by Korea's art016 masks.
    levels = []
    image = Image.fromarray(rgba)
    while True:
        dds = BytesIO()
        image.save(dds, format='DDS', pixel_format='DXT5')
        w, h = image.size
        raw = dds.getvalue()
        assert raw[84:88] == b'DXT5' and len(raw[128:]) == ((w+3)//4)*((h+3)//4)*16
        levels.append(struct.pack('<4I', len(levels), w, h, len(raw)-128) + raw[128:])
        if (w,h) == (1,1):
            break
        size = (max(1,w//2), max(1,h//2))
        image = Image.merge('RGBA', tuple(c.resize(size, Image.Resampling.BOX) for c in image.split()))
    data = bytearray(struct.pack('<I',6))
    counts, sizes = [], []
    for level in reversed(levels):
        chunks = [level[i:i+65536] for i in range(0,len(level),65536)]
        counts.append(len(chunks))
        for c in chunks:
            packed = zlib.compress(c, 9)
            packed = packed if len(packed) < len(c) else c
            data.extend(packed)
            sizes.append(struct.pack('<2I',len(c),len(packed)))
    h,w = rgba.shape[:2]
    manifest = (struct.pack('<8IBII',6,w,h,1,2,22,len(levels),2,0,1,len(levels))
                + struct.pack('<'+'I'*len(counts),*counts) + b''.join(sizes))
    rr._validate_stream_table(manifest, bytes(data))
    result = rc.rebuild(rc.parse(template), lambda c: manifest if c.tag==b'TMAN' else
                        bytes(data) if c.tag==b'TDAT' else
                        rc.Rename(name.removesuffix('.rrtex').replace('/','\\').encode()+b'\0') if c.tag==b'TXTR' else None)
    return result


class Textures:
    def __init__(self):
        self.game = stock_game.current()
        self.db = sqlite3.connect('file:'+INDEX.as_posix()+'?mode=ro',uri=True)

    @lru_cache(maxsize=32)
    def raw(self, path):
        local = NATIVE / path
        if local.is_file():
            return local.read_bytes()
        record = self.db.execute('select archive_path,logical_path from resolved_assets where logical_path=?',
                                 (path,)).fetchone()
        if not record:
            raise ValueError('Missing texture: '+path)
        return self.game.member(*record)

    @lru_cache(maxsize=24)
    def image(self, path):
        return decode(self.raw(path))


def surface(geom, stride_choices=(28,)):
    vertex,index = [c.payload for c in geom.children if c.tag==b'GEOB'][:2]
    n,_,stride,_ = struct.unpack_from('<4I',vertex)
    count,_,isize,_ = struct.unpack_from('<4I',index)
    assert stride in stride_choices and isize in (2,4) and len(vertex)==16+n*stride
    xyz = np.ndarray((n,3),'<f2',vertex,16,(stride,2)).astype(np.float32)
    uv = np.ndarray((n,2),'<f2',vertex,28,(stride,2)).astype(np.float32)
    faces = np.frombuffer(index, '<u'+str(isize), count, offset=16).reshape(-1,3)
    p = xyz[faces]
    area = np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)/2
    assert np.isfinite(area).all() and np.isfinite(uv).all()
    bary = np.array([[1/3,1/3,1/3],[.6,.2,.2],[.2,.6,.2],[.2,.2,.6]])
    return np.einsum('sa,fad->fsd',bary,uv[faces]).reshape(-1,2), np.repeat(area/4,4)


def weights(shape, parts):
    h,w = shape[:2]
    out = np.zeros(w*h)
    for uv, area in parts:
        x = (np.floor(uv[:,0]*w).astype('int64'))%w
        y = (np.floor(uv[:,1]*h).astype('int64'))%h
        out += np.bincount(y*w+x,weights=area,minlength=w*h)
    return out.reshape(h,w)


def coverage(red, weight):
    return float(weight[red>=128].sum()/weight.sum()) if weight.sum() else 0.


def alter_mask(rgba, wt, desired, albedo=None):
    """Move the outline of existing dye regions; protect native skin/hair."""
    result = rgba.copy()
    red = rgba[:,:,0]
    seeds = red >= 128
    protected = np.maximum(rgba[:,:,1], rgba[:,:,2]) > 32
    before = coverage(red,wt)
    if before >= desired:
        if before > desired:
            depth = ndimage.distance_transform_edt(seeds)
            ix = np.flatnonzero(seeds & (wt>0))
            order = ix[np.argsort(-depth.ravel()[ix],kind='stable')]
            n = np.searchsorted(np.cumsum(wt.ravel()[order]), desired*wt.sum())
            cutoff = depth.ravel()[order[min(n,order.size-1)]]
            result[:,:,0][seeds & (depth < cutoff)] = 0
        return result
    if seeds.any():
        # Weighted expansion from the nearest existing dye, with a color edge cost
        # to favor other texels on the same garment or equipment material.
        distance, idx = ndimage.distance_transform_edt(~seeds, return_indices=True)
        score = distance
        if albedo is not None:
            color = np.asarray(Image.fromarray(albedo[:,:,:3]).resize(red.shape[::-1])).astype(np.float32)
            contrast = np.linalg.norm(color - color[tuple(idx)], axis=2)
            score *= (1+contrast/70)
    else:
        # No donor dye: select a coherent patch of the dominant saturated cloth.
        if albedo is None:
            return result
        color = np.asarray(Image.fromarray(albedo[:,:,:3]).resize(red.shape[::-1])).astype(np.float32)
        saturation = color.max(2)-color.min(2)
        weighted = (wt>0) & ~protected
        if not weighted.any():
            return result
        seed = np.unravel_index(np.argmax(np.where(weighted, saturation, -1)), red.shape)
        yy,xx = np.ogrid[:red.shape[0],:red.shape[1]]
        score = np.hypot(yy-seed[0],xx-seed[1]) * (1+np.linalg.norm(color-color[seed],axis=2)/70)
    eligible = ~protected & ~seeds & (wt>0)
    ix = np.flatnonzero(eligible)
    order = ix[np.argsort(score.ravel()[ix],kind='stable')]
    n = np.searchsorted(np.cumsum(wt.ravel()[order]), (desired-before)*wt.sum())
    if order.size:
        cutoff = score.ravel()[order[min(n,order.size-1)]]
        selected = (score<=cutoff) & ~protected
        result[:,:,0][selected] = 255
    return result


def store(out, name, raw):
    p=out/name
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists() and p.read_bytes()!=raw:
        raise ValueError('Unexpected output collision: '+name)
    p.write_bytes(raw)


def unit(out, mat, textures, apply):
    raw = mat.read_bytes()
    name = mat.relative_to(NATIVE).as_posix()
    parts = defaultdict(list)
    lods = defaultdict(list)
    for mesh in (c for c in rc.walk(rc.parse(mat.with_suffix('.rrgeom').read_bytes()).roots) if c.tag==b'MESH'):
        for level,lod in enumerate(c for c in mesh.children if c.tag==b'LOD '):
            for geom in (c for c in lod.children if c.tag==b'GEOM'):
                header = next(c.payload for c in geom.children if c.tag==b'GOHD')
                _,i = rc.read_lp_string(header,0)
                material,i = rc.read_lp_string(header,i)
                effect,_ = rc.read_lp_string(header,i)
                if effect != 'unit':
                    continue
                sample = surface(geom)
                parts[material].append(sample)
                lods[level].append((material,sample))
    groups=defaultdict(list)
    for material, block in blocks(raw):
        t=slots(block)['textures']
        if material in parts and 'patternTex' in t:
            groups[(logical(t['patternTex']),logical(t['albedoTexture']))].append(material)
    output={}
    after={}
    before={}
    measurements=[]
    for (pattern,albedo), materials in groups.items():
        if pattern == '__default':
            continue
        mask = textures.image(pattern)
        wt = weights(mask.shape, [s for m in materials for s in parts[m]])
        cv = coverage(mask[:,:,0],wt)
        for m in materials:
            before[m] = mask[:,:,0]
            after[m] = mask[:,:,0]
        measurements.append({'slots':materials,'pattern':pattern,'coverage':round(cv,4)})
    def measure(red):
        res=[]
        for level, rows in sorted(lods.items()):
            total=sum(sample[1].sum() for _,sample in rows)
            colored=0.
            for m,sample in rows:
                if m in red:
                    w=weights(red[m].shape,[sample]); colored+=w[red[m]>=128].sum()
            res.append(round(float(colored/total),4) if total else 0.)
        return res
    original = measure(before)
    if apply and original and (min(original)<.102 or max(original)>.49):
        for (pattern,albedo),materials in groups.items():
            if pattern == '__default':
                continue
            mask = textures.image(pattern)
            wt = weights(mask.shape, [s for m in materials for s in parts[m]])
            cv = coverage(mask[:,:,0],wt)
            # Keep horse/camel skin and cart hardware stock. Expand rider cloth first.
            primary=any(not any(word in m.lower() for word in ('horse','camel','cart','gold','tack'))
                        for m in materials)
            reduce = max(original)>.49 and cv>.43
            if not reduce and (not primary or cv >= .49):
                continue
            desired=.40 if reduce else min(.66, max(.15,cv+(.155-min(original))*sum(s[1].sum() for rows in lods.values() for _,s in rows)/max(1.,wt.sum())))
            if cv==0 and not any('rider' in m.lower() for m in materials) and len(groups)>1:
                continue
            adjusted=alter_mask(mask,wt,desired,textures.image(albedo))
            assert np.array_equal(adjusted[:,:,1:],mask[:,:,1:])
            if np.array_equal(adjusted,mask):
                continue
            path=PREFIX+sha(adjusted.tobytes())[:24]+'.rrtex'
            encoded=encode(textures.raw(pattern),path,adjusted)
            readback=decode(encoded)
            if (coverage(readback[:,:,0],wt)>cv)==reduce:
                continue
            store(out,path,encoded)
            for m in materials:
                output[m]=path
                after[m]=readback[:,:,0]
    if output:
        rewritten=[]
        for material,block in blocks(raw):
            if material in output:
                one=mv.rewrite_material(rc.pack_document([block]),{'patternTex':output[material].replace('/','\\')},{})
                newblock=next(blocks(one))[1]
                a,b=slots(block),slots(newblock)
                assert a['parameters']==b['parameters']
                assert {k:v for k,v in a['textures'].items() if k!='patternTex'}=={k:v for k,v in b['textures'].items() if k!='patternTex'}
                rewritten.append(newblock)
            else:
                rewritten.append(block)
        store(out,name,rc.pack_document(rewritten))
    return dict(model=name,baseline=original,updated=measure(after),changed=output,slots=measurements)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('out',type=Path)
    p.add_argument('--apply',action='store_true')
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    textures=Textures()
    root=NATIVE/'art/scenario/garrison'
    paths=sorted((*root.glob('berber_units_050/*/*.rrmaterial'),*root.glob('tuareg_refined_art/units/*/body/*.rrmaterial')))
    records=[]
    for mat in paths:
        try:
            row=unit(a.out/'overlay',mat,textures,a.apply)
        except (ValueError,AssertionError) as exc:
            row={'model':mat.relative_to(NATIVE).as_posix(),'error':str(exc)}
        records.append(row)
        print(mat.parent.name,row.get('baseline'),row.get('updated'),row.get('error',''),flush=True)
    (a.out/'units.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
