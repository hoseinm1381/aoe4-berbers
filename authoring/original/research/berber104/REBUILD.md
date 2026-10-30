# Berber 1.0.4 reproduction

The authoritative base is final output/berber_update_1_0_3/Berber_future_kingdom.sga and its ZIP, pinned in build.py. The patch consists of seven native AI RGDs in compiled-ai and the frozen GM in scar/winconditions. Existing asset, audio and gameplay members come only from that release base; never substitute a raw project cook.

Use Python 3.13 with Lupa (the verified local interpreter is C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe), the installed Garrison sga-archiver, and the retained compatible archive reader used by research/berber0110/pipeline.py.

    python -B research/berber104/build.py checks
    python -B research/berber104/build.py compose
    python -B research/berber104/build.py verify
    python -B research/berber104/build.py cleanup

Composition refuses to overwrite an existing delivery. For independent reproduction, choose a new output directory, copy compiled-validation.json and mcp-check.json from the retained release evidence into it, and change the exact physical cleanup guard to that directory before running cleanup. compose creates its work directory and uses retained compiled-ai; it requires no asset/audio recook or restored historical cache. build additionally reads and validates a fresh native cook before composition.

To recook after cleanup, run cook.py prepare then cook.py build. prepare restores the retained cook-reference-inputs.zip snapshot and overlays source/attrib/instances. build uses cook-media-inputs.zip and the retained scoped _default.burnproj; only Mod Attributes is enabled. All reference/media ZIPs have hashes in cook-inputs.json and cook-media-inputs.json. Keep these snapshots, source XML, official extracted analogues and editor-identities.json; they are rebuild inputs, not disposable caches. The full author cook includes other attribute records for dependency validation; build.py selects only the seven AI records for delivery.

Do not rerun prepare.py --refresh during exact reproduction: it is the authoring generator and reads the current editable project. pre-review-inputs.zip preserves the superseded mapping inputs for provenance. Current source hashes are in mapping.json and are checked against the compiled readback record. New root and list identities came from installed Attribute Editor allocation classes; no PBG IDs were guessed.

Validation evidence is retained beside the ZIP: source-validation.json, compiled-validation.json, mcp-check.json, static-validation.json, archive/member proofs, release-validation.json, SHA256SUMS.txt, cook-evidence and cleanup reports. Native import and match acceptance are performed by the user using NATIVE_ACCEPTANCE.md.
