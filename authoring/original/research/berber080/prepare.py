"""Reuse accepted PCM recordings and prepare the normal-Garrison speech adapter."""
from pathlib import Path
import copy
import hashlib
import json
import re
import sys
import wave
from inspect_inputs import ROOT, SOURCE, OUT, HERE, extract, ARCH, rgd

sys.path.insert(0, str(ROOT / "research/berber060"))
from bindings import encode, semantic

OLD = ROOT / "output/berber_update_0_6_0"
AGE_NAMES = {1: "lowest", 2: "low", 3: "med", 4: "high"}
EVENTS = {"select": "select", "movesu": "movegc", "attack": "attack",
          "attackmovesu": "attack", "stop": "stop", "hold": "hold",
          "acknowledge": "acknowledge", "garrison": "garrison",
          "structurebuild": "structurebuild", "resourcegather": "resourcegather",
          "resourcewood": "resourcewood", "resourcemine": "resourcemine",
          "effortpain": "effortpain", "effortdeath": "effortdeath"}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def strip_speech(data, member):
    """Match the working scripted families; prove all non-speech data unchanged."""
    original = rgd.read(data)
    doc = copy.deepcopy(original)
    key = "squad_speech_ext" if "/sbps/" in member else "speech_ext"
    default = dict(rgd.flatten(doc.nodes))["default"]
    found = [(i, n) for i, n in enumerate(default.value) if n.key == key]
    assert len(found) == 1
    index, removed = found[0]
    default.value.pop(index)
    payload = encode(doc)
    parsed = rgd.read(payload)
    restored = copy.deepcopy(parsed)
    back = dict(rgd.flatten(restored.nodes))["default"]
    assert not any(n.key == key for n in back.value)
    back.value.insert(index, removed)
    assert semantic(restored.nodes) == semantic(original.nodes), member
    return payload, {"member": member, "removed_extension": key,
                     "removed_subtree": semantic([removed]), "semantic_undo": "passed"}


def prepare():
    OUT.mkdir(exist_ok=True)
    coverage = read(OLD / "coverage.json")
    accepted = {r["id"]: r for r in coverage["jobs"] if r["status"] == "accepted"}
    jobs = {j["id"]: j for j in read(ROOT / "art/voices_0_6_0/recording-plan.json")["jobs"]}
    civilian = [r for r in read(ROOT / "output/berber_update_0_6_1/audio-patch-validation.json")["selected_recordings"] if r["family"] == "villager"]
    base_bank = (SOURCE / "mod-source/scar/berber_voice_bank.scar").read_text(encoding="utf-8")
    rows, payloads, unavailable = [], {}, []

    def recording(job_id, family, action, age):
        c = accepted[job_id]
        receipt = OLD / "receipts" / (c["request_id"] + ".json")
        assert sha(receipt) == c["receipt_sha256"], str(receipt)
        r = read(receipt)
        assert r["job_id"] == job_id and r["status"] == "accepted_acoustic"
        source = Path(r["native_path"])
        digest = sha(source)
        assert digest == c["native_sha256"] and sha(Path(r["source"])) == r["source_sha256"]
        j = jobs[job_id]
        if action.startswith("effort"):
            assert j["script"].get("nonverbal"), "Efforts must be nonverbal recordings"
        with wave.open(str(source), "rb") as w:
            assert (w.getnchannels(), w.getframerate(), w.getsampwidth(), w.getcomptype()) == (1, 48000, 2, "NONE")
            duration = w.getnframes() / 48000
        member = "audio/voices/" + digest + ".wav"
        payloads[member] = {"member": member, "source": str(source), "sha256": digest, "bytes": source.stat().st_size}
        rows.append({"family": family, "action": action, "unit_age": age,
                     "recorded_age": j["age"], "event": j["event"], "delivery": j["delivery"],
                     "take": j["take"], "job_id": job_id, "request_id": c["request_id"],
                     "receipt": str(receipt), "receipt_sha256": c["receipt_sha256"],
                     "source": str(source), "member": member, "sha256": digest,
                     "duration_seconds": duration, "nonverbal": j["script"].get("nonverbal", False)})
        return member, duration

    def choose(family, action, event, age):
        options = []
        if family == "villager":
            options = [jobs[r["source_job"]] for r in civilian if r["event"] == event and r["source_job"] in accepted]
        else:
            options = [j for j in jobs.values() if j["id"] in accepted and j["family"] == family and j["event"] == event and j["age"] == ("none" if event.startswith("effort") else AGE_NAMES[age])]
        preferred = "high" if event.startswith("effort") else "norm"
        preferred_options = [j for j in options if j["delivery"] == preferred]
        if not preferred_options and event.startswith("effort"):
            preferred_options = [j for j in options if j["delivery"] == "none"]
        options = sorted(preferred_options, key=lambda j: (j["take"], j["id"]))
        if not options:
            unavailable.append({"family": family, "action": action, "age": age, "reason": "No exact accepted event/age/preferred-delivery recording; no unrelated substitution"})
            return []
        limit = 1 if family == "villager" else (2 if event.startswith("effort") else 3)
        return [recording(j["id"], family, action, age) for j in options[:limit]]

    def family_table(family, age):
        result = {}
        for action, event in EVENTS.items():
            if family == "tuareg" and event.startswith("resource"):
                continue
            result[action] = choose(family, action, event, age)
        return {k: v for k, v in result.items() if v}

    def table_text(table):
        return "\n".join('["' + action + '"]={' + ",".join('{"' + path + '",' + f"{duration:.6f}" + '}' for path, duration in clips) + "}," for action, clips in sorted(table.items()))

    villager = family_table("villager", 0)
    ages = {age: family_table("tuareg", age) for age in AGE_NAMES}
    bank = base_bank
    for family, table in (("villager", villager), ("tuareg", ages[1])):
        pattern = r'^\["' + family + r'"\]=\{\n.*?^\},'
        bank, count = re.subn(pattern, '["' + family + '"]={\n' + table_text(table) + "\n},", bank, flags=re.M | re.S)
        assert count in (0, 1)
        if count == 0:
            bank += '\nBerberVoiceBank.clips["' + family + '"]={\n' + table_text(table) + "\n}\n"
    age_names = {f"unit_spearman_tuareg_{age}_ber": age for age in AGE_NAMES}
    bank += "\n-- Tuareg dialogue follows its actual age-tier squad blueprint; efforts are shared.\n"
    bank += "BerberVoiceBank.age_clips={tuareg={\n" + "\n".join(f"[{age}]={{\n" + table_text(table) + "\n}," for age, table in ages.items()) + "\n}}\n"
    dispatcher = (SOURCE / "mod-source/scar/berber_scripted_speech.scar").read_text(encoding="utf-8")
    for old, new in [
        ('local nativeSpeech=Garrison.speech.forMod("berber_future_kingdom")\n', ""),
        ('if not f or f=="villager" or f=="tuareg" then return nil end', 'if not f then return nil end'),
        ('    nativeSpeech.pulse()\n', ""),
        ('    print("BERBER_NATIVE_SPEECH ready="..tostring(nativeSpeech.start()))\n', ""),
        ('    nativeSpeech.stop()\n', ""),
        ('version=native-speech.1', 'version=0.8.0'),
    ]:
        assert dispatcher.count(old) == 1, old
        dispatcher = dispatcher.replace(old, new)
    old = "    local choices=bank.clips[r.family] and bank.clips[r.family][event]"
    new = '''    local clips=bank.clips[r.family]
    if bank.age_clips and bank.age_clips[r.family] then
        local age=tonumber(string.match(BP_GetName(r.blueprint),"unit_spearman_tuareg_(%d)_ber"))
        if age and bank.age_clips[r.family][age] then clips=bank.age_clips[r.family][age] end
    end
    local choices=clips and clips[event]'''
    assert dispatcher.count(old) == 1
    dispatcher = dispatcher.replace(old, new)
    assert "nativeSpeech" not in dispatcher and "Garrison.speech" not in dispatcher
    (HERE / "berber_scripted_speech.scar").write_text(dispatcher, encoding="utf-8")
    (HERE / "berber_voice_bank.scar").write_text(bank, encoding="utf-8")
    patches, changes = {}, []
    for row in read(SOURCE / "evidence/restored-native-bindings.json"):
        member = row["member"]
        path = extract(member)
        data, proof = strip_speech(path.read_bytes(), member)
        target = OUT / "payloads" / member
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        patches[member] = str(target)
        changes.append(proof)
    report = {"base_sga": str(SOURCE / "berber_future_kingdom.sga"), "base_sha256": sha(SOURCE / "berber_future_kingdom.sga"),
              "recordings": rows, "unique_pcm_payloads": list(payloads.values()), "binding_changes": changes,
              "unavailable_contexts": unavailable, "paid_requests": 0,
              "villager_variations": 1, "villager_ages_shared": True,
              "tuareg_age_mapping": age_names,
              "native_suppression": "Matches table-removal layout of user-tested other families; Villager/Tuareg audible overlap still requires test"}
    (OUT / "voice-inputs.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    listing = {**patches, "scar/berber_scripted_speech.scar": str(HERE / "berber_scripted_speech.scar"), "scar/berber_voice_bank.scar": str(HERE / "berber_voice_bank.scar")}
    listing.update({member: data["source"] for member, data in payloads.items()})
    (OUT / "payload-files.json").write_text(json.dumps(listing, indent=2) + "\n")
    print(json.dumps({"unique_clips": len(payloads), "villager_actions": len(villager), "tuareg_age_actions": {age: len(table) for age, table in ages.items()}, "unavailable": unavailable}, indent=2))
    return report


if __name__ == "__main__":
    prepare()
