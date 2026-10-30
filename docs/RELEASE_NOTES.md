Berbers is independently selectable through Garrison. The owner confirmed trial.3 loaded and worked; version 0.1.0 preserves that gameplay and uses the original Villager banner for civilization presentation.

Players: download **Berbers-Garrison-0.1.0.zip**, import in Garrison client 0.1.9+, then choose Berbers / Standard / Tuning Pack: None.

Modders: clone main (or download the small editable-source ZIP), then run `python tools/inputs.py fetch`. The four input ZIPs below preserve native rebuild resources and required editable 3D art, textures, audio masters, projections and recipes. All are pinned by SHA-256. `python tools/build.py --output output/current` builds the player ZIP from this source set.

Validation: supported Garrison assembly, final all-member readback, native CRC/SHA1, ZIP CRC, packaged SGA hash, original art/audio preservation, numeric/Boolean preservation, standalone native flag recook and master restoration passed. Clean reduced-source reconstruction is recorded in the repository receipts.

The updated flag layout needs a fresh native visual retest. Detailed all-age mechanics, AI, repeated matches, save/load, multiplayer and performance remain separate acceptance gates. No runtime performance improvement is claimed from workspace cleanup.

Original credits: hossein81 and marcokistan (lead developers), Karyu and lammet (media), ForsakenCryz (original idea and civilization QA). Full original attribution is retained in the player notes and CREDITS.md.
