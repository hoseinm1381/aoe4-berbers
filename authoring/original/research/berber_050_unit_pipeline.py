"""Source-preserving skinned unit geometry pilot for Berber 0.5.0.

This prepares private RRGeom sources; it does not cook, bind or package them.
Only the position, normal and tangent lanes of verified UnitDataStream
vertices can change. Native bones, skin indices/weights, UVs, topology,
LOD partition metadata and every other chunk remain byte-identical.

Usage:
    py -3.13 research/berber_050_unit_pipeline.py inspect MANIFEST
    py -3.13 research/berber_050_unit_pipeline.py remix RECIPE.json

The recipe names one freshly decoded stock manifest, its SHA-256, expected
logical source, explicit group selectors and measured shape features. Unknown
streams, ambiguous matches or unselected groups fail closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import struct
import sys
from pathlib import Path

from berber_050_common import ART, EXT, ROOT, read, sha, write

sys.path.insert(0, str(EXT.parent))
from garrison import relic_chunky as rc  # type: ignore


def project(vector):
    return (-vector[0], -vector[2], vector[1])


def native(vector):
    return (-vector[0], vector[2], -vector[1])


def source_geometry(manifest_path: Path, manifest: dict) -> Path:
    recorded = Path(manifest['geometry']['source']['path'])
    if recorded.is_file():
        return recorded
    logical = Path(str(manifest['request']['logical_path']).replace('\\', '/'))
    expected = manifest_path.parent / 'source' / logical.with_suffix('.rrgeom')
    if expected.is_file():
        return expected
    raise FileNotFoundError(f"Donor native RRGeom unavailable: {recorded}; fallback {expected}")


def _smooth01(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _window(x, start, full_start, full_end, end):
    if not start <= full_start <= full_end <= end:
        raise ValueError('A window needs start <= full_start <= full_end <= end')
    if x <= start or x >= end:
        return 0.0
    if x < full_start:
        return _smooth01((x - start) / max(full_start - start, 1e-8))
    if x > full_end:
        return _smooth01((end - x) / max(end - full_end, 1e-8))
    return 1.0


def _feature(point, feature):
    """A bounded local cloth/armor displacement, in native world metres."""
    x, y, z = point
    kind = feature['kind']
    z_weight = _window(z, *feature['z_window'])
    if not z_weight:
        return (0.0, 0.0, 0.0)
    # Optional selectors let an artist tailor a named garment region while
    # leaving the adjacent body, bow and equipment vertices in the same LOD.
    for coordinate, key in ((x, 'x_window'), (abs(x), 'abs_x_window'), (y, 'y_window')):
        if key in feature:
            z_weight *= _window(coordinate, *feature[key])
    if not z_weight:
        return (0.0, 0.0, 0.0)
    cx, cy = feature.get('center_xy', [0.0, 0.0])
    radius_x, radius_y = feature['radius_xy']
    if min(radius_x, radius_y) <= 0:
        raise ValueError('Feature radii must be positive')
    nx, ny = (x - cx) / radius_x, (y - cy) / radius_y
    radial = math.hypot(nx, ny)
    radial_weight = _window(radial, *feature.get('radial_window', [0.0, 0.1, 0.9, 1.5]))
    weight = z_weight * radial_weight
    if not weight:
        return (0.0, 0.0, 0.0)
    amount = float(feature['metres']) * weight
    if kind == 'radial_expand':
        length = math.hypot(x - cx, y - cy)
        if length < 1e-8:
            return (0.0, 0.0, 0.0)
        return (amount * (x - cx) / length, amount * (y - cy) / length, 0.0)
    if kind == 'lateral_expand':
        return (amount * (1 if x >= cx else -1), 0.0, 0.0)
    if kind == 'front_drape':
        # AoE/Garrison projection uses negative Y as front for the humanoid
        # donors inspected in the Tuareg fixture. Recipe authors must verify
        # orientation for each new animal and rider donor.
        return (0.0, -amount, 0.0)
    if kind == 'height':
        return (0.0, 0.0, amount)
    if kind == 'axis_shift':
        direction = _unit(tuple(float(v) for v in feature['direction']))
        return tuple(amount * v for v in direction)
    raise ValueError(f'Unknown feature kind: {kind}')


def shape(point, features):
    displacement = [0.0, 0.0, 0.0]
    for feature in features:
        delta = _feature(point, feature)
        for axis in range(3):
            displacement[axis] += delta[axis]
    return tuple(point[axis] + displacement[axis] for axis in range(3))


def _unit(vector):
    length = math.sqrt(sum(x*x for x in vector))
    return tuple(x/length for x in vector) if length > 1e-9 else (0.0, 0.0, 1.0)


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _normal_tangent(point, original, features, normal_lane):
    projected = project(tuple(v / 127 for v in original))
    epsilon = 0.001
    base = shape(point, features)
    columns = []
    for axis in range(3):
        probe = list(point)
        probe[axis] += epsilon
        target = shape(probe, features)
        columns.append(tuple((target[i]-base[i])/epsilon for i in range(3)))
    if normal_lane:
        cofactors = (_cross(columns[1],columns[2]), _cross(columns[2],columns[0]), _cross(columns[0],columns[1]))
        transformed = tuple(sum(projected[k]*cofactors[k][i] for k in range(3)) for i in range(3))
    else:
        transformed = tuple(sum(projected[k]*columns[k][i] for k in range(3)) for i in range(3))
    return tuple(max(-127, min(127, round(v*127))) for v in native(_unit(transformed)))


def _vertex_chunks(doc):
    chunks = []
    for chunk in rc.walk(doc.roots):
        if chunk.tag != b'GEOB' or len(chunk.payload) < 16:
            continue
        count, reserved_a, stride, reserved_b = struct.unpack_from('<4I', chunk.payload)
        if len(chunk.payload) != 16 + count*stride:
            raise ValueError(f'GEOB count/stride mismatch at {chunk.offset}')
        if stride == 28:
            chunks.append(chunk)
    return chunks


def _matches(chunk, group):
    count = len(group['positions'])
    n, a, stride, b = struct.unpack_from('<4I', chunk.payload)
    if (n, stride) != (count, 28):
        return False
    samples = (0, count//2, count-1)
    return all(tuple(project(struct.unpack_from('<4e',chunk.payload,16+28*i))) == tuple(group['positions'][i]) for i in samples)


def inspect(manifest_path: Path):
    manifest = read(manifest_path)
    source = source_geometry(manifest_path, manifest)
    raw = source.read_bytes()
    doc = rc.parse(raw)
    chunks = _vertex_chunks(doc)
    rows = []
    for index, group in enumerate(manifest['geometry']['groups']):
        rows.append({
            'index': index, 'name': group['name'], 'material': group.get('material'),
            'stream': group['stream'], 'vertex_count': len(group['positions']),
            'bounds': group.get('bounds'), 'skin_status': (group.get('skin_projection') or {}).get('status'),
            'rig_status': (group.get('rig_projection') or {}).get('status'),
            'matching_native_vertex_chunks': sum(_matches(c,group) for c in chunks) if group['stream']=='UnitDataStream' else 0,
        })
    return {
        'manifest': str(manifest_path), 'manifest_sha256': sha(manifest_path),
        'logical_path': manifest['request']['logical_path'],
        'geometry': str(source), 'geometry_sha256': sha(source),
        'skeleton_status': manifest.get('skeleton',{}).get('status'),
        'skeleton_bones': manifest.get('skeleton',{}).get('bone_count'),
        'groups': rows,
    }


def remix(recipe_path: Path):
    recipe = read(recipe_path)
    manifest_path = Path(recipe['manifest'])
    if sha(manifest_path) != recipe['manifest_sha256']:
        raise ValueError('Decoded donor manifest SHA-256 changed')
    manifest = read(manifest_path)
    if manifest['request']['logical_path'].replace('\\','/').lower() != recipe['logical_path'].replace('\\','/').lower():
        raise ValueError('Decoded donor identity differs from recipe')
    source = source_geometry(manifest_path, manifest)
    if sha(source) != recipe['geometry_sha256']:
        raise ValueError('Native donor geometry SHA-256 changed')
    original = source.read_bytes()
    doc = rc.parse(original)
    chunks = _vertex_chunks(doc)
    changed = {}
    selected = set()
    report = []
    for target in recipe['groups']:
        index = int(target['index'])
        if index in selected:
            raise ValueError(f'Duplicate group selection {index}')
        selected.add(index)
        group = manifest['geometry']['groups'][index]
        if group['stream'] != 'UnitDataStream':
            raise ValueError(f'Group {index} is not a skinned UnitDataStream')
        if (group.get('rig_projection') or {}).get('status') != 'decoded':
            raise ValueError(f'Group {index} lacks decoded native rig binding')
        if (group.get('skin_projection') or {}).get('status') != 'palette_indices_and_weights_decoded':
            raise ValueError(f'Group {index} lacks decoded skin channels')
        matches = [c for c in chunks if c.offset not in changed and _matches(c,group)]
        if len(matches) != 1:
            raise ValueError(f'Group {index} matches {len(matches)} native vertex streams')
        chunk = matches[0]
        buf = bytearray(chunk.payload)
        edits = 0
        max_displacement = 0.0
        clipped = 0
        bounds = group['bounds']
        lower, upper = bounds['minimum'], bounds['maximum']
        for vertex, position in enumerate(group['positions']):
            offset = 16 + vertex*28
            raw = struct.unpack_from('<4e',buf,offset)
            point = tuple(project(raw))
            if point != tuple(position):
                raise ValueError(f'Group {index} vertex {vertex} differs from decode')
            destination = shape(point,target['features'])
            if target.get('contain_within_donor_bounds',False):
                bounded = tuple(max(lower[axis],min(upper[axis],destination[axis])) for axis in range(3))
                clipped += bounded != destination
                destination = bounded
            delta = math.dist(point,destination)
            if delta < 1e-6:
                continue
            max_displacement = max(max_displacement,delta)
            if delta > float(target['max_displacement_metres']):
                raise ValueError(f'Group {index} vertex {vertex} exceeds displacement bound')
            buf[offset:offset+8] = struct.pack('<4e',*native(destination),raw[3])
            quantized = project(struct.unpack_from('<4e',buf,offset))
            if math.dist(quantized,destination) > 0.004:
                raise ValueError(f'Group {index} vertex {vertex} half-float quantization too large')
            if any(not math.isfinite(value) for value in quantized):
                raise ValueError(f'Group {index} vertex {vertex} is non-finite')
            if any(quantized[axis] < lower[axis]-0.00001 or quantized[axis] > upper[axis]+0.00001 for axis in range(3)):
                raise ValueError(f'Group {index} vertex {vertex} escapes donor native bounds; culling metadata would need review')
            for lane in (8,12):
                old = struct.unpack_from('<3b',chunk.payload,offset+lane)
                new = _normal_tangent(point,old,target['features'],normal_lane=lane==8)
                buf[offset+lane:offset+lane+3] = struct.pack('<3b',*new)
            if buf[offset+11:offset+12] != chunk.payload[offset+11:offset+12] or buf[offset+15:offset+28] != chunk.payload[offset+15:offset+28]:
                raise ValueError(f'Group {index} vertex {vertex} non-geometric lanes changed')
            edits += 1
        if not edits:
            raise ValueError(f'Group {index} received no visible geometry edit')
        if clipped/len(group['positions']) > float(target.get('max_clipped_fraction',0)):
            raise ValueError(f'Group {index} clipped {clipped} vertices beyond its allowed fraction')
        changed[chunk.offset] = bytes(buf)
        report.append({'index':index,'name':group['name'],'material':group.get('material'),
                       'vertex_count':len(group['positions']),'edited_vertices':edits,
                       'edited_fraction':round(edits/len(group['positions']),4),
                       'max_displacement_metres':round(max_displacement,5),
                       'clipped_to_native_bounds':clipped,
                       'within_original_native_bounds':True})
    result = rc.rebuild(doc,lambda chunk: changed.get(chunk.offset))
    if len(result) != len(original):
        raise ValueError('Native geometry size changed')
    check = rc.parse(result)
    for before,after in zip(rc.walk(doc.roots),rc.walk(check.roots)):
        if (before.tag,before.name,before.version)!=(after.tag,after.name,after.version):
            raise ValueError('Native chunk identity changed')
        if before.offset not in changed and not before.children and before.payload != after.payload:
            raise ValueError('Opaque native chunk changed')
    output_dir=Path(recipe.get('output_dir',ART / 'pilots' / recipe['name']))
    if not output_dir.is_absolute():
        output_dir=ROOT/output_dir
    output_dir=output_dir.resolve()
    if not output_dir.is_relative_to(ART.resolve()):
        raise ValueError(f'Authoring output must remain inside {ART}: {output_dir}')
    output = output_dir / (recipe['name']+'.rrgeom')
    if output.exists() and sha(output)!=hashlib.sha256(result).hexdigest():
        raise FileExistsError(f'Candidate differs from existing output: {output}')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(result)
    receipt = {'status':'geometry_prepared_no_cook','name':recipe['name'],'recipe':str(recipe_path),
               'recipe_sha256':sha(recipe_path),'source':str(source),'source_sha256':sha(source),
               'output':str(output),'output_sha256':sha(output),'groups':report,
               'preserved':'native skeleton, SKIN indices/weights, UVs, topology, LOD metadata, all non-position/normal/tangent bytes',
               'native_cook':'pending serial token','runtime':'unverified'}
    write(output.parent/'geometry-report.json',receipt)
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ('inspect','remix'):
        sub.add_parser(name).add_argument('path',type=Path)
    args=parser.parse_args()
    result=inspect(args.path) if args.command=='inspect' else remix(args.path)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
