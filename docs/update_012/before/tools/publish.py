"""Explicitly invoked release publication using configured Git credentials.

Never prints or persists credentials. Uploads a draft, verifies remote hashes,
then publishes the release. Source push is a separate reviewed Git command.
"""
import argparse
import hashlib
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
import requests
from urllib3.util.retry import Retry

ROOT=Path(__file__).resolve().parents[1]
REPO='hoseinm1381/aoe4-berbers'


def auth():
    result=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',
                          text=True,capture_output=True,check=True,
                          env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
    values=dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
    assert values.get('password'),'Configured GitHub credential unavailable'
    return {'Authorization':'Bearer '+values['password'],'Accept':'application/vnd.github+json',
            'X-GitHub-Api-Version':'2022-11-28','User-Agent':'Berbers-release-tools'}


def api(headers,path,method='GET',body=None):
    data=None if body is None else json.dumps(body).encode('utf-8')
    request=urllib.request.Request('https://api.github.com'+path,data=data,headers=headers,method=method)
    with urllib.request.urlopen(request,timeout=90) as response:
        return json.load(response)


def upload(headers,release,path):
    assert path.stat().st_size < 2_000_000_000, f'Asset requires splitting: {path}'
    sha=hashlib.file_digest(path.open('rb'),'sha256').hexdigest()
    existing=api(headers,f'/repos/{REPO}/releases/{release["id"]}/assets')
    matches=[a for a in existing if a['name']==path.name]
    if matches:
        assert len(matches)==1
        asset=matches[0]
        assert asset['size']==path.stat().st_size and asset.get('digest')=='sha256:'+sha,'Remote asset conflict; preserve and inspect'
        print('REMOTE VERIFIED',path.name,flush=True);return asset
    parsed=urllib.parse.urlsplit(release['upload_url'].split('{',1)[0])
    assert parsed.scheme=='https' and parsed.hostname=='uploads.github.com'
    class ProgressReader:
        def __init__(self,source):self.source=source;self.sent=0;self.last=0
        def __len__(self):return path.stat().st_size
        def read(self,size=-1):
            chunk=self.source.read(size);self.sent+=len(chunk)
            if time.monotonic()-self.last>25:
                print('UPLOAD',path.name,self.sent,'/',len(self),flush=True);self.last=time.monotonic()
            return chunk
    session=requests.Session()
    # Only connection setup is retried. A failed transfer is inspected before retry.
    session.mount('https://',requests.adapters.HTTPAdapter(max_retries=Retry(total=2,connect=2,read=0,status=0,backoff_factor=1)))
    with path.open('rb') as source:
        response=session.post(release['upload_url'].split('{',1)[0],params={'name':path.name},
            data=ProgressReader(source),headers={**headers,'Content-Type':'application/zip' if path.suffix=='.zip' else 'application/octet-stream'},
            timeout=(30,900),allow_redirects=False)
    session.close()
    assert response.status_code==201,f'Upload failed HTTP {response.status_code}; inspect draft assets before retry'
    asset=response.json()
    assert asset['size']==path.stat().st_size
    # GitHub computes a digest after storage; poll boundedly if still pending.
    for attempt in range(12):
        if asset.get('digest'):break
        time.sleep(5)
        asset=api(headers,f'/repos/{REPO}/releases/assets/{asset["id"]}')
    assert asset.get('digest')=='sha256:'+sha,f'Remote digest mismatch/unavailable for {path.name}'
    print('UPLOADED AND VERIFIED',path.name,asset['size'],flush=True)
    return asset


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['inspect','release']);p.add_argument('--directory',type=Path);a=p.parse_args()
    headers=auth();account=api(headers,'/user');assert account['login']=='hoseinm1381'
    repo=api(headers,'/repos/'+REPO);assert repo['permissions']['push']
    if a.action=='inspect':
        print(json.dumps({'account':account['login'],'repository':repo['html_url'],'default_branch':repo['default_branch'],
                          'size_kb':repo['size'],'releases':len(api(headers,'/repos/'+REPO+'/releases'))},indent=2))
    else:
        assert a.directory and a.directory.is_dir()
        config=json.loads((ROOT/'project.json').read_text());tag='v'+config['version']
        releases=api(headers,'/repos/'+REPO+'/releases')
        matches=[r for r in releases if r['tag_name']==tag]
        if matches:
            assert len(matches)==1 and matches[0]['draft'],'Existing public release is immutable here'
            release=matches[0]
        else:
            release=api(headers,'/repos/'+REPO+'/releases','POST',{
                'tag_name':tag,'target_commitish':'main','name':'Berbers '+config['version'],
                'body':(ROOT/'docs/RELEASE_NOTES.md').read_text(),'draft':True,'prerelease':False})
        assets=[]
        paths=[a.directory/('Berbers-Garrison-'+config['version']+'.zip')]
        assert paths[0].is_file(), 'Missing playable release ZIP'
        assert not api(headers,f'/repos/{REPO}/releases/{release["id"]}/assets') or all(
            asset['name']==paths[0].name
            for asset in api(headers,f'/repos/{REPO}/releases/{release["id"]}/assets')
        ), 'Release must contain only the playable ZIP'
        assert len({p.name for p in paths})==len(paths)
        for path in sorted(paths,key=lambda p:(p.parent!=a.directory,p.stat().st_size)):
            if path.is_file():assets.append(upload(headers,release,path))
        assert len(assets)==1
        published=api(headers,f'/repos/{REPO}/releases/{release["id"]}','PATCH',{'draft':False})
        print(json.dumps({'release':published['html_url'],'assets':[{k:x[k] for k in ('name','size','digest','browser_download_url')} for x in assets]},indent=2),flush=True)
