"""Exact installed official API/wrapper provenance; supplements MCP checks."""
from pathlib import Path
import re,json
from pipeline import ROOT,OUT,LIB,sha,write

def collect():
    api=Path('E:/Games/steamapps/common/Age of Empires IV/scardocs/api/Essence_ScarFunctions.api')
    signatures={}
    for i,line in enumerate(api.read_text(encoding='utf8').splitlines(),1):
        m=re.match(r'(\w+)\(',line)
        if m:signatures[m[1]]={'kind':'installed_official_api','file':str(api),'line':i,'signature':line}
    for f in (LIB/'scripts').rglob('*.scar'):
        text=f.read_text(encoding='utf8',errors='replace')
        for i,line in enumerate(text.splitlines(),1):
            m=re.match(r'\s*function\s+(\w+)\s*\(',line)
            if m:signatures.setdefault(m[1],{'kind':'installed_official_wrapper','file':str(f),'line':i,'signature':line.strip(),'source_sha256':sha(f)})
    ours=list((ROOT/'research/berber0110/ai').glob('*.scar'))
    calls=set();locals=set()
    for f in ours:
        raw=f.read_text()
        raw=re.sub(r'--[^\n]*','',raw)
        calls.update(re.findall(r'(?<![.\w])([A-Z]\w*)\s*\(',raw))
        locals.update(re.findall(r'function\s+([A-Z]\w*)\s*\(',raw))
    calls-=locals
    unknown=sorted(calls-signatures.keys())
    report={'status':'passed' if not unknown else 'unresolved','unresolved':unknown,
        'api_sha256':sha(api),'scar_library':json.loads((LIB/'scar-library.json').read_text()),
        'contracts':{n:signatures[n] for n in sorted(calls) if n in signatures},
        'native_acceptance':'pending: references and Lua simulation do not execute the native engine; income API trade/relic coverage and market pricing need native qualification',
        'difficulty_evidence':{'file':str(LIB/'scripts/ai/cardinal_scoring_functions.scar'),'function':'Util_AiDifficultySwitch','line':65,
          'mapping':'AID_EASY/Easy, AID_NORMAL/Intermediate, AID_HARD/Hard, all others/Hardest'},
        'command_wrappers':'Installed command.scar: Cmd_Construct 1816; Cmd_Upgrade 1167; Cmd_Ability 1226; Cmd_AttackMove 705'}
    write(OUT/'official-api-evidence.json',report)
    print('Official contracts:',len(calls),'unresolved:',unknown)
    assert not unknown,unknown
if __name__=='__main__':collect()
