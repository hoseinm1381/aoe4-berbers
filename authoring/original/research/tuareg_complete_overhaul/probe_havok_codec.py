"""Try the independent open-source Havok parser on a copy of native RHKA."""
from pathlib import Path
import json
import sys
import traceback
ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "output/tuareg_force_trial"
sys.path.insert(0, str(WORK / "codec_runtime"))
from soulstruct.havok import HKX
source = ROOT / "output/tuareg_shield_test/evidence/source/art/civilizations/common/humans/archetypes/base_spearshield/base_spearshield.rhka"
report = {"source": str(source), "dependency": "soulstruct-havok1.5.0, local target only", "native_resource_mutated": False}
try:
    model = HKX.from_path(source)
    report.update(status="parsed", version=model.hk_version, root_type=type(model.root).__name__)
except Exception as error:
    report.update(status="not_parsed", error_type=type(error).__name__, error=str(error))
    traceback.print_exc()
(WORK / "independent-codec-probe.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
