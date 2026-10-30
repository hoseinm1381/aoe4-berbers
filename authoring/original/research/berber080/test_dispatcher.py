"""Execute the real SCAR dispatcher under Lua 5.1 with bounded engine mocks."""
from pathlib import Path
import unittest
from lupa.lua51 import LuaRuntime

HERE = Path(__file__).parent
SOURCE = Path(r"F:\aoe_4_temp\Berber_future_kingdom_ai_20261014\output\Berber-0.7.4-handoff.1-2026-10-17\mod-source\scar\berber_scripted_speech.scar")


class DispatcherTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
            now=0; roster={}; chosen={}; played={}; listeners={}; sessions=0; stops=0
            function import(_) end
            function print(_) end
            function World_GetGameTime() return now end
            function Game_GetLocalPlayer() return 'local' end
            function Player_GetRaceName(_) return 'malian' end
            function World_OwnsSquad(s) return s.world or false end
            function Squad_GetPlayerOwner(s) assert(not s.world); return s.owner or 'local' end
            function Squad_GetID(s) return s.id end
            function Squad_IsValid(id) for _,s in ipairs(roster) do if s.id==id then return true end end return false end
            function Squad_FromID(id) for _,s in ipairs(roster) do if s.id==id then return s end end end
            function Squad_IsAlive(s) return not s.dead end
            function Squad_GetBlueprint(s) return s.bp end
            function BP_GetName(bp) return bp.name end
            function Squad_GetPosition(s) return {x=0,z=0} end
            function Squad_GetHealth(s) return s.hp or 100 end
            function Camera_GetCurrentTargetPos() return {x=0,z=0} end
            function Squad_IsConstructing(s) return s.building or false end
            function Squad_IsGatheringResourceType(s,t) return s.resource==t end
            function Squad_IsAttacking(s,_) return s.attacking or false end
            function Squad_IsMoving(s) return s.moving or false end
            function Player_GetSquads(_) return roster end
            function SGroup_CountSpawned(g) return #g end
            function SGroup_GetSpawnedSquadAt(g,i) return g[i] end
            function SGroup_CreateIfNotFound(_) return {} end
            function SGroup_Destroy(_) end
            function Misc_GetSelectedSquads(g,_) for i=#g,1,-1 do g[i]=nil end; for i,s in ipairs(chosen) do g[i]=s end end
            function Rule_AddSquadEvent(f,s,e,r) listeners[s.id]=r end
            function Rule_RemoveSquadEvent(f,s) listeners[s.id]=nil end
            function Rule_AddInterval(f,t) ticker=f end
            function Rule_Remove(f) ticker=nil end
            RT_Wood=1; RT_Gold=2; RT_Stone=3; RT_Food=4
            SCMD_Move=1; SCMD_Patrol=2; SCMD_Attack=3; SCMD_StationaryAttack=4
            SCMD_AttackMove=5; SCMD_Stop=6; SCMD_HoldPosition=7; SCMD_BuildStructure=8
            SCMD_Gather=9; SCMD_Trade=10; SCMD_Load=11; SCMD_Retreat=12; SCMD_Ability=13
            GE_SquadCommandIssued=20; GE_SquadKilled=21
            Garrison={audio={forMod=function(_) return {
                session=function() sessions=sessions+1 end,
                pulse=function(_) end,
                play=function(clip,...) played[#played+1]=clip end,
                stop=function() stops=stops+1 end} end}}
            -- Deliberately NO Garrison.speech: normal-client playback must not need it.
            BerberVoiceBank={pbgids={[2359463]='villager',[1073741842]='tuareg'},blueprints={},clips={}}
            for _,f in ipairs({'villager','tuareg'}) do
                BerberVoiceBank.clips[f]={}
                for _,a in ipairs({'select','movesu','attack','stop','structurebuild','resourcegather','resourcewood','resourcemine','effortpain','effortdeath'}) do
                    BerberVoiceBank.clips[f][a]={{f..'/'..a,0.2}}
                end
            end
            villager={id=1,bp={PropertyBagGroupID=2359463,name='unit_villager_1_mal'}}
            tuareg={id=2,bp={PropertyBagGroupID=1073741842,name='unit_spearman_tuareg_1_ber'}}
        ''')
        path = HERE / "berber_scripted_speech.scar"
        self.lua.execute((path if path.exists() else SOURCE).read_text(encoding="utf-8"))

    def calls(self):
        return list(self.lua.globals().played.values())

    def test_villager_selection_without_native_api(self):
        self.lua.execute("roster={villager}; chosen={villager}; BerberSpeech_Start(); ticker(); now=5; ticker()")
        self.assertEqual(self.calls(), ["villager/select"])

    def test_spearman_selection_without_native_api(self):
        self.lua.execute("roster={tuareg}; chosen={tuareg}; BerberSpeech_Start(); ticker()")
        self.assertEqual(self.calls(), ["tuareg/select"])

    def test_mixed_selection_has_one_reply(self):
        self.lua.execute("roster={villager,tuareg}; chosen={villager,tuareg}; BerberSpeech_Start(); ticker()")
        self.assertEqual(self.calls(), ["villager/select"])

    def test_commands_and_work(self):
        self.lua.execute('''roster={villager,tuareg}; BerberSpeech_Start(); ticker()
            now=5; BerberSpeech_OnCommand({squad=tuareg,command=SCMD_Move},listeners[2])
            now=10; BerberSpeech_OnCommand({squad=tuareg,command=SCMD_Attack},listeners[2])
            now=15; BerberSpeech_OnCommand({squad=tuareg,command=SCMD_Stop},listeners[2])
            now=20; BerberSpeech_OnCommand({squad=villager,command=SCMD_Gather},listeners[1])
            now=25; BerberSpeech_OnCommand({squad=villager,command=SCMD_BuildStructure},listeners[1])''')
        self.assertEqual(self.calls(), ["tuareg/movesu", "tuareg/attack", "tuareg/stop", "villager/resourcegather", "villager/structurebuild"])

    def test_neutral_and_foreign_squads_are_not_voiced(self):
        self.lua.execute("villager.world=true; tuareg.owner='other'; roster={villager,tuareg}; chosen=roster; BerberSpeech_Start(); ticker()")
        self.assertEqual(self.calls(), [])

    def test_pain_death_and_restart(self):
        self.lua.execute('''roster={tuareg}; BerberSpeech_Start(); ticker()
            now=5; tuareg.hp=50; ticker()
            now=10; BerberSpeech_OnKilled({},listeners[2])
            BerberSpeech_Stop(); BerberSpeech_Start(); chosen={tuareg}; now=20; ticker()''')
        self.assertEqual(self.calls(), ["tuareg/effortpain", "tuareg/effortdeath", "tuareg/select"])
        self.assertEqual(self.lua.globals().sessions, 2)
        self.assertEqual(self.lua.globals().stops, 1)

    def test_tuareg_ages_follow_actual_blueprint_names(self):
        self.lua.execute('''
            BerberVoiceBank.age_clips={tuareg={}}
            for age=1,4 do BerberVoiceBank.age_clips.tuareg[age]={select={{'tuareg/age'..age,0.2}}} end
            roster={tuareg}; BerberSpeech_Start(); ticker()
            for age=1,4 do
                tuareg.bp.name='1d3145e8f1b2427f8bb0067851fcf0f1:unit_spearman_tuareg_'..age..'_ber'
                chosen={}; now=age*10; ticker(); chosen={tuareg}; now=now+2; ticker()
            end''')
        self.assertEqual(self.calls(), ["tuareg/age1", "tuareg/age2", "tuareg/age3", "tuareg/age4"])


if __name__ == "__main__":
    unittest.main()
