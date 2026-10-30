# Berber1.0.3 reproduction

Use pinned final1.0.2 ZIP/SGA and the3changedSCAR files in scar/ai. baseline-source preserves their original bytes; full34shippedSCAR files and test fixtures remain here. No asset or audio recook.

Run Python3.13 with LupaLua51/Lua53:

    python -B research/berber103/audit.py
    python -B research/berber103/checks.py
    python -B research/berber103/build.py build
    python -B research/berber103/build.py verify
    python -B research/berber103/build.py cleanup

Build refuses to overwrite existing deliverables. To reproduce after delivery, select a fresh output directory and update the exact physical cleanup guard. MCP evidence: output/berber_update_1_0_3/mcp-checks.json. Re-run check_code on3modified files and api_context for new calls. Inherited low-confidence APIs and dynamic helper resolutions remain documented by1.0.2 function audit; review current function-audit.json. Native acceptance remains separate.
