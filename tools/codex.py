"""Native Codex UI built from effective production data and real prerequisites.

Only the Codex is mutated. Private/official gameplay tables are read-only.
Current official prerequisite evidence is retained in source, so rebuilds do not
depend on a stale filename-age heuristic or on installed game lookups.
"""
import copy,re
from pathlib import PurePosixPath
from runtime import ROOT,read_json,rgd,child,at,refs

AGES={'dark_age':1,'feudal_age':2,'castle_age':3,'imperial_age':4}
def optional(n,key,default=None):
 try:return child(n,key)
 except StopIteration:return default
def plain(n):
 return {'key':n.key,'kind':n.kind,'value':[plain(x) for x in n.value] if isinstance(n.value,list) else n.value}
def fields(n):return {x['key']:x for x in n.get('value',[]) if isinstance(x,dict)}
def metadata(doc):
 default=child(doc,'default');req=[]
 for ext,key in (('requirement_ext','requirement_table'),('squad_requirement_ext','requirement_table'),('upgrade_bag','requirements')):
  e=optional(default,ext)
  if e is not None and optional(e,key) is not None:req.append(plain(child(e,key)))
 native_refs=[(p,f,n) for p,f,n,_ in refs(default.value) if n]
 ui=optional(default,'ui_ext') or optional(default,'squad_ui_ext')
 if ui is None:
  bag=optional(default,'upgrade_bag');ui=optional(bag,'ui_info') if bag else None
 name=optional(ui,'screen_name') if ui else None;icon=optional(ui,'icon_name') if ui else None
 if ui and name is None:name=next((n for p,n in rgd.flatten(ui.value) if p.endswith('/screen_name')),None)
 if ui and icon is None:icon=next((n for p,n in rgd.flatten(ui.value) if p.endswith('/icon_name')),None)
 if name is None:name=next((n for p,n in rgd.flatten(doc.nodes) if p.endswith('/screen_name')),None)
 if icon is None:icon=next((n for p,n in rgd.flatten(doc.nodes) if p.endswith('/icon_name') and n.value),None)
 construction=[]
 for ext in ('squad_engineer_ext','engineer_ext'):
  e=optional(default,ext);groups=optional(e,'construction_groups') if e else None
  if groups:
   for group in groups.value:
    menu=optional(group,'construction_menu');menu_name=child(menu,'$PBGNAME').value if menu else ''
    match=re.search(r'_age([1-4])(?:_wonders)?$',menu_name);tab_age=int(match[1]) if match else 1
    items=optional(group,'construction_items')
    if items:
     for item in items.value:
      ebp=optional(item,'ebp')
      if ebp and child(ebp,'$PBGNAME').value:construction.append([child(ebp,'$PBGNAME').value,tab_age])
 return {'requirements':req,'refs':native_refs,'construction':construction,'name':name.value if name else '', 'icon':icon.value if icon else ''}

def validate_native_layout(doc):
 for path,n in rgd.flatten(doc.nodes):
  key=path.split('/')[-1]
  if key=='ui_position_column' and not -1<=n.value<=3:raise ValueError('Codex age column outside -1..3: '+path)
  if key=='y_position' and not 0<=n.value<=11:raise ValueError('Codex row outside 0..11: '+path)
  if key=='background_height' and not 0<=n.value<=11:raise ValueError('Codex background outside four ages: '+path)
 for variant in doc.nodes:
  if not isinstance(variant.value,list):continue
  bag=optional(variant,'codex_bag')
  if bag is None:continue
  for group in child(bag,'tech_tree').value:
   pos=[(child(n,'x_position').value,child(n,'y_position').value) for n in child(group,'items').value]
   for i,(x,y) in enumerate(pos):
    if any(y==yy and abs(x-xx)<2 for xx,yy in pos[i+1:]):raise ValueError('Codex icons overlap at native 2-unit pitch')

class Graph:
 def __init__(self,tables,config,stock=None):
  self.owner=config['owner'].replace('-','')+':'
  self.private={(m.split('/')[1],self.owner+PurePosixPath(m).stem):metadata(d) for m,d in tables.items() if m.count('/')>=2}
  self.stock=stock if stock is not None else read_json(ROOT/'source/codex-stock-data.json')['records']
  self.upgrades=read_json(ROOT/'source/codex-stock-facts.json')['records'];self.memo={};self.missing=set();self.construction_ages={};self.foreign_builder_menus=[]
 def get(self,fam,name):
  row=self.private.get((fam,name))
  if row is not None:return row
  if fam=='upgrade' and name in self.upgrades:
   x=self.upgrades[name];return {'requirements':[x['requirements']],'refs':[],'name':'','icon':''}
  row=self.stock.get(fam+'/'+name)
  if row is None:self.missing.add(fam+'/'+name)
  return row or {'requirements':[],'refs':[],'name':'','icon':''}
 def requirement_age(self,node,trail):
  f=fields(node);kind=f.get('$REF',{}).get('value',node.get('key','')).replace('\\','/').split('/')[-1]
  if kind=='required_not':return 1
  if f.get('is_present',{}).get('value') is False:return 1
  if kind in ('required_player_upgrade','required_entity_upgrade'):
   ref=f.get('upgrade_name') or f.get('upgrade')
   if ref:
    target=fields(ref).get('$PBGNAME',{}).get('value','')
    return self.age('upgrade',target,trail) if target else 1
  children=[x for x in node.get('value',[]) if isinstance(x,dict) and isinstance(x.get('value'),list)]
  vals=[self.requirement_age(c,trail) for c in children]
  if kind=='required_any_in_list':
   req=f.get('requirements') or f.get('requirement_table')
   return min([self.requirement_age(x,trail) for x in req['value']] or [1]) if req else 1
  return max(vals or [1])
 def age(self,fam,name,trail=()):
  if fam=='upgrade' and name in AGES:return AGES[name]
  key=(fam,name)
  if key in trail:return 1
  if key not in self.memo:
   self.memo[key]=max([self.requirement_age(x,trail+(key,)) for x in self.get(fam,name)['requirements']] or [1])
  return self.memo[key]
 def landmark_target(self,name):
  if 'landmark' not in name:return None
  def walk(n):
   f=fields(n)
   if f.get('is_present',{}).get('value') is False:
    ref=f.get('upgrade_name');target=fields(ref).get('$PBGNAME',{}).get('value','') if ref else ''
    if target in AGES and AGES[target]>1:return AGES[target]
   for c in n.get('value',[]):
    if isinstance(c,dict) and isinstance(c.get('value'),list):
     value=walk(c)
     if value:return value
  return next((a for n in self.get('ebps',name)['requirements'] if (a:=walk(n))),None)
 def production(self,name):
  return sorted(set((f,n) for p,f,n in self.get('ebps',name)['refs'] if (f=='sbps' and '/spawner_ext/spawn_items/' in p and p.endswith('/squad')) or (f=='upgrade' and '/upgrade_ext/standard_upgrades/' in p)))
 def construction(self,fam,name):
  row=self.get(fam,name)
  # A foreign stock Villager's conditional free-production slot does not define
  # this independent civilization's construction UI. Record rather than import
  # that donor civilization's entire alternate landmark tree.
  if fam=='sbps' and not name.startswith(self.owner) and any('landmark' in n for p,f,n in row['refs'] if '/construction_items/' in p):
   self.foreign_builder_menus.append(name);return set()
  found=[n for p,f,n in row['refs'] if f=='ebps' and '/construction_items/construction_item/ebp' in p and '/associated_ebps/' not in p]
  for target,age in row.get('construction',[]):self.construction_ages[target]=min(age,self.construction_ages.get(target,age))
  if fam=='sbps' and not found:
   for p,f,n in row['refs']:
    if f=='ebps' and '/squad_loadout_ext/unit_list/' in p:found.extend(self.construction('ebps',n))
  return set(found)
 def discover(self,capital,starters,supplement=()):
  buildings={capital};todo=[('ebps',capital)]+list(starters)+[('sbps',self.owner+x) for x in supplement];seen=set()
  while todo:
   fam,name=todo.pop()
   if (fam,name) in seen:continue
   seen.add((fam,name))
   for building in self.construction(fam,name):
    if building not in buildings:buildings.add(building);todo.append(('ebps',building))
   if fam=='ebps':todo.extend(x for x in self.production(name) if x[0]=='sbps')
  return buildings

def family_key(fam,name):
 if fam=='sbps':
  # These aliases are conditional forms/tier names only; admission age always
  # comes from native requirements. Every displayed alias is saved in the report.
  name=re.sub(r'_(?:cheap|free|normal|shoot)(?=_|$)','',name)
  name=re.sub(r'_[1-4](?=_|$)','_tier',name)
 elif fam=='upgrade':
  name=re.sub(r'_(?:iii|ii|i)$','_tier',name)
  name=re.sub(r'_[2-4](?=_|$)','_tier',name)
 return fam+'/'+name

def build(tables,config):
 graph=Graph(tables,config);review=read_json(ROOT/'source/codex-review.json');owner=graph.owner
 codex=next(d for m,d in tables.items() if m.startswith('attrib/codex/'))
 army=next(d for m,d in tables.items() if m.startswith('attrib/army/'));ab=at(army,'default/army_bag')
 capital=next(n for p,f,n,_ in refs(ab.value) if 'starting_buildings' in p and f=='ebps' and n)
 starters=list(dict.fromkeys((f,n) for p,f,n,_ in refs(ab.value) if 'starting_units/' in p and f=='sbps' and n))
 builder=next(n for f,n in starters if 'villager' in n)
 buildings=graph.discover(capital,starters,review.get('script_builders',[]))
 # Same named age/state variants use one producer column and union their menus.
 merged={}
 for b in sorted(buildings,key=lambda x:(x!=capital,x)):
  meta=graph.get('ebps',b);label=meta['name'] or b
  key=(str(label),bool(graph.landmark_target(b)))
  merged.setdefault(key,[]).append(b)
 plans=[]
 for variants in merged.values():
  b=variants[0];target=graph.landmark_target(b);base=min(max(graph.age('ebps',x),graph.construction_ages.get(x,1)) for x in variants)
  if b==capital:base=1
  header_age=target-1 if target else base;available=target or base
  products=sorted(set(x for v in variants for x in graph.production(v)))
  if capital in variants:products=sorted(set(products+starters))
  # Each visible family/tier occupies one icon; no doubled conditional forms.
  seen={};aliases=[]
  for fam,name in products:
   age=max(available,graph.age(fam,name));key=(family_key(fam,name),age)
   if key in seen:aliases.append({'shown':seen[key][1],'alias':name,'age':age});continue
   seen[key]=(fam,name,age)
  plans.append({'producer':b,'variants':variants,'header_age':header_age,'available_age':available,'items':list(seen.values()),'aliases':aliases,'landmark':bool(target)})
 plans.sort(key=lambda p:(p['producer']!=capital,p['header_age'],p['landmark'],p['producer']))
 template=rgd.read((ROOT/'source/ui-templates/english-codex.rgd').read_bytes());tb=at(template,'default/codex_bag')
 proto_group=child(child(tb,'tech_tree'),'group');proto_item=child(child(proto_group,'items'),'tech_tree_item')
 rootchild=child(child(child(tb,'root_item'),'children'),'codex_item_default');container=child(child(rootchild,'children'),'codex_item_container');leaf=child(child(container,'children'),'codex_item_default')
 def setpbg(node,fam,name,key='pbg'):
  p=child(node,key);child(p,'$PBGNAME').value=name;child(p,'$PBGMAP').value=fam
 report={'source':'Native construction tabs/spawner/standard-upgrade menus and positive private/current official prerequisites. No product filename-derived ages.','producer_count':len(plans),'groups':[],'native_codex_visual_test':'pending','missing_stock_evidence':sorted(graph.missing),'foreign_builder_menus_not_imported':sorted(set(graph.foreign_builder_menus))}
 for variant in [n for n in codex.nodes if isinstance(n.value,list)]:
  bag=child(variant,'codex_bag');groups=[];roots=[]
  for plan in plans:
   group=copy.deepcopy(proto_group);entries=[];positions=[];legacy=copy.deepcopy(rootchild);containers=[]
   setpbg(legacy,'ebps',plan['producer']);child(child(child(legacy,'ui_codex_info'),'ui_position'),'ui_position_column').value=plan['header_age']-1
   # Stock ordinary producers lead their available age band. Age-up landmarks
   # occupy the last row of the preceding construction age instead.
   hy=3*(plan['header_age']-1)+(2 if plan['landmark'] else 0)
   def item(fam,name,x,y):
    n=copy.deepcopy(proto_item);setpbg(n,fam,name);setpbg(n,'','','upgrade_pbg')
    for k,v in (('x_position',x),('y_position',y),('left_branch_length',0),('right_branch_length',0),('top_line_length',0)):child(n,k).value=v
    entries.append(n);positions.append((x,y));return n
   item('ebps',plan['producer'],0,hy)
   lanes={};occupied=set()
   for fam,name,age in plan['items']:
    key=family_key(fam,name);slot=0
    while (key,slot,age) in occupied:slot+=1
    occupied.add((key,slot,age));lanes.setdefault((key,slot),len(lanes))
   uses={};width=len(lanes)
   for fam,name,age in plan['items']:
    key=family_key(fam,name);slot=uses.get((key,age),0);uses[(key,age)]=slot+1
    # Persistent lanes align each unit/research chain across all four ages.
    # Native x pitch2 keeps 44px icons separated. Products follow the producer
    # header: units row1, research row2 of each age band.
    x=2*lanes[(key,slot)]-(width-1);y=3*(age-1)+(2 if fam=='upgrade' else 1)
    n=item(fam,name,x,y)
    if fam=='sbps':
     def positive_upgrades(node):
      f=fields(node)
      if f.get('is_present',{}).get('value') is False or f.get('$REF',{}).get('value','').endswith('required_not'):return []
      if 'upgrade_name' in f:
       target=fields(f['upgrade_name']).get('$PBGNAME',{}).get('value','')
       return [target] if target else []
      return [t for c in node.get('value',[]) if isinstance(c,dict) and isinstance(c.get('value'),list) for t in positive_upgrades(c)]
     candidates=[u for req in graph.get(fam,name)['requirements'] for u in positive_upgrades(req) if ('upgrade',u) in [(f,n) for f,n,a in plan['items']]]
     if candidates:setpbg(n,'upgrade',candidates[0],'upgrade_pbg')
    c=copy.deepcopy(container);l=copy.deepcopy(leaf);setpbg(l,fam,name)
    child(child(child(l,'ui_codex_info'),'ui_position'),'ui_position_column').value=age-1
    child(l,'children').value=[];child(c,'children').value=[l];containers.append(c)
   child(group,'items').value=entries;child(group,'background_height').value=11
   b=plan['producer'];style='military'
   if any(k in b for k in ('econ','resource','farm','house','market','caravan')):style='economic'
   elif any(k in b for k in ('defense','outpost','wall','keep','wonder')):style='defence'
   elif any(k in b for k in ('tech','university','blacksmith','religious','divan')):style='tech'
   child(group,'background_template').value='center' if b==capital else style
   child(legacy,'children').value=containers;groups.append(group);roots.append(legacy)
   if variant.key=='default':report['groups'].append(dict(plan,positions=positions))
  child(bag,'tech_tree').value=groups;root=child(bag,'root_item');setpbg(root,'sbps',builder);child(root,'children').value=roots
  child(bag,'landmark_count').value=sum(p['landmark'] for p in plans)
  for key,fam,items in (('unique_units','sbps',review['unique_units']),('unique_techs','upgrade',review['unique_techs'])):
   proto=child(child(tb,key),'pbg');values=[]
   for name in items:
    if (fam,owner+name) not in graph.private:raise ValueError('Unknown owned overview entry '+name)
    p=copy.deepcopy(proto);child(p,'$PBGNAME').value=owner+name;child(p,'$PBGMAP').value=fam;values.append(p)
   child(bag,key).value=values
  child(bag,'special_items').value=[]
 validate_native_layout(codex);report['native_bounds_verified']=True
 return codex,report
