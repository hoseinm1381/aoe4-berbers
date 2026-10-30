import json,struct
from pathlib import Path
r=json.loads(Path('output/berber_update_0_2_5/integration/com_lumber_camp.native.json').read_text());print([(o['fields']['m_blueprint']['text'],struct.unpack('<10f',bytes.fromhex(o['fields']['m_transform']['raw']))) for o in r if o['type']=='VisualStampBlueprint'])
