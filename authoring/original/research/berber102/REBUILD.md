# Berber 1.0.2 reproduction

Use exact final1.0.1 SGA/ZIP, pinned by SHA-256 in build.py. The2patch members
are scar/ai/berber_ai_navigation.scar and scar/ai/berber_ai_military.scar.
The entire34-member shipped SCAR tree is frozen in scar/ for auditing and
tests. baseline-source/ retains the two original1.0.1 files. No art/audio/tuning
recook is required. Keep all earlier pinned build-chain inputs and source bundles.

Run with verified Python3.13 and LupaLua51/Lua53:

    python -B research/berber102/audit.py
    python -B research/berber102/checks.py
    python -B research/berber102/simulation.py
    python -B research/berber102/build.py checks
    python -B research/berber102/finish_audit.py

MCP evidence is preserved in output/berber_update_1_0_2/mcp-symbol-audit.json
and mcp-file-checks.json. Re-run api_context for every native/wrapper symbol,
inspect_symbol for lower-confidence contracts and check_code for each shipped
SCAR when code or the official API library changes. audit-resolution.json
explains dynamic names and all static warnings; it is not native acceptance.

build.py build refuses to overwrite a release. To reproduce after delivery,
select a new empty output folder and update the explicit physical cleanup guard.
It composes exactly2members on frozen1.0.1, hashes every decoded archive member,
checks no additions/removals, verifies native archive CRC/SHA1, packages the
inherited identity and cover, and compares ZIP-contained SGA SHA-256.

    python -B research/berber102/build.py verify
    python -B research/berber102/build.py cleanup

Cleanup inventories exact release-owned work, protects base/final and source
inputs by hashes, rejects reparse points and removes only the verified work
folder. Full34shipped sources, test fixtures, original2baseline members and
reports remain available. Native match acceptance follows RELEASE_NOTES.md.
