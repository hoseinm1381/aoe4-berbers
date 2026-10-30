# Berber 0.9.1 UV repair plan

User scope: repair all 22 flagged RRGeom files, preserve current models and
gameplay, package 0.9.1. Execute inline in isolated release-owned directories;
the dirty editable project and Blender work are not inputs or edit targets.

1. Freeze final 0.9.0 SGA identity and reproduce the 22 non-finite UV failures.
2. Resolve each original official donor from retained source recipes. Confirm
   stream layout, vertex order, topology and donor identity before copying UVs.
   Restore donor UV0 spans only; no guessed zeros or geometry replacement.
3. Prove every changed byte belongs to an approved UV0 span, all donor UVs are
   finite, and positions/normals/tangents/skin/indices/chunks are unchanged.
   Reject ambiguous correspondence and unrelated archive changes.
4. Compose from final090, replace exactly 22 RRGeom members, and read back all
   archive members. Compare every unchanged decoded member by SHA-256; verify
   native CRC/SHA1 and all22 finite-UV checks.
5. Package one 0.9.1 ZIP, carrying forward current090 metadata and audio. Remove
   the obsolete22-UV warning, record actual limitations and runtime pending.
6. Preserve recipe/scripts, donor provenance and compact proofs. Verify delivery,
   inventory release-owned regenerable work copies, check junctions/dependencies,
   clean only those copies, recheck hashes/ZIP, update rebuild/storage handoff.

Native import, visual appearance and gameplay acceptance remain separate.
