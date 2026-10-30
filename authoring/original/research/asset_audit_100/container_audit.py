"""Read-only cooked RGD/RIFF/MP3 and final ZIP/archive-integrity audit."""
from pathlib import Path
import sys,os,json,hashlib,platform,struct,warnings,wave,io,math,subprocess,concurrent.futures,collections,zipfile
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/berber_update_1_0_0';SGA=OUT/'Berber_future_kingdom.sga'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';sys.path.insert(0,str(EXT));from garrison_shared import rgd
READER=Path('E:/age of empires 4 mods/07_Subscribed_Mods/Subscribed_Mods/Current/subscribed_mods/.aoe4-sga-v10-runtime');sys.path[:0]=[str(READER/'site-packages'),str(READER/'SGA-V10/src')];platform.system=lambda:'Windows'
with warnings.catch_warnings():
 warnings.simplefilter('ignore');from relic.sga.v10 import EssenceFSHandler;from relic.sga.core.definitions import Version

def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def riff(raw):
 if raw[:4] not in (b'RIFF',b'RIFX') or raw[8:12]!=b'WAVE':raise ValueError('MissingRIFF/WAVE header')
 order='<' if raw[:4]==b'RIFF' else '>';end=struct.unpack_from(order+'I',raw,4)[0]+8
 if end>len(raw):raise ValueError('RIFF declared size exceeds file')
 pos=12;chunks={}
 while pos+8<=end:
  tag=raw[pos:pos+4].decode('ascii',errors='replace');size=struct.unpack_from(order+'I',raw,pos+4)[0];pos+=8
  if pos+size>end:raise ValueError('RIFF chunk exceeds container '+tag)
  chunks[tag]=(pos,size);pos+=size+(size%2)
 if 'fmt ' not in chunks or 'data' not in chunks:raise ValueError('Missingfmt/data')
 fmtpos,size=chunks['fmt '];codec,channels,rate=struct.unpack_from(order+'HHI',raw,fmtpos)
 if not channels or not rate or chunks['data'][1]==0:raise ValueError('Empty/invalidformat')
 return codec,channels,rate,chunks

def mp3_decode(n,raw):
 r=subprocess.run(['ffmpeg','-v','error','-nostdin','-i','pipe:0','-map','0:a:0','-f','null','NUL'],input=raw,capture_output=True)
 return dict(member=n,bytes=len(raw),status='passed' if r.returncode==0 and not r.stderr.strip() else 'error',error=r.stderr.decode(errors='replace')[:500])

def main():
 expected=json.loads((OUT/'member-sha256-proof.json').read_text())['after'];hashes={};data_errors=[];nonfinite=[];counts=collections.Counter();codecs=collections.Counter();mp3=[];attr=[]
 with SGA.open('rb') as f, concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  h=f.read(12);f.seek(0);EssenceFSHandler.version=Version(int.from_bytes(h[8:10],'little'),int.from_bytes(h[10:12],'little'));fs=EssenceFSHandler.read(f)
  for n in sorted(fs.walk.files()):
   raw=fs.readbytes(n);n=n.lstrip('/');hashes[n]=hashlib.sha256(raw).hexdigest();ext=Path(n).suffix
   try:
    if ext=='.rgd':
     d=rgd.read(raw);flat=list(rgd.flatten(d.nodes));counts['rgd']+=1
     bad=[p for p,node in flat if isinstance(node.value,float) and not math.isfinite(node.value)]
     if bad:nonfinite.append(dict(member=n,fields=bad))
     attr.append(dict(member=n,fields=len(flat),nonfinite_fields=bad))
    elif ext in ('.wav','.wem'):
     codec,ch,rate,chunks=riff(raw);counts[ext]+=1;codecs[str(codec)]+=1
     if ext=='.wav':
      with wave.open(io.BytesIO(raw),'rb') as w:
       frames=w.readframes(w.getnframes())
       if len(frames)!=w.getnframes()*w.getnchannels()*w.getsampwidth():raise ValueError('PCMframe byte count mismatch')
    elif ext=='.mp3':mp3.append(pool.submit(mp3_decode,n,raw))
   except Exception as e:data_errors.append(dict(member=n,error=str(e)))
  fs.close();audio=[x.result() for x in mp3]
 if set(hashes)!=set(expected):raise ValueError('Archive member names changed')
 mismatches=[n for n in expected if expected[n]!=hashes[n]]
 archive=json.loads(subprocess.check_output([str(EXT/'bin/sga-archiver.exe'),'list',str(SGA),'--verify'],text=True,encoding='utf8'))
 zip_path=OUT/'Berber-1.0.0.zip';v=json.loads((OUT/'release-validation.json').read_text());assert sha(SGA)==v['sga_sha256'] and sha(zip_path)==v['zip_sha256']
 with zipfile.ZipFile(zip_path) as z:
  assert z.testzip() is None
  with z.open('Berber_future_kingdom.sga') as payload:zip_sga_sha=hashlib.file_digest(payload,'sha256').hexdigest()
  assert zip_sga_sha==v['sga_sha256']
 verified=archive['archive']['verification']['verified']
 report=dict(status='passed' if not(data_errors or mismatches or nonfinite or any(x['status']!='passed' for x in audio)) and verified else 'review_required',archive_sha256=v['sga_sha256'],zip_sha256=v['zip_sha256'],fresh_decoded_member_hashes=len(hashes),hash_mismatches=mismatches,archive_crc_sha1=verified,zip_crc_and_sga_sha256='passed',counts=dict(counts),riff_codecs=dict(codecs),mp3_fresh_full_decodes=len(audio),mp3_errors=[x for x in audio if x['status']!='passed'],data_errors=data_errors,nonfinite_attrib_values=nonfinite,attributes=attr,scope='CompiledRGD tree readability/finitefields; fullPCM payload readability; WwiseWEMRIFFstream boundaries/header format only, not proprietary-codec listening; MP3fullFFmpegdecode; allarchive/ZIPchecks fresh. No ingamevisual orbehavior proof.')
 (OUT/'data-container-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='attributes'},indent=2))
if __name__=='__main__':main()
