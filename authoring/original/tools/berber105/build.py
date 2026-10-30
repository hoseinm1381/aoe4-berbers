"""Build forward from final 1.0.4, without a historical release chain.

compose --output NEW.sga [--overrides MEMBER_TO_FILE.json]
extract --member LOGICAL_PATH --output NEW_FILE
cook: restore retained attribute/media snapshots and run current Content Editor.
"""
from pathlib import Path
import argparse,copy,json,os,shutil,subprocess,sys,zipfile
import workspace as w

def extract(member,destination,archive=None):
    member=w.member_name(member);destination=Path(destination)
    if destination.exists():raise FileExistsError(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    w.run(w.ARCH,'extract-member',archive or w.BASE,member,destination)
    return destination

def semantic(nodes):return [(n.key,n.hash,n.kind,semantic(n.value) if isinstance(n.value,list) else n.value) for n in nodes]
def encode(doc,rgd):
    keys={h:k for h,k in doc.keys}
    for _,n in rgd.flatten(doc.nodes):
        if n.key is not None:keys[n.hash]=n.key
    doc.keys=list(keys.items());raw=rgd.write(doc)
    assert semantic(rgd.read(raw).nodes)==semantic(doc.nodes)
    return raw

def protect(member,raw,baseline):
    """Carry forward proven UV/speech corrections while retaining intended edits."""
    sys.path.insert(0,str(w.EXT));from garrison_shared import rgd
    proof=[]
    if member.endswith('.rgd'):
        old=rgd.read(baseline);doc=rgd.read(raw)
        before=dict(rgd.flatten(old.nodes));after=dict(rgd.flatten(doc.nodes))
        for key in ('speech_ext','squad_speech_ext'):
            default=after.get('default')
            if default and 'default/'+key not in before:
                removed=[n for n in default.value if n.key==key]
                if removed:default.value[:]=[n for n in default.value if n.key!=key];proof.append('retain absent '+key)
        for path,node in rgd.flatten(doc.nodes):
            if node.key=='attachment_speaker_code' and path in before and before[path].value=='':
                if node.value!='':node.value='';proof.append('clear '+path)
        if proof:raw=encode(doc,rgd)
    if member in {r['member'] for r in w.read(w.HERE/'uv-donors.json')['models']}:
        import uv
        # Reapply only if needed. Reject incompatible topology instead of
        # guessing a correspondence or silently shipping non-finite UVs.
        _,current=uv.groups(raw);_,retained=uv.groups(baseline)
        assert len(current)==len(retained)
        same=all(a['chunk'].payload[28::a['stride']]==b['chunk'].payload[28::b['stride']] for a,b in zip(current,retained))
        uv_equal=all(a['count']==b['count'] and all(a['chunk'].payload[16+i*a['stride']+12:16+i*a['stride']+16]==b['chunk'].payload[16+i*b['stride']+12:16+i*b['stride']+16] for i in range(a['count'])) for a,b in zip(current,retained))
        if not uv_equal:
            raw,report=uv.restore_uv(raw,baseline);proof.append({'uv_repair':report})
        assert all(not g['bad'] for g in uv.groups(raw)[1])
    return raw,proof

def compose(destination,overrides=None):
    destination=Path(destination);assert not destination.exists()
    assert w.sha(w.BASE)==w.BASE_SHA
    destination.parent.mkdir(parents=True,exist_ok=True)
    expected=w.archive_hashes(w.BASE);changed={};corrections={}
    if overrides:
        inputs=w.read(overrides);work=destination.parent/(destination.stem+'-work');assert not work.exists();work.mkdir()
        payload={}
        for name,path in inputs.items():
            name=w.member_name(name);source=Path(path);raw=source.read_bytes()
            if name in expected:
                old=extract(name,work/'baseline'/name).read_bytes();raw,proof=protect(name,raw,old);corrections[name]=proof
            target=work/'payload'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            payload[name]=target;changed[name]=w.digest(raw)
        listing=work/'members.txt';listing.write_text(''.join(k+'='+str(v.resolve())+'\n' for k,v in payload.items()))
        # The archiver preserves each existing member's TOC identity. Split
        # additions by native attrib/data alias when both are present.
        current=w.BASE
        for index,alias in enumerate(('attrib','data')):
            selected={k:v for k,v in payload.items() if (k.startswith('attrib/'))==(alias=='attrib')}
            if not selected:continue
            subset=work/(alias+'.txt');subset.write_text(''.join(k+'='+str(v.resolve())+'\n' for k,v in selected.items()))
            final=destination if alias=='data' or not any(not k.startswith('attrib/') for k in payload) else work/'attrib-stage.sga'
            w.run(w.ARCH,'set-members',current,subset,final,'--alias',alias);current=final
        if not payload:shutil.copyfile(w.BASE,destination)
    else:shutil.copyfile(w.BASE,destination)
    actual=w.archive_hashes(destination)
    assert actual==dict(expected,**changed)
    inv=json.loads(w.run(w.ARCH,'list',destination,'--verify'));assert inv['archive']['verification']['verified']
    if not overrides:assert w.sha(destination)==w.BASE_SHA
    report={'status':'passed','baseline_sha256':w.BASE_SHA,'archive_sha256':w.sha(destination),'members':len(actual),'explicit_overrides':changed,'preservation_corrections':corrections,'all_unselected_resources_identical':True}
    w.save(destination.with_suffix('.verification.json'),report)
    print('COMPOSE_VERIFIED',len(actual),'members;',len(changed),'explicit overlays',flush=True)
    return report

def cook(source_dir=None):
    inputs=w.HERE/'native_ai';work=w.OUT/'work/native-project';assert not work.exists();work.mkdir(parents=True)
    for filename,recordname,dest in [('cook-reference-inputs.zip','cook-inputs.json',work),('cook-media-inputs.zip','cook-media-inputs.json',work/'assets')]:
        archive=inputs/filename;assert w.sha(archive)==w.read(inputs/recordname)['snapshot_sha256']
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            for n in z.namelist():w.member_name(n)
            z.extractall(dest)
    overlays=Path(source_dir) if source_dir else inputs/'source/attrib/instances'
    for p in w.walk(overlays):
        target=work/'assets/attrib/instances'/p.relative_to(overlays);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    shutil.copyfile(inputs/'_default.burnproj',work/'assets/_default.burnproj')
    core=w.EXT/'bin/core/garrison-core.exe';editor=Path('E:/Games/steamapps/common/Age of Empires IV/EssenceEditor.exe')
    args=[core,'essence','build-mod','--editor',editor,'--mod',work/'Berber_future_kingdom.aoe4mod','--run-root',w.OUT/'work/native-cook','--timeout','600','--console-burn-log']
    p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf8',errors='replace',timeout=660)
    (w.OUT/'native-cook.log').write_text(p.stdout+'\n'+p.stderr)
    w.save(w.OUT/'native-cook-result.json',{'exit_code':p.returncode,'command':list(map(str,args))})
    assert p.returncode==0,p.stderr[-2000:]
    cooked=w.OUT/'work/native-cook/output/extension/Berber_future_kingdom/Berber_future_kingdom.sga'
    proofs=[]
    for source in w.walk(inputs/'compiled-ai'):
        member='attrib/'+source.relative_to(inputs/'compiled-ai').as_posix();target=w.OUT/'work/ai-readback'/member
        extract(member,target,cooked)
        if not source_dir:assert w.sha(target)==w.sha(source),member
        proofs.append({'member':member,'sha256':w.sha(target),'retained_identical':w.sha(target)==w.sha(source)})
    w.save(w.OUT/'native-cook-proof.json',{'status':'passed','source_dir':str(overlays),'seven_ai_records':proofs,'cook_sha256':w.sha(cooked)})
    print('CURRENT_COOK_VERIFIED',len(proofs),flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['compose','extract','cook']);p.add_argument('--output');p.add_argument('--overrides');p.add_argument('--member');p.add_argument('--source-dir');a=p.parse_args()
    if a.command=='compose':compose(a.output,a.overrides)
    elif a.command=='extract':extract(a.member,a.output)
    else:cook(a.source_dir)
if __name__=='__main__':main()
