"""Re-encode editable 0.1.2 audio masters into a separate review directory.

Usage: python tools/audio_rebuild.py --output OUTPUT_DIRECTORY
FFmpeg with libvorbis is required (GARRISON_FFMPEG overrides PATH).
This never changes the active native manifest, masters or player ZIP. Review
edited outputs and update the manifest before building a new local candidate.
Full mod rebuilds use the already verified native inputs and need no FFmpeg.
"""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--allow-edited-masters',action='store_true');args=parser.parse_args()
 out=args.output.resolve()
 if out.exists():raise ValueError('Use an empty new review directory; existing evidence is protected')
 if out.is_relative_to(ROOT/'inputs') or out.is_relative_to(ROOT/'authoring') or out.is_relative_to(ROOT/'release'):raise ValueError('Protected authoring/native/release directory')
 ff=os.environ.get('GARRISON_FFMPEG') or shutil.which('ffmpeg')
 if not ff:raise ValueError('FFmpeg with libvorbis is required')
 recipe=json.loads((ROOT/'source/audio-012-recipe.json').read_text());report={}
 for member,row in recipe['files'].items():
  source=ROOT/'authoring'/row['source_master'];sourcehash=sha(source)
  if not args.allow_edited_masters and sourcehash!=row['source_master_sha256']:raise ValueError('Changed master: '+str(source))
  rate=row['sample_rate'];channels=row['channels'];frame=channels*2
  pcm=subprocess.run([ff,'-v','error','-i',str(source),'-f','s16le','-ar',str(rate),'-ac',str(channels),'pipe:1'],check=True,capture_output=True).stdout
  if 'rotation_segments_frames' in row:pcm=b''.join(pcm[a*frame:b*frame] for a,b in row['rotation_segments_frames'])
  if not args.allow_edited_masters and hashlib.sha256(pcm).hexdigest()!=row['source_pcm_sha256']:raise ValueError('PCM/rotation changed: '+member)
  target=out/member;target.parent.mkdir(parents=True,exist_ok=True)
  subprocess.run([ff,'-v','error','-y','-f','s16le','-ar',str(rate),'-ac',str(channels),'-i','pipe:0','-map_metadata','-1','-c:a','libvorbis','-q:a',str(row['quality']),str(target)],input=pcm,check=True)
  decoded=subprocess.run([ff,'-v','error','-i',str(target),'-f','s16le','-ar',str(rate),'-ac',str(channels),'pipe:1'],check=True,capture_output=True)
  delta=(len(decoded.stdout)-len(pcm))//frame
  if decoded.stderr.strip() or abs(delta)>2048:raise ValueError('Unexpected Vorbis packet-tail length: '+member)
  report[member]={'bytes':target.stat().st_size,'sha256':sha(target),'source_sha256':sourcehash,'decoded_tail_delta_frames':delta}
 (out/'verification.json').write_text(json.dumps({'files':report,'note':'Vorbis container page identifiers may differ between FFmpeg runs; native full mod rebuilds retain the checked-in exact native member bytes.'},indent=2)+'\n')
 print('ENCODED_AND_DECODE_VERIFIED',len(report))
if __name__=='__main__':main()
