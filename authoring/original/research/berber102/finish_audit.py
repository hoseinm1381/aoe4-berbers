from pathlib import Path
import hashlib,json,collections
from lupa.lua53 import LuaRuntime
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'output/berber_update_1_0_2'
def write(name,data):(OUT/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
audit=json.loads((OUT/'function-audit.json').read_text(encoding='utf8'));mcp=json.loads((OUT/'mcp-symbol-audit.json').read_text(encoding='utf8'))
lua=LuaRuntime(unpack_returned_tuples=True);compile=lua.eval('function(s,n) local f,e=load(s,n); return f~=nil,e end')
compiled=[]
for row in audit['files']:
 p=HERE/row['file'];ok,error=compile(p.read_text(encoding='utf8'),row['file']);assert ok,(row,error)
 compiled.append({'file':row['file'],'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
write('syntax-validation.json',{'status':'passed','runtime':'Lua5.3 compile only; does not execute engine calls','files':compiled})
resolutions={}
for n,r in audit['calls'].items():
 if r['kind']!='unresolved_or_dynamic':continue
 evidence=mcp['symbols'].get(n,{})
 if evidence.get('symbol_status')=='referenced':
  resolutions[n]={'kind':'official_usage_only','samples':evidence['usage_samples'],'limitation':'No API declaration; inherited contract, not full native verification'}
 elif n in ('audio.play','audio.pulse','audio.session','audio.stop','BM_audio.stopBed'):
  method=n.split('.')[-1];text=(HERE/'scar/garrison/garrison.scar').read_text();lines=[i for i,s in enumerate(text.splitlines(),1) if 'function a.'+method+'(' in s]
  assert lines,(n,method)
  resolutions[n]={'kind':'shipped_factory_method','provider':'scar/garrison/garrison.scar','lines':lines,'factory':'Garrison.audio.forMod'}
 elif n in ('blob:byte','blob:sub','key:match','schar','sunpack'):
  resolutions[n]={'kind':'Lua_string_method_or_alias','provider':'Lua5.3 string library; garrison.scar lines28,67,83,99,187'}
 elif n=='fn':resolutions[n]={'kind':'callback_parameter','provider':'scar/ai/berber_ai_engine.scar WithSquads/WithEntity; explicit function arguments'}
 else:raise AssertionError(('unresolved',n))
static=json.loads((OUT/'static-validation.json').read_text())
assert not sum(x['summary']['errors'] for x in static)
warnings=[{'file':x['file'],'diagnostic':d} for x in static for d in x['diagnostics']]
write('audit-resolution.json',{'status':'offline_review_complete_native_pending','scope':'All34shippedSCARs;465namedcalltokens,154nativeAPI,35officialwrappers,233projecthelpers,27Lua/import,16dynamic/reference resolutions',
 'dynamic_resolutions':resolutions,'native_argument_count_mismatches':audit['arity_review'],'unresolved_call_names':[],
 'mcp_status_counts':dict(collections.Counter(x['symbol_status'] for x in mcp['symbols'].values())),
 'static_warnings':warnings,'warning_review':[
 'b.options/job.options are construction job parameter tables initialized by Construct/options or economy recovery, not lobby options.',
 'fn is an explicit callback parameter; string methods and Garrison audio endpoints resolve above.',
 'Rule_RemoveSquadEvent is official API evidence in function-audit/MCP; player squad group in speech is borrowed and deliberately not destroyed.',
 'Enduring_Generations_Reconcile has a pre-existing match-lifetime interval without explicit game-over removal. Defeated players have modifiers removed by reconciliation; game-over lifecycle remains an inherited review caveat. No1.0.2change to it.'
 ],'new_handle_contract':'AI_FindAISquadByID lookup result must satisfy scartype==ST_AISQUAD before AI_IsSquadValid or AISquad_HasPathWithinDistance; nil defers terrain pathfinding to normal commands; nonnative types reject.',
 'native_limitations':['No official usage examples for new AI handle conversion APIs','Lookup absence return and scartype classification need fresh native confirmation','Static call-name/arity checks do not prove all parameter domains or engine lifecycle behavior'],
 'review':'Independent read-only reviewer found no concrete blocker; seven strict tests rerun; noted same native lookup/type uncertainty.'})
print('ALL34_SYNTAX_AND_DYNAMIC_RESOLUTIONS_PASSED')
