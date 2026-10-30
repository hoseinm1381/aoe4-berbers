"""Validate the maintained voice guidance and preserve compact review evidence."""
from pathlib import Path
from urllib.parse import unquote
import hashlib
import json
import re
import subprocess
import sys

SKILL = Path(r"C:\Users\RS\.codex\skills\aoe4-garrison-blender")
FILES = [SKILL / "SKILL.md"] + [SKILL / "references" / name for name in (
    "scripted-unit-voices.md", "native-voices.md", "music-and-audio.md", "packaging-and-catalog.md")]


def anchors(path):
    result = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^#{1,6}\s+", line):
            heading = re.sub(r"^#{1,6}\s+", "", line).strip().lower()
            result.add(re.sub(r"\s+", "-", re.sub(r"[^\w\-\s]", "", heading)))
    return result


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


checked = 0
errors = []
for path in FILES:
    text = path.read_text(encoding="utf-8")
    for destination in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", text):
        if re.match(r"^[a-z]+://", destination):
            continue
        target, _, fragment = unquote(destination).partition("#")
        resolved = (path.parent / target).resolve() if target else path
        checked += 1
        if not resolved.is_file():
            errors.append([str(path), destination, "missing file"])
        elif fragment and fragment not in anchors(resolved):
            errors.append([str(path), destination, "missing heading anchor"])
    assert not re.search(r"\bsk_[0-9a-f]{20,}", text), "Credential-like text found"
assert not errors, errors
validator = Path(r"C:\Users\RS\.codex\skills\.system\skill-creator\scripts\quick_validate.py")
validated = subprocess.run([sys.executable, "-B", str(validator), str(SKILL)], check=True, capture_output=True, text=True)
base = Path(r"F:\aoe_4_temp\Berber_future_kingdom_ai_20261014\output\berber_update_0_8_1")
report = json.loads((base / "release-validation.json").read_text(encoding="utf-8"))
for key in ("zip", "sga"):
    assert digest(Path(report[key])) == report[key + "_sha256"]
assert report["audible_villager_overlap"] == "operator_confirmed_resolved"
result = {
    "skill_root": str(SKILL), "modified_files": [str(p) for p in FILES],
    "quick_validate": validated.stdout.strip(), "local_links_and_anchors_checked": checked,
    "link_errors": errors, "file_sha256": {str(p.relative_to(SKILL)): digest(p) for p in FILES},
    "reference_lines": len((SKILL / "references/scripted-unit-voices.md").read_text(encoding="utf-8").splitlines()),
    "independent_forward_check": {
        "scenarios": ["Villager overlap after main speech removal", "normal playback versus unsupported native_speech", "duplicate ZIP manifest"],
        "result": "passed", "followup": "Old-companion comparison ambiguity clarified and independently rechecked"},
    "baseline_failures": "Observed 0.7.1 incomplete binding failures and 0.8.0 Villager overlap; 0.8.1 attachment repair confirmed by operator",
    "operator_confirmation_recorded": True, "delivery_hashes_unchanged": True,
    "memory_files_modified": False,
}
(Path(__file__).parent / "validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: result[k] for k in ("quick_validate", "local_links_and_anchors_checked", "reference_lines", "delivery_hashes_unchanged")}))
