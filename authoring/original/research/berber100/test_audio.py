"""Focused frame-order, source-selection and bitrate contract tests."""
from pathlib import Path
import unittest
from unittest.mock import patch
import audio_prepare as audio


class AudioTests(unittest.TestCase):
    def test_rotation_keeps_every_post_intro_frame_once(self):
        pcm = b''.join(i.to_bytes(4, 'little') for i in range(100))
        for entry in (10, 25, 40):
            rotated = audio.rotate_pcm(pcm, entry, skip=10)
            frames = [int.from_bytes(rotated[i:i + 4], 'little') for i in range(0, len(rotated), 4)]
            self.assertEqual(frames, list(range(entry, 100)) + list(range(10, entry)))
            self.assertEqual(sorted(frames), list(range(10, 100)))

    def test_invalid_rotation_rejected(self):
        for pcm, entry in ((b'x', 1), (bytes(400), 9), (bytes(400), 50)):
            with self.assertRaises(ValueError):
                audio.rotate_pcm(pcm, entry, skip=10)

    def test_real_catalog_has48_slots_and_prefers_wav_duplicate(self):
        root = Path(__file__).resolve().parents[2]
        selected, candidates, metadata = audio.inventory(root)
        self.assertEqual((len(selected), len(metadata)), (48, 48))
        self.assertEqual(selected['FA_B2'].suffix.lower(), '.wav')
        self.assertEqual(len(candidates['FA_B2']), 2)
        self.assertEqual(sum(p.suffix == '.flac' for p in selected.values()), 12)

    def test_bitrate_uses_audio_stream_not_cover_inflated_file_rate(self):
        run = type('Run', (), {'stderr': b'bitrate: 186 kb/s\nStream #0:0: Audio: mp3 (mp3float), 48000 Hz, stereo, fltp, 128 kb/s\n'})()
        with patch.object(audio.subprocess, 'run', return_value=run):
            self.assertEqual(audio.mp3_bitrate('source.mp3'), 128)


if __name__ == '__main__':
    unittest.main()
