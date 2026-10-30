import unittest
from jobs import take_count,text_override_prompt


class NativeTakeLimits(unittest.TestCase):
    def test_frequent_orders_include_stop_hold_and_combat_crew_orders(self):
        for event in ('stop','hold','charge','weaponfire','weaponaim','select','attackground','movegc',
                      'resourcewood','resourcemine','resourcefarm','structurebuild','structurerepair','healorder'):
            with self.subTest(event=event):self.assertEqual(take_count(event,8),3)

    def test_rare_reactions_and_efforts_have_two(self):
        for event in ('effortpain','effortdeath','celebrate','reacthelp'):
            with self.subTest(event=event):self.assertEqual(take_count(event,8),2)

    def test_native_selectability_caps_the_target(self):
        self.assertEqual(take_count('stop',1),1)
        self.assertEqual(take_count('select',2),2)
        self.assertEqual(take_count('effortpain',1),1)

    def test_text_override_default_delivery_is_unchanged(self):
        text='تَوَقَّفُوا هُنَا'
        self.assertEqual(text_override_prompt(text,'norm'),text)
        self.assertEqual(text_override_prompt(text,'high'),'[shouting] '+text)
        self.assertEqual(text_override_prompt(text,'stealth'),'[whispering] '+text)

    def test_explicit_angry_preserves_exact_arabic_words_and_vowels(self):
        text='تَوَقَّفُوا هُنَا'
        self.assertEqual(text_override_prompt(text,'high',combat_tag='angry'),'[angry] '+text)

    def test_combat_tag_rejects_other_delivery_nonverbal_and_unapproved_tags(self):
        for delivery in ('norm','stealth','none'):
            with self.subTest(delivery=delivery),self.assertRaises(ValueError):
                text_override_prompt('توقفوا',delivery,combat_tag='angry')
        with self.assertRaises(ValueError):text_override_prompt('توقفوا','high',combat_tag='angry',nonverbal=True)
        for tag in ('shouting','happy','ANGRY','',True):
            with self.subTest(tag=tag),self.assertRaises(ValueError):text_override_prompt('توقفوا','high',combat_tag=tag)


if __name__=='__main__':unittest.main()
