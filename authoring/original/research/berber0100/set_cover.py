"""Add the existing Content Editor cover to the current candidate, retaining payloads."""
import hashlib,json,shutil,zipfile,struct
from pathlib import Path
from release import ZIP,FINAL,ROOT,OUT,verify
from pipeline import sha,write

def main():
    report=json.loads((OUT/'release-validation.json').read_text())
    assert sha(ZIP)==report['zip_sha256'] and sha(FINAL)==report['sga_sha256']
    cover=(ROOT/'assets/mod.png').read_bytes()
    assert cover[:8]==b'\x89PNG\r\n\x1a\n'
    width,height=struct.unpack('>II',cover[16:24])
    assert len(cover)<=4*1024*1024 and max(width,height)<=4096
    temporary=OUT/'Berber-0.10.0-cover.tmp.zip'
    assert not temporary.exists()
    old_hash=report['zip_sha256'];old_bytes=ZIP.stat().st_size
    hashes={}
    with zipfile.ZipFile(ZIP) as src,zipfile.ZipFile(temporary,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as dst:
        assert src.testzip() is None
        manifest=json.loads(src.read('garrison.json'))
        manifest['details']['cover']='cover.png'
        for info in src.infolist():
            if info.filename in ['garrison.json','cover.png']:continue
            digest=hashlib.sha256()
            with src.open(info) as reader,dst.open(info,'w') as writer:
                while block:=reader.read(1024*1024):writer.write(block);digest.update(block)
            hashes[info.filename]=digest.hexdigest()
            assert hashes[info.filename]==report['zip_members'][info.filename]
        raw=(json.dumps(manifest,indent=2)+'\n').encode()
        dst.writestr('garrison.json',raw);dst.writestr('cover.png',cover)
        hashes.update({'garrison.json':hashlib.sha256(raw).hexdigest(),'cover.png':hashlib.sha256(cover).hexdigest()})
    with zipfile.ZipFile(temporary) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(set(z.namelist()))
        assert set(z.namelist())==set(hashes)
        for name,digest in hashes.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
    new_hash=sha(temporary)
    write(OUT/'cover-update-validation.json',{'status':'passed','source':'assets/mod.png',
        'cover_sha256':hashes['cover.png'],'cover_bytes':len(cover),'dimensions':[width,height],
        'previous_zip_sha256':old_hash,'zip_sha256':new_hash,'sga_sha256_unchanged':report['sga_sha256'],
        'all_existing_payload_hashes_preserved_except_manifest':True,
        'temporary_bytes_before_cleanup':old_bytes,'temporary_bytes_after_cleanup':0,
        'temporary_bytes_reclaimed':old_bytes,'native_card_display':'pending reimport'})
    # Atomic replacement removes only the verified superseded package, leaving no staging copy.
    temporary.replace(ZIP)
    report.update(zip_sha256=new_hash,zip_bytes=ZIP.stat().st_size,zip_members=hashes,
                  cover='cover.png',cover_source='assets/mod.png')
    write(OUT/'release-validation.json',report)
    (OUT/'SHA256SUMS.txt').write_text(new_hash+'  '+ZIP.name+'\n'+sha(FINAL)+'  '+FINAL.name+'\n')
    verify()
    # Keep current delivery references consistent; historical coverless SHA remains in evidence.
    for path in [ROOT/'REBUILD_NEXT.md',ROOT/'STORAGE.md']:
        text=path.read_text().replace(old_hash,new_hash).replace(f'{old_bytes:,}',f'{ZIP.stat().st_size:,}')
        path.write_text(text)
    assert not temporary.exists()
    print('COVER_PACKAGE_VERIFIED',new_hash,ZIP.stat().st_size,'bytes; SGA unchanged; no staging copies retained')

if __name__=='__main__':main()
