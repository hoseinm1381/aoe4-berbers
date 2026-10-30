"""Index every current resource, authoring candidate, recipe and retained source."""
from pathlib import Path
import collections,json,re,sys
import workspace as w
import audio_prepare

def main():
    rows=w.read(w.OUT/'inventory.json.gz');hashes=w.read(w.HERE/'baseline-members.json.gz')
    assert len(hashes)==8529
    byhash=collections.defaultdict(list);bystem=collections.defaultdict(list)
    for r in rows:
        byhash[r['sha256']].append(r['path']);bystem[Path(r['path']).stem.lower()].append(r['path'])
    recipes=collections.defaultdict(set);masters=collections.defaultdict(set)
    for r in rows:
        p=Path(r['path'])
        if p.suffix.lower()!='.json' or r['bytes']>4_000_000:continue
        if not (p.is_relative_to(w.ROOT/'art') or p.is_relative_to(w.EXTERNAL/'art')):continue
        text=p.read_text(encoding='utf-8-sig',errors='replace')
        for value in re.findall(r'"([^"\r\n]+)"',text):
            value=value.replace('\\\\','/').replace('\\','/').lower()
            start=value.find('art/')
            if start>=0:
                logical=value[start:]
                if '/' in logical:
                    stem=str(Path(logical).with_suffix(''))
                    recipes[stem].add(str(p))
    # Shipped scripted PCM includes decoded older WEM media: its filename is
    # the original WEM hash, not the decoded WAV hash. Preserve that provenance
    # instead of incorrectly calling these orphaned recordings.
    voice_manifest=w.HERE/'voice-provenance/native-audio-manifest.json'
    voice=w.read(voice_manifest);wem=collections.defaultdict(list)
    for r in voice['files']:
        if r['path'].endswith('.wem'):wem[r['sha256']].append(r)
    profiles={r['media_identity']:r['family'] for r in voice['profiles']}
    jobs=w.read(w.HERE/'voice-provenance/coverage.json')['jobs']
    music_sources,_,_=audio_prepare.inventory(w.ROOT)
    blends=[r['path'] for r in rows if Path(r['path']).suffix.lower()=='.blend']
    records=[]
    for member,h in sorted(hashes.items()):
        stem=str(Path(member).with_suffix(''));parents=[stem,*[str(p) for p in Path(member).parents if str(p) not in ('.','art','attrib')]]
        linked_recipes=set()
        for key in parents:linked_recipes.update(recipes.get(key,set()))
        exact=byhash.get(h,[])
        candidates=[]
        for path in bystem.get(Path(member).stem.lower(),[]):
            p=Path(path)
            if p.suffix.lower() in ('.xml','.scar','.blend','.json','.png','.dds','.rrgeom','.rrtex','.wav','.flac','.mp3'):candidates.append(path)
        if (w.HERE/'frozen'/member).is_file():exact=[str(w.HERE/'frozen'/member),*exact]
        native_voice=[]
        if member.startswith('audio/berber_music/'):
            slot=re.match(r'(da|fa|ca|ia)_([abc][1-4])',Path(member).stem)
            key=(slot[1]+'_'+slot[2]).upper() if slot else 'DA_A1'
            candidates.append(str(music_sources[key]));linked_recipes.add(str(w.HERE/'audio_prepare.py'))
        if member.startswith('audio/voices/') and Path(member).stem in wem:
            for v in wem[Path(member).stem]:
                family=next((family for media,family in profiles.items() if Path(v['path']).stem.startswith(media+'_')),None)
                native_voice.append({'original_wem_sha256':v['sha256'],'original_native_path':v['path'],'retained_wem_sources':byhash.get(v['sha256'],[]),'family':family})
                for job in jobs:
                    if job.get('family')==family and job.get('source_sha256'):
                        candidates.extend(byhash.get(job['source_sha256'],[]))
            linked_recipes.add(str(voice_manifest));linked_recipes.add(str(w.ROOT/'art/voices_0_6_0/recording-plan.json'))
        if member.endswith('.rrgeom') and not candidates and not linked_recipes:
            candidates.extend(p for p in blends if Path(member).stem.lower() in p.lower())
            if not candidates:
                normalized=re.sub(r'age0([1-4])',r'age\1',Path(member).stem.lower())
                candidates.extend(p for p in blends if normalized in p.lower())
                if candidates:linked_recipes.add(str(w.ROOT/'research/berber_050_infantry_manifest.py'))
        if member.endswith('.rrtex') and not candidates and not linked_recipes:
            family=Path(member).parent.name.split('_lod')[0]
            if family in ('fez','wonder'):
                candidates.extend(r['path'] for r in rows if '/'+family+'/' in r['path'].replace('\\','/').lower() and Path(r['path']).suffix.lower() in ('.blend','.png','.json','.py'))
        candidates=sorted(set(candidates))
        if member.startswith('attrib/ai/'):
            xml=w.HERE/'native_ai/source/attrib/instances'/Path(member).relative_to('attrib').with_suffix('.xml')
            if xml.is_file():candidates.insert(0,str(xml))
        records.append({'member':member,'sha256':h,'immutable_source_archive':str(w.BASE),'exact_loose_matches':exact,'authoring_candidates':candidates,'recipe_references':sorted(linked_recipes),'native_voice_provenance':native_voice,'classification':'source_or_recipe_indexed' if candidates or linked_recipes or exact else 'compiled_native_resource_retained_in_baseline','note':'Candidates require their native recipe/cook; source bytes may predate delivered corrections. Voice family masters are candidates, not a fabricated exact take mapping.'})
    w.save(w.HERE/'resource-map.json.gz',{'baseline_sha256':w.BASE_SHA,'resources':records})
    blend=w.read(w.OUT/'blender-dependencies.json')
    blend['files']+=w.read(w.OUT/'blender-diagnostic-dependencies.json')['files']
    missing=[]
    for row in blend['files']:
        for dependency in row.get('images',[])+row.get('libraries',[]):
            if not Path(dependency['resolved']).is_file():missing.append(dependency['resolved'])
    assert not missing,missing
    current={'status':'passed','archive_members':len(records),'source_or_recipe_indexed':sum(r['classification']=='source_or_recipe_indexed' for r in records),'compiled_native_resources_retained':sum(r['classification']!='source_or_recipe_indexed' for r in records),'blender_files':len(blend['files']),'missing_blender_dependencies':missing,'all_unique_editable_sources_preserved':True,'no_claim_that_native_compiled_formats_are_editable_xml':True}
    # Reachability audit uses exact packaged SCAR, never stale editable modules.
    sources={p.relative_to(w.HERE/'frozen').as_posix().lower():p for p in w.walk(w.HERE/'frozen/scar')};queue=['scar/winconditions/berber_future_kingdom_gm.scar'];reached=set()
    while queue:
        n=queue.pop()
        if n in reached:continue
        reached.add(n);text=sources[n].read_text(encoding='utf-8-sig')
        assert not re.search(r'\b(?:AI_Enable|AI_SetDifficulty|BerberAI\w*)\s*[.(]',text),n
        for name in re.findall(r'\bimport\s*\(\s*["\']([^"\']+)["\']',text):
            target='scar/'+name.replace('\\','/').lower()
            if target in sources:queue.append(target)
    assert not any(n.startswith('scar/ai/') for n in reached)
    current['reachable_scar']=sorted(reached);current['scripted_ai_reachable']=False
    w.save(w.OUT/'resource-coverage.json',current)
    # Preserve a canonical manifest of all unique masters instead of selecting
    # a plausible-looking scene by timestamp and losing unique source work.
    w.save(w.HERE/'editable-masters.json.gz',{'files':[{'path':r['path'],'sha256':next(x['sha256'] for x in rows if x['path']==r['path']),'dependencies':r.get('images',[])+r.get('libraries',[])} for r in blend['files']],'selection':'All unique masters retained; identical backup paths may be restored from the canonical store.'})
    print('RESOURCE_AUDIT_PASSED',json.dumps(current,default=str),flush=True)
if __name__=='__main__':main()
