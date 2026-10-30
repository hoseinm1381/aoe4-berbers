"""Rebuild all Berber music from retained originals; never modify source audio.

MP3 inputs necessarily receive one new lossy generation after PCM rotation.
No intermediate MP3 is ever used as an encoding input. FFprobe is not required.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess

RATE = 48000
FRAME_BYTES = 4
SKIP = 10 * RATE
CODES = ('da', 'fa', 'ca', 'ia')
AGES = ('Dark Age', 'Feudal Age', 'Castle Age', 'Imperial Age')
RECIPE = 'berber100-stereo48k-s16-rotate-v1-no-tags'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8')


def rotate_pcm(pcm, entry, skip=SKIP):
    """Remove [0,skip), then cyclically rotate the full surviving frame range."""
    if len(pcm) % FRAME_BYTES:
        raise ValueError('PCM must contain complete stereo16 frames')
    frames = len(pcm) // FRAME_BYTES
    if not 0 <= skip <= entry < frames / 2:
        raise ValueError('Entry must be in the original first half, after skip')
    return pcm[entry * FRAME_BYTES:] + pcm[skip * FRAME_BYTES:entry * FRAME_BYTES]


def decode(path):
    run = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0',
                          '-f', 's16le', '-ar', str(RATE), '-ac', '2', 'pipe:1'],
                         check=True, capture_output=True)
    if run.stderr.strip():
        raise ValueError(f'Audio decode errors for {path}: {run.stderr.decode(errors="replace")}')
    if len(run.stdout) % FRAME_BYTES:
        raise ValueError(f'Incomplete decoded PCM frame: {path}')
    return run.stdout


def mp3_bitrate(path):
    # ffprobe on this machine is an ffmpeg alias, so inspect ffmpeg's input stream.
    run = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(path)], capture_output=True)
    info = run.stderr.decode(errors='replace')
    audio = [line for line in info.splitlines() if 'Audio: mp3' in line]
    match = re.search(r', (\d+) kb/s', audio[0]) if audio else None
    if not match:
        raise ValueError(f'Cannot determine source MP3 audio bitrate: {path}')
    rate = min(128, int(match.group(1)))
    if rate not in (8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128):
        raise ValueError(f'Unsupported safe bitrate: {rate}')
    return rate


def inventory(root):
    dark = root / 'art/music_dark_age_20261018'
    later = root / 'art/music_next_ages_20261018'
    metadata = {}
    for row in json.loads((dark / 'catalog.json').read_text(encoding='utf-8'))['tracks']:
        metadata['DA_' + row['slot']] = row
    for row in json.loads((later / 'generation-manifest.json').read_text(encoding='utf-8'))['tracks']:
        metadata[row['slot']] = row
    candidates = {}
    for path in [*(dark / 'lossless').glob('*.flac'), *(later / 'incoming').iterdir()]:
        match = re.match(r'^(DA|FA|CA|IA)[ _]([ABC][1-4])(?:[ ._]|$)', path.name, re.I)
        if path.suffix.lower() in ('.flac', '.wav', '.mp3') and match:
            slot = match.group(1).upper() + '_' + match.group(2).upper()
            candidates.setdefault(slot, []).append(path)
    expected = {f'{age.upper()}_{theme}{level}' for age in CODES for theme in 'ABC' for level in range(1, 5)}
    if set(candidates) != expected or set(metadata) != expected:
        raise ValueError('Expected exactly all 48 music slots in inputs and metadata')
    rank = {'.wav': 0, '.flac': 1, '.mp3': 2}
    selected = {}
    for slot, paths in candidates.items():
        ordered = sorted(paths, key=lambda p: (rank[p.suffix.lower()], p.name))
        if len(ordered) > 1 and rank[ordered[0].suffix.lower()] == rank[ordered[1].suffix.lower()]:
            raise ValueError(f'Ambiguous equal-quality source for {slot}')
        selected[slot] = ordered[0]
    return selected, candidates, metadata


def encode(pcm, target, bitrate):
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 's16le', '-ar', str(RATE),
                    '-ac', '2', '-i', 'pipe:0', '-map', '0:a:0', '-map_metadata', '-1',
                    '-map_chapters', '-1', '-c:a', 'libmp3lame', '-b:a', f'{bitrate}k',
                    '-id3v2_version', '0', '-write_id3v1', '0', str(target)],
                   input=pcm, check=True)


def lua(value):
    if isinstance(value, (list, tuple)):
        return '{' + ','.join(lua(item) for item in value) + '}'
    return json.dumps(value, ensure_ascii=True)


def prepare(ROOT, WORK, OUT):
    root, work, out = Path(ROOT), Path(WORK), Path(OUT)
    out.mkdir(parents=True, exist_ok=True)
    selected, candidates, metadata = inventory(root)
    manifest_path = out / 'audio-manifest.json'
    old = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    old_members = old.get('members', {}) if old.get('recipe') == RECIPE else {}
    inputs, tracks, members, result = {}, [], {}, {}
    durations = [[[0 for _ in range(4)] for _ in range(3)] for _ in range(4)]
    names = [[metadata[f'{age.upper()}_{theme}1']['theme'] for theme in 'ABC'] for age in CODES]
    for slot, paths in candidates.items():
        for path in paths:
            rel = path.relative_to(root).as_posix()
            inputs[rel] = dict(sha256=sha(path), bytes=path.stat().st_size,
                               selected=path == selected[slot])
    generated = reused = 0
    for age_index, age in enumerate(CODES):
        for theme_index, theme in enumerate('ABC'):
            for level in range(1, 5):
                slot = f'{age.upper()}_{theme}{level}'
                source = selected[slot]
                relative = source.relative_to(root).as_posix()
                source_hash = inputs[relative]['sha256']
                pcm = decode(source)
                frames = len(pcm) // FRAME_BYTES
                if frames <= SKIP * 2:
                    raise ValueError(f'Track too short for first-half entries: {slot}')
                bitrate = mp3_bitrate(source) if source.suffix.lower() == '.mp3' else 192
                entries = (SKIP, frames // 4, frames * 2 // 5)
                specs = [(index, entry, rotate_pcm(pcm, entry)) for index, entry in enumerate(entries, 1)]
                if slot == 'DA_A1':
                    specs.append((0, 0, pcm))
                for index, entry, rotated in specs:
                    stem = f'{age}_{theme.lower()}{level}' + (f'_entry{index}' if index > 1 else '')
                    member = 'audio/berber_music/' + ('intro_a1' if index == 0 else stem) + '.mp3'
                    target = work / 'payload' / member
                    pcm_hash = hashlib.sha256(rotated).hexdigest()
                    cached = old_members.get(member, {})
                    cache_ok = (target.exists() and cached.get('source_sha256') == source_hash
                                and cached.get('rotated_pcm_sha256') == pcm_hash
                                and cached.get('bitrate_kbps') == bitrate
                                and cached.get('sha256') == sha(target))
                    if cache_ok:
                        reused += 1
                    else:
                        encode(rotated, target, bitrate)
                        generated += 1
                    decoded = decode(target)
                    expected_frames = len(rotated) // FRAME_BYTES
                    if len(decoded) // FRAME_BYTES != expected_frames:
                        raise ValueError(f'Frame count changed: {member}')
                    if target.read_bytes()[:3] == b'ID3':
                        raise ValueError(f'Unexpected packaged ID3 metadata: {member}')
                    members[member] = dict(path=str(target.resolve()), sha256=sha(target),
                        bytes=target.stat().st_size, slot=slot, entry=index,
                        source=relative, source_sha256=source_hash,
                        source_frames=frames, source_seconds=frames / RATE,
                        source_range_frames=[0 if index == 0 else SKIP, frames],
                        rotation_segments_frames=[[entry, frames], [SKIP, entry]] if index else [[0, frames]],
                        entry_frame=entry, entry_seconds=entry / RATE,
                        first_ten_seconds_removed=index != 0,
                        expected_frames=expected_frames, full_decode_frames=len(decoded) // FRAME_BYTES,
                        duration_seconds=expected_frames / RATE,
                        rotated_pcm_sha256=pcm_hash,
                        decoded_pcm_sha256=hashlib.sha256(decoded).hexdigest(),
                        bitrate_kbps=bitrate, sample_rate=RATE, channels=2,
                        embedded_images=False, id3_metadata=False)
                    result[member] = target
                durations[age_index][theme_index][level - 1] = (frames - SKIP) / RATE
                tracks.append(dict(slot=slot, selected_source=relative, source_sha256=source_hash,
                                   source_pcm_sha256=hashlib.sha256(pcm).hexdigest(),
                                   source_frames=frames, source_seconds=frames / RATE,
                                   bitrate_kbps=bitrate, entry_frames=list(entries),
                                   alternatives=[p.relative_to(root).as_posix() for p in candidates[slot] if p != source]))
                print(f'{slot}: verified {len(specs)} outputs ({bitrate}kbps)', flush=True)
    for relative, info in inputs.items():
        if sha(root / relative) != info['sha256']:
            raise ValueError(f'Source changed during preparation: {relative}')
    if len(result) != 145:
        raise ValueError('Expected 145 audio members')
    source_bytes = sum(row['bytes'] for row in inputs.values() if row['selected'])
    output_bytes = sum(row['bytes'] for row in members.values())
    pcm_bytes = sum(row['expected_frames'] * FRAME_BYTES for row in members.values())
    size = dict(selected_source_bytes=source_bytes, all_retained_input_bytes=sum(row['bytes'] for row in inputs.values()),
                output_bytes=output_bytes, equivalent_stereo48k16_pcm_bytes=pcm_bytes,
                bytes_saved_against_pcm=pcm_bytes - output_bytes,
                note='145 encoded files versus 48 selected originals; originals and unused MP3 alternative retained unchanged')
    manifest = dict(status='passed', recipe=RECIPE, source_slots=48, output_files=145,
                    format='stereo48k MP3; lossless originals192kbps, suppliedMP3 at source bitrate capped128kbps',
                    scope='Full decode/frame/hash/source preservation checks; listening and native playback remain separate',
                    sources=inputs, tracks=tracks, members=members, size=size,
                    run=dict(generated=generated, reused_hash_verified=reused),
                    ffmpeg_version=subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True).stdout.decode().splitlines()[0])
    write(manifest_path, manifest)
    write(out / 'audio-size-evidence.json', size)
    catalog = ('-- Generated by audio_prepare.py from retained source audio.\nBM_Catalog={ages=' + lua(AGES)
               + ',codes=' + lua(CODES) + ',names=' + lua(names) + ',durations=' + lua(durations)
               + ',intro_seconds=' + str(members['audio/berber_music/intro_a1.mp3']['duration_seconds']) + '}\n')
    (root / 'research/berber100/berber_music_catalog.scar').write_text(catalog, encoding='utf-8')
    return result


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[2]
    out = root / 'output/berber_update_1_0_0'
    print(f'Prepared {len(prepare(root, out / "work", out))} verified music files')
