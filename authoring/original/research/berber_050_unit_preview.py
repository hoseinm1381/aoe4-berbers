"""Matched native-geometry projections for private Berber 0.5.0 pilots.

These are source review images, not Blender or in-game screenshots.
"""
from __future__ import annotations

import argparse
import math
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from berber_050_common import read
from berber_050_unit_pipeline import _matches, _vertex_chunks, project, rc, source_geometry


def _points(raw, group):
    chunks=_vertex_chunks(rc.parse(raw))
    matches=[c for c in chunks if _matches(c,group)]
    if len(matches)!=1:
        # The remixed stream no longer has stock positions. Match its unique
        # 28-byte vertex count in the same source group order instead.
        matches=[c for c in chunks if struct.unpack_from('<4I',c.payload)==(len(group['positions']),0,28,0)]
    if len(matches)!=1:
        raise ValueError(f"Cannot identify unique native stream for {group['name']} {group['material']}")
    c=matches[0]
    return [project(struct.unpack_from('<4e',c.payload,16+i*28))[:3] for i in range(len(group['positions']))]


def _project(point,angle,scale,origin):
    x,y,z=point
    s,c=math.sin(angle),math.cos(angle)
    horizontal=x*c+y*s
    depth=-x*s+y*c
    return (origin[0]+horizontal*scale,origin[1]-z*scale,depth)


def _panel(group,points,angle,width,height,title):
    image=Image.new('RGB',(width,height),(239,234,222))
    draw=ImageDraw.Draw(image)
    extent=group['bounds']['extent']
    scale=min((width-70)/max(extent[0],extent[1]),(height-95)/extent[2])
    origin=(width/2,height-42)
    projected=[_project(p,angle,scale,origin) for p in points]
    triangles=[]
    for tri in group['triangles']:
        if len(tri)!=3:
            continue
        p=[projected[i] for i in tri]
        if abs((p[1][0]-p[0][0])*(p[2][1]-p[0][1])-(p[2][0]-p[0][0])*(p[1][1]-p[0][1]))<0.05:
            continue
        triangles.append((sum(q[2] for q in p)/3,p))
    for depth,p in sorted(triangles,key=lambda row:row[0],reverse=True):
        cross=(p[1][0]-p[0][0])*(p[2][1]-p[0][1])-(p[2][0]-p[0][0])*(p[1][1]-p[0][1])
        colour=(75,68,57) if cross>0 else (101,92,75)
        draw.polygon([(q[0],q[1]) for q in p],fill=colour)
    draw.text((18,15),title,fill=(20,20,20))
    draw.text((18,height-25),'Native LOD1 geometry projection | no material or animation',fill=(55,55,55))
    return image


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recipe',type=Path)
    args=parser.parse_args()
    recipe=read(args.recipe)
    manifest=read(recipe['manifest'])
    group=manifest['geometry']['groups'][0]
    source=source_geometry(Path(recipe['manifest']),manifest).read_bytes()
    candidate=(args.recipe.parent/(recipe['name']+'.rrgeom')).read_bytes()
    stock_points=_points(source,group)
    new_points=_points(candidate,group)
    for name,angle in [('front',0),('three_quarter',math.pi/4),('side',math.pi/2)]:
        left=_panel(group,stock_points,angle,650,850,'Official native donor | '+name)
        right=_panel(group,new_points,angle,650,850,'Berber geometry candidate | '+name)
        spread=Image.new('RGB',(1300,850))
        spread.paste(left,(0,0));spread.paste(right,(650,0))
        path=args.recipe.parent/f'geometry-preview-{name}.png'
        spread.save(path)
        print(path)


if __name__=='__main__':
    main()
