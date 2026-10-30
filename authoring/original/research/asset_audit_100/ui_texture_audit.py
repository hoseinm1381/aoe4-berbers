"""Validate format28 UI stream framing and compare diagnostic BC7 projection to PNG sources."""
exec(open('research/asset_audit_100/refs_audit.py',encoding='utf8').read().split('for i,n in enumerate')[0])
from PIL import Image,ImageChops,ImageStat
import io,math
rows=[]
for n in sorted(n for n in names if n.endswith('.rrtex') and not n.startswith('art/')):
 d=rc.parse(read(n));chs={ch.tag:ch for ch in rc.walk(d.roots)};manifest=chs[b'TMAN'].payload;version,width,height,depth,kind,internal=struct.unpack_from('<6I',manifest)
 tx._validate_stream_table(manifest,chs[b'TDAT'].payload);stream,mips=tx._decode_mips(chs[b'TDAT'].payload)
 candidate=ROOT/'assets'/Path(n).with_suffix('.png');row={'path':n,'internal_format':internal,'dimensions':[width,height],'stream_version':stream,'stream_table_validated':True,'mips':[{'level':m.level,'width':m.width,'height':m.height,'bytes':len(m.data),'blocks_4x4_16byte_size_matches':len(m.data)==math.ceil(m.width/4)*math.ceil(m.height/4)*16,'source_encoding':m.source_encoding,'sha256':hashlib.sha256(m.data).hexdigest()} for m in mips],'png_source':str(candidate),'png_exists':candidate.exists()}
 if candidate.exists():
  im=Image.open(candidate).convert('RGBA');row['png_dimensions']=list(im.size);row['png_sha256']=sha(candidate);row['dimension_matches']=im.size==(width,height)
  # BC7 is a diagnostic hypothesis. This does not assign the native internal-format meaning.
  try:
   proj=Image.open(io.BytesIO(tx._dds([mips[0]],98))).convert('RGBA');diff=ImageChops.difference(proj,im);stat=ImageStat.Stat(diff);row['diagnostic_BC7_projection']={'dxgi_hypothesis':98,'mean_absolute_channel_error':stat.mean,'rms_channel_error':stat.rms,'maximum_channel_error':[v[1] for v in diff.getextrema()]}
  except Exception as e:row['diagnostic_BC7_projection']={'error':str(e)}
 rows.append(row)
report={'archive_sha256':sha(ARCH),'textures':len(rows),'stream_tables_validated':sum(r['stream_table_validated'] for r in rows),'all_mip_block_sizes_match':all(m['blocks_4x4_16byte_size_matches'] for r in rows for m in r['mips']),'PNG_sources_found':sum(r['png_exists'] for r in rows),'PNG_dimensions_match':sum(r.get('dimension_matches',False) for r in rows),'rows':rows,'conclusion':'All46 format28 UI/mod texture stream tables and compressed mip framing validated. PNG source dimensions crosschecked. Native internal-format28 interpretation remains unqualified by installed decoder; optional DXGI98 BC7 projection is diagnostic only. No native visual proof.'}
(OUT/'ui-texture-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print({k:v for k,v in report.items() if k!='rows'});print('BC7 samples',[(r['path'],r.get('diagnostic_BC7_projection')) for r in rows[:3]])
fs.close();f.close()
