# Berber Dark Age music Test2

Test1 music and HUD confirmed working by user2026-10-18; rollback preserved.
Test2 new random-entry behavior needs user native test.

All logical track transitions (peace,combat,theme) choose one of10seconds,
25percent or40percent of original duration. Original first10seconds are removed
from subsequent looping playback. Only initial Atlas Peace uses intro_a1.mp3
from beginning. Mute/retry/restore retain entry. Private presentation PRNG never
uses simulation RNG. Consecutive transitions avoid repeating the same position.
WAV diagnostic reference uses fixed10second entry. Opening retires0.5s before
nominal loop boundary; muting/restoring it prevents reusing the original intro.
22tests pass, including opening interruption regressions.

Rebuild: frozen0100SGA/ZIP + this folder + research/berber0100/pipeline.py,
all12 retained FLAC/compact MP3s and catalog/size-validation in
art/music_dark_age_20261018. entry_audio.py regenerates36 MP3 entry variants
from lossless FLAC, verifies source PCM and full decoded frame counts.
Only GM gains import; three music SCARs,37MP3s and one WAV are added.
Original AI/art/tuning/audio/UV repairs remain byte-identical.

Python3.13/lupa.lua51+lua53, FFmpeg7.1, installed Garrison archiver and
pipeline.READER required. Run Python -B research/dark_age_music_test_2/test_music.py.
For new iteration change OUT/ZIP/VERSION/exact physical cleanup guard first.
Then build.py build, inspect validation, build.py cleanup. Existing finalSGA
and ZIP cannot be overwritten. verify action rechecks final hash/ZIP.

Cleanup only verified F: output/berber_dark_age_music_test_2/work after delivery
validation; retain all masters/scripts/reports/finalSGA/ZIP and Test1 rollback.
No large PCM caches needed: FFmpeg regenerates in memory from retained FLAC.
Music shares speech endpoint without calling session/stop/pulse.
Native audio seams, pause/speed/save/load and multiplayer remain separate gates.
