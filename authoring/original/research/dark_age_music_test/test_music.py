from pathlib import Path
import unittest
from lupa.lua51 import LuaRuntime

ROOT=Path(__file__).resolve().parent

class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute((ROOT/'berber_dark_age_policy.scar').read_text())
        self.p=self.lua.globals().BDMPolicy
        self.s=self.p.new(0)
    def test_unique_attackers_not_damage_events(self):
        for _ in range(40):self.p.record(self.s,1,1)
        self.assertEqual(self.p.count(self.s,1),1)
        self.assertEqual(self.p.demand(1),2)
        self.assertEqual(self.p.demand(6),3)
        self.assertEqual(self.p.demand(20),4)
    def test_escalation_needs_stable_one_second(self):
        self.p.record(self.s,1,1)
        self.assertEqual(self.p.tick(self.s,1),1)
        self.assertEqual(self.p.tick(self.s,2),2)
    def test_big_battle_then_quiet_hold(self):
        for i in range(20):self.p.record(self.s,i,1)
        self.p.tick(self.s,1);self.assertEqual(self.p.tick(self.s,2),4)
        self.assertEqual(self.p.tick(self.s,10),4)
        self.assertEqual(self.p.tick(self.s,21),4)
        self.assertEqual(self.p.tick(self.s,22),1)
    def test_expired_entities_are_removed(self):
        self.p.record(self.s,1,1);self.assertEqual(self.p.count(self.s,10),0)
        self.assertIsNone(self.s.seen[1])
    def test_rewind_clears_future_contacts(self):
        self.p.record(self.s,1,90);self.p.tick(self.s,90)
        self.assertEqual(self.p.tick(self.s,1),1)
        self.assertEqual(self.p.count(self.s,1),0)
    def test_transport_same_track_is_not_restarted(self):
        self.assertTrue(self.p.needs_track(None,'A1',False))
        self.assertFalse(self.p.needs_track('A1','A1',False))
        self.assertTrue(self.p.needs_track('A1','A2',False))
        self.assertFalse(self.p.needs_track('A1','A2',True))

class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
          now=0;rules={};events={};beds=0;stops=0;gains=0;ui=0;silence=false;accept=true
          endpoint={session=function() error('music must not reset speech session') end,
            stop=function() error('music must not stop speech session') end,
            pulse=function() error('speech owns heartbeat') end,
            bed=function(path,gain) beds=beds+1;last_path=path;return accept end,
            stopBed=function() stops=stops+1;return true end,
            setBedGain=function(gain) gains=gains+1;return true end}
          Garrison={audio={forMod=function() return endpoint end}}
          function import(...) end; function Core_RegisterModule(...) end
          function print(...) end
          function World_GetGameTime() return now end
          function Rule_Exists(f) return rules[f]~=nil end
          function Rule_AddInterval(f,t) rules[f]=t end
          function Rule_Remove(f) rules[f]=nil end
          function Rule_AddGlobalEvent(f,e) events[f]=e end
          function Rule_RemoveGlobalEvent(f) events[f]=nil end
          function Sound_SetForceSilence(v) silence=v end
          function Sound_MusicStop() end
          function UI_CreateCommand(n) return n end
          function UI_CreateDataContext(t) return t end
          function UI_AddChild(...) ui=ui+1 end
          function UI_Remove(...) ui=ui-1 end
          function UI_SetDataContext(...) end
          function Game_GetLocalPlayer() return 1 end
          function Entity_GetID(e) return e.id end
          function Entity_IsValid(id) return id~=0 end
          function World_OwnsEntity(e) return e.owner==0 end
          function Entity_GetPlayerOwner(e) return e.owner end
          function Entity_IsOfType(e,t) return e.scout==true and t=='scout' end
          function Player_ObserveRelationship(a,b) if a~=b then return 2 else return 1 end end
          GE_DamageReceived=7;R_ENEMY=2
        ''')
        self.lua.execute((ROOT/'berber_dark_age_policy.scar').read_text())
        self.lua.execute((ROOT/'berber_dark_age_catalog.scar').read_text())
        self.lua.execute((ROOT/'berber_dark_age_test.scar').read_text())
        self.g=self.lua.globals();self.g.BDM_OnGameSetup();self.g.BDM_OnInit();self.g.BDM_Start()
    def test_start_is_idempotent_no_shared_session_reset(self):
        self.g.BDM_Start();self.assertEqual(self.g.ui,1)
        self.g.BDM_Tick();self.g.BDM_Tick();self.assertEqual(self.g.beds,1)
    def test_normal_ticks_do_not_restart_and_gain_has_live_endpoint(self):
        self.g.BDM_Tick();self.g.BDM_VolumeUp();self.g.BDM_Tick()
        self.assertEqual(self.g.beds,1);self.assertEqual(self.g.gains,1)
    def test_manual_states_theme_and_wav_reference(self):
        self.g.BDM_Massive();self.g.BDM_ThemeB();self.g.BDM_Tick()
        self.assertIn('b4.mp3',self.g.last_path)
        self.g.BDM_WavReference();self.g.BDM_Tick()
        self.assertIn('reference_a1.wav',self.g.last_path)
    def test_mute_does_not_stop_voices_and_native_mode_restores_music(self):
        self.g.BDM_Tick();self.g.BDM_Mute();self.g.BDM_Tick()
        self.assertEqual(self.g.beds,1);self.assertTrue(self.g.silence)
        self.g.BDM_Native();self.assertFalse(self.g.silence)
    def test_bad_transport_restores_native_music_after_bounded_retries(self):
        self.g.accept=False
        for i in range(25):self.g.now=i;self.g.BDM_Tick()
        self.assertFalse(self.g.silence);self.assertEqual(self.g.BDM_State.mode,'native')
    def test_damage_filter_scout_repair_world_and_unrelated_battles(self):
        self.lua.execute('''
          BDM_Damage({attacker={id=1,owner=1,scout=true},victim={id=2,owner=2}})
          BDM_Damage({attacker={id=2,owner=2},victim={id=1,owner=1},isRepairing=true})
          BDM_Damage({attacker={id=2,owner=2},victim={id=3,owner=3}})
          BDM_Damage({attacker={id=4,owner=0},victim={id=1,owner=1}})
        ''')
        self.assertEqual(self.g.BDMPolicy.count(self.g.BDM_State.policy,0),0)
        self.lua.execute('BDM_Damage({attacker={id=2,owner=2},victim={id=1,owner=1}})')
        self.assertEqual(self.g.BDMPolicy.count(self.g.BDM_State.policy,0),1)
    def test_restore_no_duplicate_ui_rule_or_reset(self):
        self.g.BDM_ThemeC();self.g.BDM_OnGameRestore();self.g.BDM_OnGameRestore()
        self.assertEqual(self.g.ui,1);self.assertEqual(self.g.BDM_State.theme,3)
        self.assertEqual(self.lua.eval('(function() local n=0 for _ in pairs(rules) do n=n+1 end return n end)()'),1)
    def test_cleanup_releases_ui_rules_events_and_native_silence(self):
        self.g.BDM_OnGameOver();self.g.BDM_OnGameOver()
        self.assertEqual(self.g.ui,0);self.assertFalse(self.g.silence)
        self.assertEqual(self.lua.eval('next(rules)==nil and next(events)==nil'),True)

class ShippedEndpointTests(unittest.TestCase):
    def setUp(self):
        from lupa.lua53 import LuaRuntime as Lua53
        self.lua=Lua53(unpack_returned_tuples=True)
        self.lua.execute('''
          packets={}
          function import(...) end
          function World_GetGameTime() return 10 end
          function Garrison_Send(blob) table.insert(packets,Garrison.decode(blob)) end
        ''')
        self.lua.execute((ROOT/'fixtures/garrison.scar').read_text())
    def test_real_endpoint_music_controls_preserve_speech_epoch(self):
        self.lua.execute('''
          a=Garrison.audio.forMod('berber_future_kingdom')
          assert(a.session());assert(a.play('audio/voice.wav',0,0,1))
          assert(a.bed('audio/berber_dark_age/da_a1.mp3',0.03))
          assert(a.setBedGain(0.04));assert(a.stopBed())
          assert(a.play('audio/voice2.wav',0,0,1))
        ''')
        self.assertEqual(self.lua.eval('#packets'),6)
        self.assertTrue(self.lua.eval("packets[1].m=='audio_session' and packets[4].bed_gain==0.04 and packets[5].stop_bed==true"))
        self.assertTrue(self.lua.eval("packets[6].clip=='audio/voice2.wav' and packets[1].epoch==packets[6].epoch"))
    def test_real_endpoint_requires_existing_speech_session(self):
        self.lua.execute("a=Garrison.audio.forMod('berber_future_kingdom');result=a.bed('audio/berber_dark_age/da_a1.mp3',0.03)")
        self.assertFalse(self.lua.globals().result)
        self.assertEqual(self.lua.eval('#packets'),0)

if __name__=='__main__':unittest.main(verbosity=2)
