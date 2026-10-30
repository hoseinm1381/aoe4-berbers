# Berber Dark Age music test1 - rebuild and evidence

Delivery: output/berber_dark_age_music_test_1/Berber-Dark-Age-Music-Test-1.zip
Version0.10.0-music.1 is a test candidate, not the other agent's AI redesign.
Use NORMAL GAME SPEED for the first soundtrack test.

Frozen0100SGA SHA256:
6cd768459540576754946f47f51f3e93ef6e974814149ea9f01d5cc93206de0c
BaselineZIP SHA256:
086e656592d3e75d29d25c6237e2789f0b820476ad638ba573e7e3d77ab95088

Only the packaged GM gains one import. Three isolated musicSCAR files,12 MP3s
and one48kHz stereo16PCM A1 WAV reference are new. Every existing AI/art/tuning/
audio/speech member is byte-identical. Editable assets/scar/AI is never read
into the payload. No Content Editor recook is needed for raw SCAR/external audio.
Same mod/bundle identity avoids duplicate gameGUIDs: importing temporarily
replaces installed Berber. Reimport the retained0100ZIP to remove this test.

Required retained inputs:
- This folder's controller, policy, catalog, test_music.py and build.py.
- fixtures/garrison.scar: exact frozen endpoint for Lua5.3 packet tests only.
- art/music_dark_age_20261018/compact_mp3:12 stereo192kbps source recordings.
- art/music_dark_age_20261018/lossless/DA_A1.flac: generates reference WAV.
- That music folder's catalog.json and size-validation.json: PCM/asset hashes.
- Frozen0100SGA/ZIP and research/berber0100/pipeline.py.
- Installed Garrison archiver, Python3.13/lupa.lua51+lua53, FFmpeg7.1.
- Compatible read-only SGA reader from pipeline.READER; native exact readback
  is the fallback. No large extracted art cache is retained.

Commands from project root with verified Python3.13 and -B:
  research/dark_age_music_test/test_music.py
  research/dark_age_music_test/build.py verify
For a NEW iteration update OUT, ZIP, VERSION and the exact cleanup path guard
in build.py, preserving current outputs. Then build.py build, focused SCAR/MCP
checks, inspect proofs and build.py cleanup. Never overwrite current delivery.

Output uses the existing F: junction. Cleanup removes only inventoried test/work:
payload/reference WAV, tiny baseline extracts and unpublished case probe SGA.
FinalSGA/ZIP, source scripts/fixture, compact evidence and all music inputs stay.

Sixteen checks pass:14 Lua5.1 controller/policy mocks and2 Lua5.3 checks of the
exact shipped endpoint. Source validation0errors; two endpoint-alias warnings
resolve to that loader. MCP parser-only names resolve to local policy/controller
or endpoint methods. All8389 decoded member hashes, archiveCRC/SHA1 and ZIPCRC/
member checks passed.8372 existing members unchanged; GM import only;16new.
Fresh read-only review found no confirmed important blocker.

Native HUD, MP3 playback, live gain, loops/transitions, pause/speed/save/load and
multiplayer remain PENDING. See output MUSIC_TEST_REPORT.txt. 'Submitted' means
no transport exception, not audible success. BerberSpeech owns session/heartbeat:
music never resets/stops it. setBedGain exists in the actual shipped loader,
newer than the skill's older documented baseline; live gain is a native test gate.
