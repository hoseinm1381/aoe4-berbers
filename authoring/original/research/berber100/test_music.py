from pathlib import Path
import unittest
from lupa.lua51 import LuaRuntime
ROOT=Path(__file__).resolve().parent

class MusicTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
          age=1;now=0;rules={};events={};beds=0;stops=0;gains=0;ui=0;silence=false;accept=true
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
          function Player_GetCurrentAge(p) return age end
          function Entity_GetID(e) return e.id end
          function Entity_IsValid(id) return id~=0 end
          function World_OwnsEntity(e) return e.owner==0 end
          function Entity_GetPlayerOwner(e) return e.owner end
          function Entity_IsOfType(e,t) return e.scout==true and t=='scout' end
          function Player_ObserveRelationship(a,b) if a~=b then return 2 else return 1 end end
          GE_DamageReceived=7;R_ENEMY=2
        ''')

        self.lua.execute((ROOT/'berber_music_policy.scar').read_text())
        catalog=ROOT/'berber_music_catalog.scar'
        if catalog.exists():self.lua.execute(catalog.read_text())
        else:self.lua.execute('BM_Catalog={ages={"Dark Age","Feudal Age","Castle Age","Imperial Age"},codes={"da","fa","ca","ia"},intro_seconds=120,names={},durations={}};for a=1,4 do BM_Catalog.names[a]={"A","B","C"};BM_Catalog.durations[a]={{110,110,110,110},{110,110,110,110},{110,110,110,110}} end')
        self.lua.execute((ROOT/'berber_music.scar').read_text())
        self.g=self.lua.globals();self.g.BM_OnGameSetup();self.g.BM_OnInit();self.g.BM_Start()
    def tick(self,now=None):
        if now is not None:self.g.now=now
        self.g.BM_Tick()
    def battle(self,n=6):
        for i in range(n):self.g.BMPolicy.record(self.g.BM_State.policy,i,self.g.now)
        self.tick();self.tick(self.g.now+1)
    def test_start_idempotent_no_shared_session_reset(self):
        self.g.BM_Start();self.tick();self.tick()
        self.assertEqual(self.g.beds,1);self.assertEqual(self.g.ui,1)
    def test_original_opening_and_retirement_before_loop(self):
        self.tick();self.assertIn('intro_a1.mp3',self.g.last_path)
        self.tick(self.g.BM_Catalog.intro_seconds-.4);self.assertNotIn('intro_',self.g.last_path)
    def test_all_three_age_advancements_use_proper_music_and_new_entry(self):
        self.tick()
        for age,code in ((2,'fa'),(3,'ca'),(4,'ia')):
            self.g.age=age;self.tick(age*10)
            self.assertIn('/'+code+'_a1',self.g.last_path)
            self.assertIn(self.g.BM_State.entry,(1,2,3))
    def test_advanced_age_start_never_plays_dark_age_intro(self):
        self.g.age=3;self.tick();self.assertIn('/ca_a1',self.g.last_path)
    def test_all_48_catalog_paths_and_3_entries(self):
        s=self.g.BM_State
        for age,code in enumerate(('da','fa','ca','ia'),1):
            for theme in range(1,4):
                for level in range(1,5):
                    for entry in range(1,4):
                        s.age=age;s.theme=theme;s.level=level;s.entry=entry
                        suffix='' if entry==1 else '_entry'+str(entry)
                        self.assertEqual(self.g.BM_Path(),f'audio/berber_music/{code}_{chr(96+theme)}{level}{suffix}.mp3')
    def test_combat_then_peace_selects_entries_after_intro(self):
        self.tick();self.battle();self.assertIn('_a3',self.g.last_path)
        first=self.g.BM_State.entry
        self.tick(10);self.tick(22)
        self.assertIn('_a1',self.g.last_path);self.assertNotEqual(self.g.BM_State.entry,first)
    def test_retries_keep_entry_then_recover(self):
        self.tick();self.g.age=2;self.g.accept=False;self.tick()
        entry=self.g.BM_State.entry;self.tick(1);self.assertEqual(self.g.BM_State.entry,entry)
        self.g.accept=True;self.tick();self.assertIn('/fa_a1',self.g.last_path)
    def test_failed_transport_restores_native_music(self):
        self.g.accept=False
        for i in range(25):self.tick(i)
        self.assertFalse(self.g.silence);self.assertEqual(self.g.BM_State.mode,'native')
    def test_volume_is_live_and_does_not_restart(self):
        self.tick();self.g.BM_VolumeUp();self.tick()
        self.assertEqual(self.g.beds,1);self.assertEqual(self.g.gains,1);self.assertEqual(self.g.BM_State.gain,4)
    def test_volume_zero_mutes_bed_only_and_resume_avoids_opening(self):
        self.tick();self.g.BM_Volume(-3);self.tick()
        self.assertEqual(self.g.beds,1);self.assertEqual(self.g.BM_State.gain,0)
        self.g.BM_VolumeUp();self.tick();self.assertNotIn('intro_',self.g.last_path)
    def test_zero_volume_also_mutes_native_fallback(self):
        self.g.accept=False
        for i in range(25):self.tick(i)
        self.assertFalse(self.g.silence)
        self.g.BM_Volume(-3);self.tick()
        self.assertTrue(self.g.silence);self.assertEqual(self.g.BM_State.gain,0)
    def test_volume_clamps(self):
        self.g.BM_Volume(1000);self.assertEqual(self.g.BM_State.gain,100)
        self.g.BM_Volume(-1000);self.assertEqual(self.g.BM_State.gain,0)
    def test_restore_retains_nonopening_entry_no_duplicate_registrations(self):
        self.g.age=4;self.tick();path=self.g.last_path
        self.g.BM_OnGameRestore();self.g.BM_OnGameRestore();self.tick()
        self.assertEqual(self.g.last_path,path);self.assertEqual(self.g.ui,1)
        self.assertEqual(self.lua.eval('(function() local n=0 for _ in pairs(rules) do n=n+1 end return n end)()'),1)
    def test_restore_opening_does_not_replay_intro(self):
        self.tick();self.g.BM_OnGameRestore();self.tick();self.assertNotIn('intro_',self.g.last_path)
    def test_clock_rewind_does_not_replay_intro_or_stale_contacts(self):
        self.tick(50);self.battle();self.tick(1)
        self.assertEqual(self.g.BMPolicy.count(self.g.BM_State.policy,1),0)
        self.assertNotIn('intro_',self.g.last_path)
    def test_peace_theme_rotation_keeps_correct_age(self):
        self.g.age=2;self.tick();duration=self.g.BM_Catalog.durations[2][1][1]
        self.tick(duration*2+1);self.assertIn('/fa_b1',self.g.last_path)
    def test_damage_filters(self):
        self.lua.execute('BM_Damage({attacker={id=1,owner=1,scout=true},victim={id=2,owner=2}}); BM_Damage({attacker={id=2,owner=2},victim={id=3,owner=3}}); BM_Damage({attacker={id=4,owner=0},victim={id=1,owner=1}})')
        self.assertEqual(self.g.BMPolicy.count(self.g.BM_State.policy,0),0)
        self.lua.execute('BM_Damage({attacker={id=2,owner=2},victim={id=1,owner=1}})')
        self.assertEqual(self.g.BMPolicy.count(self.g.BM_State.policy,0),1)
    def test_cleanup_releases_only_owned_resources(self):
        self.g.BM_OnGameOver();self.g.BM_OnGameOver()
        self.assertEqual(self.g.ui,0);self.assertFalse(self.g.silence)
        self.assertTrue(self.lua.eval('next(rules)==nil and next(events)==nil'))
    def test_ui_has_only_volume_buttons(self):
        text=(ROOT/'berber_music.scar').read_text()
        self.assertEqual(text.count('<Button '),2)
        self.assertNotIn('WAV reference',text);self.assertNotIn('BDM_',text)

class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute((ROOT/'berber_music_policy.scar').read_text())
        self.p=self.lua.globals().BMPolicy
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
