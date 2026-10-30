from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
for kind in ['funduq','ribat']:
 out=ROOT/'output/berber_update_0_2_7/integration'/kind
 burn=out/'stamp-source/source/_default.burnproj'
 text=burn.read_text(encoding='utf-8-sig')
 report=json.loads((out/'media-manifest.json').read_text())
 expected=(report['primary_stamp']+'.rdo').replace('/','\\')
 disabled=[]
 def rule(m):
  s=m.group();name=re.search(r'<Burner>(.*?)</Burner>',s).group(1)
  includes=re.search(r'<Includes>(.*?)</Includes>',s,re.S).group(1)
  # Only actual final typed stamp and normal attribute/localization recipes may burn.
  allow=name in ['AttributeBurner','UCSBurner','LuaBurner'] or (name=='ReflectBurner' and includes==expected)
  if not allow:
   s=s.replace('<IsEnabled>true</IsEnabled>','<IsEnabled>false</IsEnabled>');disabled.append({'burner':name,'includes':includes})
  return s
 text=re.sub(r'<BurnRule>.*?</BurnRule>',rule,text,flags=re.S)
 burn.write_text(text,encoding='utf8')
 command=json.loads((out/'prepared-stamp-command.json').read_text())
 command[command.index('--run-root')+1]=str(out/'stamp-native-v2')
 (out/'prepared-stamp-command.json').write_text(json.dumps(command,indent=2))
 (out/'stamp-rule-repair.json').write_text(json.dumps({'reason':'Compiled native media are validator inputs, not material/geometry source burn inputs','disabled':disabled,'only_stamp':expected},indent=2))
 print(kind,len(disabled),'disabled rules')
