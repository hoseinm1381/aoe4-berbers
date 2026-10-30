"""Build both native Codex representations from actual private production data.

Copies native UI record templates and preserves the carrier's allocated PBG ID.
This changes display data only; it does not grant or remove production options.
"""
import copy,re
from pathlib import PurePosixPath
from runtime import rgd,child,at,refs

def validate_native_layout(doc):
    """Four native age bands: columns -1/0..3, rows 0..11."""
    for path,node in rgd.flatten(doc.nodes):
        if node.key=='ui_position_column' and not -1<=node.value<=3:
            raise ValueError('Codex age column outside -1..3: '+path+' = '+str(node.value))
        if node.key=='y_position' and not 0<=node.value<=11:
            raise ValueError('Codex age row outside 0..11: '+path+' = '+str(node.value))
        if node.key=='background_height' and not 0<=node.value<=11:
            raise ValueError('Codex background extends past four native age bands: '+path)

def build(tables,config):
    owner=config['owner'].replace('-','')+':'
    def family(m):return m.split('/')[1]
    byname={(family(m),PurePosixPath(m).stem):doc for m,doc in tables.items()}
    def lookup(fam,name):return byname.get((fam,name[len(owner):])) if name.startswith(owner) else None
    codex=next(doc for m,doc in tables.items() if m.startswith('attrib/codex/'))
    def age_of(fam,name):
        match=re.search(r'(?:_|age)([1-5])(?:_|$)',name.split(':')[-1])
        age=min(4,int(match.group(1))) if match else 1
        doc=lookup(fam,name)
        if doc is not None:
            for path,family,target,_ in refs(doc.nodes):
                if not path.startswith('/default/') or 'require' not in path:continue
                if target in ('feudal_age','castle_age','imperial_age'):
                    age=max(age,{'feudal_age':2,'castle_age':3,'imperial_age':4}[target])
        return age
    if config.get('codex_mode')=='repair_bounds':
        # Retain the existing Berber graph and row/branch layout. Its original
        # exporter used producer indexes for native age columns too.
        def repair(node,age=None):
            if not isinstance(node.value,list):
                if node.key=='ui_position_column':node.value=age-1 if age else -1
                elif node.key=='background_height':node.value=min(11,node.value)
                return
            pbg=next((c for c in node.value if c.key=='pbg'),None)
            if pbg is not None:
                name=child(pbg,'$PBGNAME').value;fam=child(pbg,'$PBGMAP').value
                age=age_of(fam,name) if name else None
            for n in node.value:repair(n,age)
        for node in codex.nodes:repair(node)
        validate_native_layout(codex)
        return codex,{'mode':'existing graph retained; age columns/background bounds repaired','native_bounds_verified':True}
    army=next(doc for m,doc in tables.items() if m.startswith('attrib/army/'))
    bag=at(army,'default/army_bag')
    capital=next(name for path,fam,name,_ in refs(bag.value) if 'starting_buildings' in path and fam=='ebps' and name)
    starters=[]
    for path,fam,name,_ in refs(bag.value):
        if 'starting_units/' in path and fam=='sbps' and name and (fam,name) not in starters:starters.append((fam,name))
    builder=next((name for fam,name in starters if 'villager' in name),starters[0][1])
    buildings={capital};menu_queue=[]
    # Owned engineer SBP and EBP construction targets include every age and both
    # landmark alternatives. Native menus are followed without taking unrelated
    # requirements, enemies, ruins or foreign TC snapshots as producers.
    for (fam,name),doc in byname.items():
        if fam not in ('ebps','sbps'):continue
        for path,targetfam,target,_ in refs(doc.nodes):
            if 'construction' in path and target:
                if targetfam=='ebps' and lookup(targetfam,target):buildings.add(target)
                elif targetfam=='menu':menu_queue.append(target)
    seen=set()
    while menu_queue:
        name=menu_queue.pop()
        if name in seen:continue
        seen.add(name);doc=lookup('menu',name)
        if doc is None:continue
        for _,fam,target,_ in refs(doc.nodes):
            if fam=='ebps' and lookup(fam,target):buildings.add(target)
            elif fam=='menu' and target:menu_queue.append(target)
    producers=[]
    for building in sorted(buildings,key=lambda n:(n!=capital,n)):
        doc=lookup('ebps',building);items=[]
        if doc is not None:
            for path,fam,name,_ in refs(doc.nodes):
                wanted=(fam=='sbps' and '/spawner_ext/spawn_items/' in path and path.endswith('/squad')) or (fam=='upgrade' and '/upgrade_ext/standard_upgrades/' in path)
                if wanted and name and (fam,name) not in items:items.append((fam,name))
        if building==capital:
            for item in starters:
                if item not in items:items.append(item)
        producers.append((building,items))
    if len(producers)<2:raise ValueError('Construction graph did not reach civilization buildings')
    report={'producer_count':len(producers),'groups':[], 'unpositioned_script_grants':[],
            'source':'owned construction menus, native spawners and standard upgrade lists',
            'native_codex_visual_test':'pending'}
    template_bag=at(codex,'default/codex_bag')
    proto_group=copy.deepcopy(child(child(template_bag,'tech_tree'),'group'))
    proto_item=copy.deepcopy(child(child(proto_group,'items'),'tech_tree_item'))
    proto_root_child=copy.deepcopy(child(child(child(template_bag,'root_item'),'children'),'codex_item_default'))
    container=copy.deepcopy(child(child(proto_root_child,'children'),'codex_item_container'))
    leaf=copy.deepcopy(child(child(container,'children'),'codex_item_default'))
    for variant in [n for n in codex.nodes if isinstance(n.value,list)]:
        cbag=child(variant,'codex_bag');tree=child(cbag,'tech_tree')
        root=child(cbag,'root_item')
        child(child(root,'pbg'),'$PBGNAME').value=builder
        child(child(root,'pbg'),'$PBGMAP').value='sbps'
        # All template copies have existing native structural fields. Repeated
        # list record names are intentional; there are no new gameplay IDs here.
        groups=[];roots=[];landmarks=0
        for producer_index,(building,items) in enumerate(producers):
            group=copy.deepcopy(proto_group);entries=[];positions=set()
            def item(fam,name,x,y):
                if (x,y) in positions:raise ValueError('Overlapping Codex positions')
                positions.add((x,y));n=copy.deepcopy(proto_item)
                child(child(n,'pbg'),'$PBGNAME').value=name;child(child(n,'pbg'),'$PBGMAP').value=fam
                for key,value in (('x_position',x),('y_position',y),('left_branch_length',0),('right_branch_length',0),('top_line_length',0)):
                    child(n,key).value=value
                child(child(n,'upgrade_pbg'),'$PBGNAME').value='';child(child(n,'upgrade_pbg'),'$PBGMAP').value=''
                entries.append(n)
            item('ebps',building,0,3*(age_of('ebps',building)-1))
            totals={}
            for fam,name in items:
                age=age_of(fam,name);totals[age]=totals.get(age,0)+1
            rowcounts={}
            for fam,name in items:
                age=age_of(fam,name)
                offset=rowcounts.get(age,0);rowcounts[age]=offset+1
                item(fam,name,offset//2-totals[age]//4,3*(age-1)+1+offset%2)
            child(group,'items').value=entries
            child(group,'background_height').value=max(2,max(y for _,y in positions))
            template='military'
            if any(k in building for k in ('econ','resource','farm','house','market','caravan')):template='economic'
            elif any(k in building for k in ('defense','outpost','wall','keep','wonder')):template='defence'
            elif any(k in building for k in ('tech','university','blacksmith','monastery')):template='tech'
            child(group,'background_template').value='center' if building==capital else template
            groups.append(group)
            entry=copy.deepcopy(proto_root_child)
            child(child(entry,'pbg'),'$PBGNAME').value=building;child(child(entry,'pbg'),'$PBGMAP').value='ebps'
            try:child(child(child(entry,'ui_codex_info'),'ui_position'),'ui_position_column').value=age_of('ebps',building)-1
            except StopIteration:pass
            containers=[]
            for fam,name in items:
                c=copy.deepcopy(container);l=copy.deepcopy(leaf)
                child(child(l,'pbg'),'$PBGNAME').value=name;child(child(l,'pbg'),'$PBGMAP').value=fam
                child(child(child(l,'ui_codex_info'),'ui_position'),'ui_position_column').value=age_of(fam,name)-1
                try:child(l,'children').value=[]
                except StopIteration:pass
                child(c,'children').value=[l];containers.append(c)
            child(entry,'children').value=containers;roots.append(entry)
            if 'landmark' in building:landmarks+=1
            if variant.key=='default':report['groups'].append({'producer':building,'items':items,'positions':sorted(positions)})
        tree.value=groups;child(root,'children').value=roots
        child(cbag,'landmark_count').value=landmarks
    validate_native_layout(codex)
    report['native_bounds_verified']=True
    return codex,report
