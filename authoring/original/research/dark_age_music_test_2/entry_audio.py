"""Regenerable music entry variants from retained lossless masters, no transcoding chain."""
import hashlib,subprocess
RATE=48000
SKIP=10*RATE

def rotate_pcm(pcm,entry):
    """Drop the first ten seconds, rotate remaining complete stereo16 frames."""
    assert len(pcm)%4==0 and SKIP<=entry<len(pcm)//8
    return pcm[entry*4:]+pcm[SKIP*4:entry*4]

def add_entries(root,work,payload,proof,sha,write):
    result={};rows=[]
    for track in proof['tracks']:
        source=root/'art/music_dark_age_20261018'/track['flac_path']
        assert sha(source)==track['flac_sha256']
        pcm=subprocess.run(['ffmpeg','-v','error','-i',str(source),'-f','s16le','-ar','48000','-ac','2','pipe:1'],check=True,capture_output=True).stdout
        assert hashlib.sha256(pcm).hexdigest()==track['pcm_sha256']
        frames=len(pcm)//4
        for index,entry in enumerate((SKIP,int(frames*.25),int(frames*.40)),1):
            name='audio/berber_dark_age/da_'+track['slot'].lower()+('' if index==1 else '_entry'+str(index))+'.mp3'
            target=payload/name;target.parent.mkdir(parents=True,exist_ok=True)
            rotated=rotate_pcm(pcm,entry)
            assert len(rotated)==len(pcm)-SKIP*4
            subprocess.run(['ffmpeg','-v','error','-y','-f','s16le','-ar','48000','-ac','2','-i','pipe:0','-map_metadata','-1','-c:a','libmp3lame','-b:a','192k',str(target)],input=rotated,check=True)
            decoded=subprocess.run(['ffmpeg','-v','error','-i',str(target),'-f','s16le','-ar','48000','-ac','2','pipe:1'],check=True,capture_output=True).stdout
            assert len(decoded)==len(rotated)
            result[name]=target
            rows.append(dict(member=name,entry_seconds=entry/RATE,original_seconds=frames/RATE,output_seconds=len(rotated)/4/RATE,first_ten_seconds_removed=True,source_sha256=track['flac_sha256'],rotated_pcm_sha256=hashlib.sha256(rotated).hexdigest(),mp3_sha256=sha(target),bytes=target.stat().st_size,full_decode_frames=len(decoded)//4))
    write(work.parent/'entry-audio-proof.json',dict(status='passed',variants=rows,format='stereo48k192kbps MP3 from lossless FLAC',recipe='Remove original first10s then rotate remaining audio to 10seconds/25percent/40percent of original timeline'))
    return result
