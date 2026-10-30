"""Audit exact shipped SCAR calls against local official contracts + MCP."""
from pathlib import Path
import collections,hashlib,json,os,re,sys
ROOT=Path(__file__).resolve().parents[2];SOURCE=Path(__file__).resolve().parent
OUT=ROOT/'output/berber_update_1_0_3'
LIB=Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/scar-library/scripts/scar'
API=Path('E:/Games/steamapps/common/Age of Empires IV/scardocs/api/Essence_ScarFunctions.api')
CONTROL=set('and break do else elseif end false for function if in local nil not or repeat return then true until while'.split())
STANDARD=set('assert collectgarbage dofile error getfenv getmetatable ipairs load loadfile loadstring module newproxy next pairs pcall print rawequal rawget rawset require select setfenv setmetatable tonumber tostring type unpack xpcall import'.split())
DEF=re.compile(r'\b(local\s+)?function\s+([\w.:]+)\s*\(([^)]*)\)')
CALL=re.compile(r'(?<![\w.:])([A-Za-z_][\w.:]*)\s*\(')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=2)+'\n',encoding='utf8')
def mask(text):
 result=list(text);i=0
 while i<len(text):
  start=i;comment=text.startswith('--',i)
  if comment:i+=2
  long=re.match(r'\[(=*)\[',text[i:])
  if long:
   closing=']'+long[1]+']';end=text.find(closing,i+len(long[0]));end=len(text) if end<0 else end+len(closing)
  elif comment:
   end=text.find('\n',i);end=len(text) if end<0 else end
  elif text[i:i+1] in ('"',"'"):
   quote=text[i];i+=1
   while i<len(text):
    if text[i]=='\\':i+=2;continue
    if text[i]==quote:i+=1;break
    i+=1
   end=i
  else:i=start+1;continue
  for n in range(start,end):
   if result[n]!='\n':result[n]=' '
  if not comment:result[start]='Q'
  i=end
 return ''.join(result)

def args_at(text,start):
 stack=[];commas=0;end=start
 for end in range(start,len(text)):
  c=text[end]
  if c in '({[':stack.append(c)
  elif c in ')}]':
   if not stack:break
   stack.pop()
  elif c==',' and not stack:commas+=1
 part=text[start:end]
 if re.search(r'\bfunction\b',part):return None,part
 return (commas+1 if part.strip() else 0),part

def main():
 OUT.mkdir(exist_ok=True)
 official={}
 for i,line in enumerate(API.read_text(encoding='utf8').splitlines(),1):
  m=re.match(r'(\w+)\((.*?)\) RETURNS:',line)
  if m:official[m[1]]={'kind':'native_api','file':str(API),'line':i,'params':m[2].strip(),'signature':line}
 wrappers={};official_imports={}
 for p in LIB.rglob('*.scar'):
  text=p.read_text(encoding='utf8',errors='replace');masked=mask(text)
  for m in DEF.finditer(masked):
   if not m[1]:wrappers.setdefault(m[2],{'kind':'official_wrapper','file':str(p),'line':text.count('\n',0,m.start())+1,'params':m[3].strip()})
  official_imports[p.relative_to(LIB).as_posix().lower()]=str(p)
 files=list((SOURCE/'scar').rglob('*.scar'));defs=collections.defaultdict(list);calls=[];imports=[];fileproof=[]
 for p in files:
  text=p.read_text(encoding='utf8');masked=mask(text);name=p.relative_to(SOURCE).as_posix();spans=[]
  for m in DEF.finditer(masked):
   defs[m[2]].append({'file':name,'line':text.count('\n',0,m.start())+1,'local':bool(m[1]),'params':m[3].strip()});spans.append((m.start(),m.end()))
  for m in re.finditer(r'\b([\w.:]+)\s*=\s*function\s*\(([^)]*)\)',masked):defs[m[1]].append({'file':name,'line':text.count('\n',0,m.start())+1,'local':True,'params':m[2].strip()})
  for m in CALL.finditer(masked):
   if m[1] in CONTROL or any(a<=m.start()<b for a,b in spans):continue
   argc,argtext=args_at(masked,m.end())
   calls.append({'name':m[1],'file':name,'line':text.count('\n',0,m.start())+1,'argc':argc,'args':text[m.end():m.end()+len(argtext)]})
  for m in re.finditer(r'\bimport\s*\(\s*["\']([^"\']+)["\']',text):
   rel=m[1].lower().replace('\\','/');private=SOURCE/'scar'/rel
   imports.append({'from':name,'import':rel,'resolution':'packaged' if private.exists() else 'official' if rel in official_imports else 'native_loader_or_missing','provider':str(private) if private.exists() else official_imports.get(rel)})
  fileproof.append({'file':name,'sha256':sha(p),'bytes':p.stat().st_size,'functions':len(spans)})
 classified={};arity=[]
 for n in sorted({r['name'] for r in calls}):
  sites=[r for r in calls if r['name']==n]
  if n in official:entry=official[n]
  elif n in wrappers:entry=wrappers[n]
  elif n in defs:entry={'kind':'project_helper','definitions':defs[n]}
  elif n in STANDARD or n.split('.')[0] in ('math','string','table','os','io','coroutine','debug','package','bit32'):entry={'kind':'lua_or_import'}
  else:entry={'kind':'unresolved_or_dynamic'}
  classified[n]=dict(entry,sites=sites)
  if n in official:
   params=official[n]['params'];expected=0 if not params or params=='Void' else len(params.split(','))
   for r in sites:
    if r['argc'] is not None and r['argc']!=expected:arity.append(dict(r,expected=expected,signature=official[n]['signature']))
 write(OUT/'function-audit.json',{'scope':'All34exact shipped SCAR members, frozen1.0.1 plus102patches; official imports separately resolved','files':fileproof,'imports':imports,'definitions':dict(defs),'calls':classified,'arity_review':arity,'counts':dict(collections.Counter(v['kind'] for v in classified.values()))})
 (OUT/'mcp-symbols.json').write_text(json.dumps(sorted(n for n,r in classified.items() if r['kind'] in ('native_api','official_wrapper','unresolved_or_dynamic')),indent=2)+'\n')
 print('AUDIT',len(files),'files',len(classified),'distinct calls',dict(collections.Counter(v['kind'] for v in classified.values())))
 print('UNRESOLVED',[(n,[s['file'] for s in r['sites']][:2]) for n,r in classified.items() if r['kind']=='unresolved_or_dynamic'])
 print('ARITY_REVIEW',[(r['name'],r['file'],r['line'],r['argc'],r['expected']) for r in arity])
 print('IMPORT_REVIEW',[r for r in imports if r['resolution']=='native_loader_or_missing'])

if __name__=='__main__':main()
