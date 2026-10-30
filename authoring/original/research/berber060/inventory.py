"""Read only stock SPD inventory; no media extraction or game writes."""
from common import *
import json, tempfile

def main():
    from profiles import parse_profile
    destination=OUT/'inventory'
    summaries=[]
    for civ in ('Malian','Abbasid'):
        archive=GAME/'cardinal/archives'/f'SoundSpeech{civ}.sga'
        listing=json.loads(run(ARCH,'list',archive,'--filter','.spd'))
        archive_hash=sha(archive)
        media_listing=json.loads(run(ARCH,'list',archive,'--filter','.wem'))
        known={m['path'].replace('\\','/').lower() for m in media_listing['members']}
        write(destination/f'{civ.lower()}-spd-members.json',listing)
        for member in listing['members']:
            if not member['path'].endswith('.spd'): continue
            target=destination/'stock'/member['path']
            target.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='spd-readback-',dir=destination) as scratch:
                fresh=Path(scratch)/'profile.spd'
                run(ARCH,'extract-member',archive,member['path'],fresh)
                if target.exists() and sha(target)!=sha(fresh):
                    raise ValueError('Observed fixture changed; preserve prior evidence and reinspect: '+str(target))
                if not target.exists(): target.write_bytes(fresh.read_bytes())
            references={m['text'].replace('\\','/').lower() for row in parse_profile(target.read_bytes()) for m in row['media']}
            missing=sorted(references-known)
            summaries.append({'archive':str(archive),'archive_sha256':archive_hash,'member':member['path'],'path':str(target),'sha256':sha(target),'size':target.stat().st_size,
                'unique_media_references':len(references),'archive_media_count':len(known),'missing_media_paths':missing,
                'media_validation':'archive namespace membership only; WEM bytes not extracted or decoded'})
            if missing: raise ValueError('Stock profile media not found in its donor archive: '+member['path'])
    write(destination/'stock-profiles.json',summaries)
    print(f'Extracted {len(summaries)} stock profiles only')

if __name__=='__main__': main()
