"""Combined-module trace regression. Simplified simulation, NEVER native proof."""
from pathlib import Path
import hashlib,json
from lupa.lua51 import LuaRuntime
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent

def simulate():
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute((HERE/'fixtures/test_runtime.lua').read_text())
    for name in ['policy','catalog','engine','navigation','economy','production','military','controller']:
        lua.execute((HERE/'scar/ai'/f'berber_ai_{name}.scar').read_text())
    lua.execute((ROOT/'assets/scar/buildings/tribal_tent.scar').read_text())
    lua.execute('''
      setup_match(false)
      for _,p in ipairs(players) do p.resources={20000,20000,20000,20000};p.rates={100,100,100,100} end
      for _,e in ipairs(all_entities) do
        if e.resource_type==RT_Food then e.name='sheep' elseif e.resource_type==RT_Wood then e.name='tree'
        elseif e.resource_type==RT_Gold then e.name='gold_mine' elseif e.resource_type==RT_Stone then e.name='stone_mine' end
      end
      entity_index={};squad_index={}
      function update_indices()
        for _,e in ipairs(all_entities) do entity_index[e.id]=e end
        for _,p in ipairs(players) do for _,s in ipairs(p.squads) do squad_index[s.id]=s end end
      end
      function Entity_IsValid(id) local e=entity_index[id];return e~=nil and not e.invalid end
      function Squad_IsValid(id) local s=squad_index[id];return s~=nil and not s.invalid end
      update_indices();tribal_tent_start();BerberAI_OnGameSetup();BerberAI_OnInit();BerberAI_SetDifficulty();BerberAI_Start()
    ''')
    trace=[]
    for tick in range(1,181):
        lua.execute('advance(10);update_indices();BerberAI_Tick()')
        if tick==90:
            before=lua.globals().rand_calls
            lua.globals().BerberAI_OnGameRestore()
            assert lua.globals().rand_calls==before,'restore redrew simulation RNG'
        if tick==100:
            lua.execute('''
              local p=players[1];local s=p.squads[#p.squads]
              s.alive=false;s.despawned=true;s.entity.alive=false;s.entity.despawned=true
              table.insert(all_entities,{id=999999,name='dead_world_entity',alive=false,despawned=true,pos=pos(0,0)})
            ''')
        if tick%6==0:
            states=[]
            for i in range(1,8):
                st=lua.globals().BerberAI_State.players[i*11]
                states.append({'pid':st.pid,'age':st.age,'workers':st.live['villager'] or 0,
                    'archers':st.live['archer'] or 0,'lancers':st.live['zenata'] or 0,
                    'buildings':len(st.buildings),'saving':bool(st.saving_age)})
            trace.append({'time':tick*10,'states':states})
    assert lua.globals().players[8].enabled,'other civilization AI changed'
    assert all(s['age']==4 for s in trace[-1]['states']),'combined flow did not reach Imperial'
    assert all(s['workers']<=[60,75,90,105,105,105,105][i] for i,s in enumerate(trace[-1]['states']))
    assert len(lua.globals().grants)==0,'direct free-resource recovery returned'
    assert any(o.kind=='train' and 'archer' in o.name for o in lua.globals().orders.values())
    assert any(o.kind=='train' and 'horseman' in o.name for o in lua.globals().orders.values())
    lua.globals().BerberAI_OnGameOver()
    lua.execute('assert(next(rules)==nil)')
    return trace

def main():
    first=simulate();second=simulate()
    assert first==second,'repeated deterministic traces differ'
    data=json.dumps(first,sort_keys=True,separators=(',',':')).encode()
    report={'status':'passed','scenario':'eight slots: seven Berber AI and native English; normal land',
        'simulated_seconds':1800,'runs':2,'ticks_per_run':180,'trace_sha256':hashlib.sha256(data).hexdigest(),
        'restore_at_seconds':900,'death_despawn_after_seconds':1000,'final':first[-1],
        'fixture':'Deliberately high fixed resources/income and simplified geometry/commands; control-flow only',
        'does_not_prove':['native opening timings','native costs/legality','combat/pathfinding','total-income source coverage','multiplayer performance']}
    out=ROOT/'output/berber_update_1_0_2';out.mkdir(parents=True,exist_ok=True)
    (out/'simulation-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('SIMULATION_PASSED',report['trace_sha256'])
if __name__=='__main__':main()
