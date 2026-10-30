"""UNQUALIFIED runtime mute candidate: remove paired speech extensions only."""
import copy,sys
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'research/berber060'))
from common import EXT
sys.path.insert(0,str(EXT))
from garrison_shared import rgd
from bindings import semantic,encode
from bindings import patch as patch_speaker

def explicit_candidate(data,member,audio_root=None):
 """Probe explicit absent private profile; this is not qualified native muting."""
 family='villager' if 'unit_villager_1_mal' in member else 'tuareg'
 if family=='tuareg' and 'unit_spearman_tuareg_' not in member:raise ValueError('Outside two pilot families')
 speaker='b71vmute' if family=='villager' else 'b71tmute'
 if audio_root is not None and (Path(audio_root)/('malian_'+speaker+'.spd')).exists():raise ValueError('Mute candidate profile already exists; preserve it and refuse')
 payload,changes=patch_speaker(data,speaker,'malian')
 return payload,{'kind':'explicit_absent_private_profile','family':family,'speaker':speaker,'changes':changes,'semantic_undo':'passed','native_mute':'UNVERIFIED until audible pilot; stock fallback remains possible'}

def patch(data,extension):
 if extension not in ('speech_ext','squad_speech_ext'):raise ValueError('Not a speech extension')
 original=rgd.read(data);doc=copy.deepcopy(original)
 default=dict(rgd.flatten(doc.nodes))['default']
 matches=[(i,n) for i,n in enumerate(default.value) if n.key==extension]
 if len(matches)!=1 or not isinstance(matches[0][1].value,list):raise ValueError('Expected one existing speech table')
 index,removed=matches[0];default.value.pop(index)
 payload=encode(doc)
 verify(original,rgd.read(payload),index,removed)
 return payload,{'extension':extension,'sibling_index':index,'removed':semantic([removed]),'native_mute':'UNVERIFIED until audible pilot'}

def verify(original,candidate,index,removed):
 restored=copy.deepcopy(candidate);default=dict(rgd.flatten(restored.nodes))['default']
 if any(n.key==removed.key for n in default.value):raise ValueError('Speech extension unexpectedly remains')
 default.value.insert(index,copy.deepcopy(removed))
 if semantic(restored.nodes)!=semantic(original.nodes):raise ValueError('Non-speech semantic difference')
