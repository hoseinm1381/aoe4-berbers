"""Targeted official/baseline RGD read-only evidence. No authoring changes."""
from pathlib import Path
import hashlib, json, os, subprocess, sys, xml.etree.ElementTree as X
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
SCRATCH=OUT/'catalog-scratch'
ARCH=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe'
OFFICIAL=Path('E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga')
BASE=ROOT/'output/berber_update_0_10_1/Berber_future_kingdom.sga'
sys.path.insert(0,str(ROOT/'research/berber0100'))
from catalog import rgdreq, age

def run(*args):
    p=subprocess.run([str(a) for a in args],capture_output=True,text=True,encoding='utf8',errors='replace')
    if p.returncode:raise RuntimeError(p.stdout+p.stderr)
    return p.stdout
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def section(rt,name):return rt.find('./RGDNode[@Key="default"]/RGDNode[@Key="'+name+'"]')
def refs(node):
    if node is None:return []
    return [n.get('Value') for n in node.iter('RGDNode') if n.get('Key')=='$PBGNAME']

def main():
    wanted={'building_econ_wood_mal','building_econ_mining_camp_mal','unit_ram_3_mal','unit_archer_2_mal'}
    wanted.update('upgrade_econ_resource_'+r+'_harvest_rate_'+str(t) for r in ['food','wood','gold','stone'] for t in [2,3,4])
    wanted.update('upgrade_'+kind+'_'+tier for kind in ['melee_damage','melee_armor','ranged_damage','ranged_armor'] for tier in ['i','ii','iii'])
    wanted.update('upgrade_unit_'+unit+'_'+str(t)+'_mal' for unit in ['archer','horseman'] for t in [3,4])
    wanted.update(['upgrade_econ_resource_wood_fell_rate_1','upgrade_unit_town_center_wheelbarrow_1'])
    wanted.add('upgrade_siege_engineers')
    records=[]
    for label,archive in [('official',OFFICIAL),('baseline',BASE)]:
        entries=json.loads(run(ARCH,'list',archive))['members']
        members=[e['path'] for e in entries if Path(e['path']).stem in wanted and e['path'].endswith('.rgd') and any('/'+cat+'/' in e['path'] for cat in ['ebps','sbps','upgrade'])]
        dest=SCRATCH/label
        missing=[member for member in members if not (dest/member).exists()]
        if missing:
            args=[ARCH,'extract',archive,dest]
            for member in missing:args.extend(['--member',member])
            run(*args)
        for member in members:
            path=dest/member;decoded=path.with_suffix('.decoded.xml')
            if not decoded.exists():run(ARCH,'decode-rgd',path,decoded)
            rt=X.parse(decoded).getroot()
            req=section(rt,'upgrade_bag' if '/upgrade/' in member else 'squad_requirement_ext' if '/sbps/' in member else 'requirement_ext')
            row={'source':label,'archive':str(archive),'member':member,'rgd_sha256':sha(path),
                 'requirement':rgdreq(req),'upgrade_refs':refs(section(rt,'upgrade_ext')),
                 'construction_refs':refs(section(rt,'construction_ext')),
                 'builder_refs':refs(section(rt,'squad_engineer_ext')),
                 'spawner_refs':refs(section(rt,'spawner_ext'))}
            records.append(row)
    result={'archives':[{'source':l,'path':str(a),'sha256':sha(a)} for l,a in [('official',OFFICIAL),('baseline',BASE)]],'records':records}
    (OUT/'catalog-provenance.json').write_text(json.dumps(result,indent=2)+'\n')
    selected={}
    for r in records:
        category=next(c for c in ['ebps','sbps','upgrade'] if '/'+c+'/' in r['member'])
        selected[(category,Path(r['member']).stem)]=r
    mapping={'building_upgrades':{},'upgrades':{},'entities':{},'squad_builders':{}}
    for (category,name),r in selected.items():
        if category=='upgrade':
            era=age(name)
            if name.endswith('_iii'):era=4
            elif name.endswith('_ii'):era=3
            elif name.endswith('_i'):era=2
            mapping['upgrades'][name]={'age':era,'requirement':r['requirement']}
        elif category=='ebps':
            if 'building_econ_' in name:mapping['building_upgrades'][name]=r['upgrade_refs']
            elif 'ram' in name:mapping['entities'][name]={'requirement':r['requirement']}
        elif r['builder_refs']:mapping['squad_builders'][name]=r['builder_refs']
    (OUT/'catalog-mapping.json').write_text(json.dumps(mapping,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
