import json
from pathlib import Path
p=Path('output/berber_update_0_2_5/authors/lumber');d=json.loads((p/'delivery.json').read_text());report={'status':'passed','building':'lumber','cook':d['cook'],'model_mapping':{m['source']:m['private'] for m in d['models']},'payloads':d['payloads'],'source_validation':str(p/'source-validation.json'),'assembly_validation':str(p/'assembly-validation.json'),'author_delivery':str(p/'delivery.json'),'native_acceptance':'pending user'};(p/'integration-manifest.json').write_text(json.dumps(report,indent=2));print(len(report['payloads']),report['model_mapping'])
