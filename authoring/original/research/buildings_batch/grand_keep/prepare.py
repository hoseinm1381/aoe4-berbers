from pathlib import Path
import shutil,subprocess,json,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/grand_keep';Q=R/'research/buildings_batch/grand_keep';O=R/'output/buildings_batch/grand_keep'
for p in [A,Q,O]:p.mkdir(parents=True,exist_ok=True)
for src,dst in [(R/'art/buildings/funduq/geometry_helpers.py',A/'geometry_helpers.py'),(R/'research/buildings_batch/funduq/run_build.py',Q/'run_build.py')]:
 s=src.read_text().replace('funduq','grand_keep').replace('Funduq','GrandKeep');dst.write_text(s)
src=R/'research/buildings_batch/keep/stock';shutil.copytree(src,Q/'stock',dirs_exist_ok=True)
b=Path('C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin');arc='E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga'
for tag,p in [('core','attrib/ebps/races/core/buildings/building_wonder_age3.rgd'),('mal','attrib/ebps/races/malian/buildings/building_landmark_age3_landmarkf_mal.rgd')]:
 f=Q/(tag+'.rgd')
 if not f.exists():subprocess.run([str(b/'sga-archiver.exe'),'extract-member',arc,p,str(f)],check=True,capture_output=True)
 if not f.with_suffix('.xml').exists():subprocess.run([str(b/'sga-archiver.exe'),'decode-rgd',str(f),str(f.with_suffix('.xml'))],check=True,capture_output=True)
target=R/'assets/attrib/instances/ebps/races/malian/buildings/landmarks/almohad_keep/building_landmark_age3_landmarkf_mal.xml'
shutil.copyfile(target,Q/'current_target.xml')
tree=E.parse(target);vals=[{'tag':e.tag,'name':e.get('name'),'value':e.get('value')} for e in tree.iter() if e.get('name') in ['animator_scale','entity_scale','upgrade_name','state_tree','footprint_scale','parent_pbg']]
evidence={'construction_age':3,'completed_minimum_age':4,'required_completed_sources':[4],'source_scale_factor':.8,'target_animator_scale':125,'entity_scale':100,'site_footprint':[8,8],'source_envelope_plan':7.8*.8,'native_rendered_envelope_plan':7.8,'current_xml_values':vals,'construction_reuse':'Age IV cumulative stages in Age III construction, no separate completed Age III model','official_readbacks':['core.xml','mal.xml'],'builder_reference':'assets/attrib/instances/sbps/races/malian/berbers/unit_villager_1_mal.xml:1538'}
(Q/'AGE_AND_TARGET_EVIDENCE.json').write_text(json.dumps(evidence,indent=2));print(json.dumps(evidence,indent=2))
