"""Private Berber 0.5.0 civilian/support/ruler art source generator.

Generates donor-pinned recipes, native geometry candidates and masked albedo
sources for review. It never cooks or edits live mod resources.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

from berber_050_unit_pipeline import remix, source_geometry

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/unit_remix_0_5_0/civilian"
DONORS = ROOT / "output/berber_update_0_5_0/donors.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def family_donors():
    data = json.loads(DONORS.read_text(encoding="utf8"))["families"]
    for family, source, ages in (
        ("villager", "villager_abbasid_alternatives", (1, 2, 3, 4)),
        ("imam", "imam_regional_alternatives", (3, 4)),
        ("king", "king_regional_alternatives", (1, 2, 3, 4)),
    ):
        for age in ages:
            # Official King consumer uses the age-IV model at every age.
            donor_age = 4 if family == "king" else age
            donor = next(d for d in data[source]["donors"] if d["age"] == donor_age and
                         ("sultanate" in d["logical_path"] if family == "imam" else
                          "abbasids" in d["logical_path"] if family == "king" else True))
            yield family, age, donor


def trader_exact_donors():
    data=json.loads(DONORS.read_text(encoding="utf8"))["families"]["trader"]["donors"]
    for age in (2,3,4):
        for sex in ("male","female"):
            candidates=[d for d in data if d["age"]==age and "mal_horse_combined_trade" in d["logical_path"]
                        and ("_female_" in d["logical_path"]) == (sex=="female")]
            if len(candidates)!=1:
                raise ValueError(f"Expected one exact horse Trader donor {age}/{sex}; found {len(candidates)}")
            yield age,sex,candidates[0]


def window(kind, z, metres, **kw):
    return {"kind": kind, "z_window": z, "center_xy": [0, 0],
            "radius_xy": [1, 1], "radial_window": [0, 0.01, 0.9, 2],
            "metres": metres, **kw}


def features(family, age, group):
    name = group["name"].lower()
    if family == "trader":
        material = group["material"].lower()
        if "gold" in name or "horse_trade" in name:
            return []
        if "equipment" in name or "cart" in material or "equipment" in material:
            # Pannier/cargo covers only: horse, wheels and gold stay intact.
            return [window("radial_expand", [0.92, 1.08, 1.54, 1.78],
                           0.055 + 0.005*(age-2),
                           y_window=[-0.18, -0.03, 0.7, 0.86])]
        if "rider" in material or "cavalry_trade" in name:
            return [window("lateral_expand", [0.46, 0.56, 0.8, 0.94],
                           0.045 + 0.005*(age-2), abs_x_window=[0.07, 0.14, 0.33, 0.42]),
                    window("radial_expand", [1.61, 1.68, 1.79, 1.86], 0.028,
                           abs_x_window=[0, 0.01, 0.17, 0.22])]
        return []
    if family == "villager":
        return [window("lateral_expand", [0.47, 0.56, 0.78, 0.94],
                       0.045 + 0.005*(age-1), abs_x_window=[0.06, 0.13, 0.34, 0.42]),
                window("radial_expand", [1.61, 1.67, 1.79, 1.86],
                       0.027 + 0.002*(age-1), abs_x_window=[0, 0.01, 0.18, 0.23]),
                window("lateral_expand", [1.08, 1.16, 1.32, 1.46],
                       0.018, abs_x_window=[0.28, 0.33, 0.5, 0.58])]
    if family == "imam":
        return [window("lateral_expand", [0.25, 0.38, 0.7, 0.93],
                       0.055 + 0.005*(age-3), abs_x_window=[0.05, 0.11, 0.36, 0.46]),
                window("radial_expand", [1.55, 1.64, 1.81, 1.95], 0.033,
                       abs_x_window=[0, 0.01, 0.19, 0.25])]
    if family == "king":
        return [window("lateral_expand", [0.43, 0.55, 0.88, 1.05],
                       0.036 + 0.009*(age-1), abs_x_window=[0.04, 0.1, 0.35, 0.46]),
                window("radial_expand", [1.55, 1.65, 1.91, 2.08],
                       0.025 + 0.004*(age-1), abs_x_window=[0, 0.01, 0.2, 0.27])]
    raise ValueError(family)


def albedo(manifest, out: Path, family: str, age: int, slot: str = "body"):
    materials = manifest["material"]["materials"]
    if family == "trader":
        group = next(g for g in manifest["geometry"]["groups"] if
                     ("cart" in g["material"] if slot == "cargo" else "cavalry_trade" in g["name"] and
                      (g["material"].replace("_", "") == "lod1" or "rider" in g["material"] and "lod1" in g["material"])))
        mat = next(m for m in materials if m["name"] == group["material"])
    else:
        mat = next(m for m in materials if m["name"].replace("_", "") == "lod1")
    tex = next(t for t in mat["textures"] if t["name"] == "albedoTexture")
    pattern = next((t for t in mat["textures"] if t["name"] == "patternTex"), None)
    src = Path(tex["projection_path"])
    mask_path = Path(pattern["projection_path"]) if pattern and pattern["projection_path"] else None
    image = Image.open(src).convert("RGBA")
    mask = Image.open(mask_path).convert("RGB") if mask_path and mask_path.is_file() else None
    if mask and mask.size != image.size:
        mask = mask.resize(image.size, Image.Resampling.NEAREST)
    pix = image.load()
    mpix = mask.load() if mask else None
    # Project native LOD1 UV triangles by their actual 3D garment height.
    # Feet, sandals and waist leather are protected even when their albedo
    # happens to be pale enough for a simple colour selector.
    protect = Image.new("L", image.size, 0)
    pd = ImageDraw.Draw(protect)
    for group in manifest["geometry"]["groups"]:
        if group["material"] != mat["name"]:
            continue
        uv = group["uv_layers"]["UVMap"]
        pos = group["positions"]
        for tri in group["triangles"]:
            z = sum(pos[i][2] for i in tri)/3
            coords = [(uv[i][0]*(image.width-1),(1-uv[i][1])*(image.height-1)) for i in tri]
            if z < 0.23:
                pd.polygon(coords,fill=255)
    protected_px = protect.load()
    # Restrained indigo, ochre, and cream progression. Keep masked owner/skin
    # lanes completely untouched, including the pattern source itself.
    palette = ({"cargo": ((0.40, 0.61, 0.82), (0.55, 0.67, 0.72), (0.78, 0.65, 0.43))}["cargo"][age-2]
               if slot == "cargo" else {
        "villager": ((0.61, 0.77, 0.93), (0.68, 0.79, 0.92), (0.56, 0.7, 0.83), (0.48, 0.63, 0.8)),
        "imam": ((0.65, 0.75, 0.9), (0.55, 0.67, 0.84)),
        "trader": ((0.81, 0.79, 0.66), (0.76, 0.75, 0.69), (0.72, 0.72, 0.73)),
        "king": ((0.92, 0.84, 0.65), (0.50, 0.66, 0.45), (0.43, 0.69, 0.88), (0.24, 0.43, 0.73)),
    }[family][age - {"villager":1,"imam":3,"trader":2,"king":1}[family]])
    changed = 0
    for y in range(image.height):
        for x in range(image.width):
            r,g,b,a = pix[x,y]
            if protected_px[x,y] and (family != "villager" or
                                      (r > g*1.03 and r > b*1.02)):
                continue
            if a < 16 or max(r,g,b) < 35 or min(r,g,b) < 12:
                continue
            if mpix:
                mr,mg,mb = mpix[x,y]
                if max(mr,mg,mb) > 100 and max(mr,mg,mb) > 1.35*min(mr,mg,mb):
                    continue
            if family == "trader":
                # The combined horse has two independent native atlases. In
                # the equipment atlas the burgundy saddle blanket occupies
                # this UV island; baskets, rope and horse tack occupy others.
                # In each rider atlas the large lower-left island is garment
                # cloth (male trousers / female lower robe), not skin or gear.
                # The apparently burgundy cargo island wraps the woven
                # basket, not a saddle blanket. Preserve that complete atlas.
                cargo_cloth = False
                female = "female" in tex["logical_path"]
                cloth_island = ((x > image.width*0.36 and y > image.height*0.85)
                                if female and age == 4 else
                                (x < image.width*(0.66 if female else 0.61) and
                                 y > image.height*0.54))
                rider_cloth = (slot == "body" and cloth_island and
                               r > g*1.13 and r > b*1.12)
                if cargo_cloth or rider_cloth:
                    cloth_rgb = {
                        2: (0.28, 0.43, 0.69),
                        3: (0.48, 0.62, 0.52),
                        4: (0.38, 0.54, 0.76),
                    }[age]
                    # Preserve weave and folds while lifting dark burgundy
                    # enough that the new fabric reads in the LOD1 preview.
                    value = min(230, max(72, 0.7*max(r,g,b)+45))
                    q = tuple(round(value*c) for c in cloth_rgb)
                    if max(abs(q[i]-(r,g,b)[i]) for i in range(3)) >= 9:
                        pix[x,y] = (*q,a)
                        changed += 1
                    continue
                # No broad neutral recolour on combined mounted atlases:
                # it also changes basket weave, cargo, skin and horse tack.
                continue
            # Restrict to cloth-like neutral/tan atlas regions; leather/skin
            # colours are left alone by the chroma and warmth tests.
            if max(r,g,b)/max(1,min(r,g,b)) > 2.05:
                continue
            headcloth = (family == "villager" and x < image.width*0.66 and
                         y > image.height*0.62 and r > g*1.18 and r > b*1.12)
            # Warm brown leather covers belts, sandals and straps on these
            # atlases. The villager headwrap is the one intentional exception.
            robe_king = (family == "king" and 0.33*image.width < x < 0.75*image.width and
                         0.27*image.height < y < 0.89*image.height and
                         r > g*1.13 and g > b*1.16 and r < 165)
            if r > g*1.10 and r > b*1.07 and not (headcloth or robe_king):
                continue
            pixel_palette = palette
            if family == "imam" and age == 3 and x < image.width*0.76 and y > image.height*0.84:
                # Sultanate monk atlas places the unmasked lower robe here;
                # use a sand-coloured cloth panel below the slate outer robe.
                pixel_palette = (0.94, 0.83, 0.64)
            lum = 0.2126*r+0.7152*g+0.0722*b
            factor = 0.74 + 0.26*min(1,lum/160)
            q = tuple(round(max(0,min(255,lum*c*factor))) for c in pixel_palette)
            if max(abs(q[i]-(r,g,b)[i]) for i in range(3)) < 9:
                continue
            pix[x,y] = (*q,a)
            changed += 1
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out)
    return {"source":str(src),"source_sha256":digest(src),"pattern_source":str(mask_path) if mask_path else None,
            "pattern_sha256":digest(mask_path) if mask_path else None,
            "output_sha256":digest(out),"changed_pixels":changed,
            "source_texture":tex["logical_path"],
            "donor_albedo_texture_id":Path(tex["logical_path"]).stem.split("_")[0],
            "owner_colour_mask":"native unchanged; two-player native preview pending"}


def prepare_one(family, age, donor, name_override=None):
    name=name_override or f"{family}_age0{age}"
    out=ART/family/name
    out.mkdir(parents=True,exist_ok=True)
    path=ROOT/donor["decoded_manifest"]
    manifest=json.loads(path.read_text(encoding="utf8"))
    source=source_geometry(path,manifest)
    groups=[]
    for i,g in enumerate(manifest["geometry"]["groups"]):
        if g["stream"] != "UnitDataStream":
            continue
        f=features(family,age,g)
        if f:
            groups.append({"index":i,"features":f,"max_displacement_metres":0.09,
                           "contain_within_donor_bounds":True,"max_clipped_fraction":0.28})
    if not groups:
        raise ValueError(f"No supported garment groups: {name}")
    palette=albedo(manifest,out/"candidate-albedo.png",family,age)
    cargo=albedo(manifest,out/"candidate-cargo-albedo.png",family,age,"cargo") if family == "trader" else None
    recipe={"schema":"berber-050-unit-geometry/v1","name":name,
            "output_dir":str(out.relative_to(ROOT)),
            "manifest":str(path.relative_to(ROOT)),"manifest_sha256":digest(path),
            "logical_path":donor["logical_path"],"geometry_sha256":digest(source),
            "design":f"{family} age {age}: regional layered cloth/headwear and restrained progression; native rig, tools and states retained",
            "groups":groups,"preview_albedo":"candidate-albedo.png",
            "donor_albedo_texture_id":palette["donor_albedo_texture_id"]}
    if cargo:
        recipe["preview_albedos"]={palette["donor_albedo_texture_id"]:"candidate-albedo.png",
                                   cargo["donor_albedo_texture_id"]:"candidate-cargo-albedo.png"}
    (out/"recipe.json").write_text(json.dumps(recipe,indent=2)+"\n",encoding="utf8")
    report=remix(out/"recipe.json")
    (out/"material-source.json").write_text(json.dumps(palette,indent=2)+"\n",encoding="utf8")
    if cargo:
        (out/"material-source-cargo.json").write_text(json.dumps(cargo,indent=2)+"\n",encoding="utf8")
    print(name,report["output_sha256"],[(g["index"],g["edited_fraction"]) for g in report["groups"]],flush=True)


def villager_manifest():
    donors = {(f,a):d for f,a,d in family_donors()}
    rows=[]
    for age in (1,2,3,4):
        name=f"villager_age0{age}"
        out=ART/"villager"/name
        donor=donors["villager",age]
        sources={
            "geometry_recipe":out/"recipe.json",
            "authored_rrgeom":out/(name+".rrgeom"),
            "geometry_report":out/"geometry-report.json",
            "editable_blend":out/(name+".blend"),
            "authored_albedo":out/"candidate-albedo.png",
            "material_source":out/"material-source.json",
            "preview_donor_lod1":out/"textured-donor.png",
            "preview_candidate_lod1":out/"textured-candidate.png",
            "preview_team_red":out/"textured-team-red.png",
            "preview_team_blue":out/"textured-team-blue.png",
        }
        missing=[key for key,path in sources.items() if not path.is_file()]
        if missing:
            raise FileNotFoundError(f"{name} missing {missing}")
        material=json.loads(sources["material_source"].read_text(encoding="utf8"))
        row={"family":"villager","age":age,"private_variant_name":name,
             "private_resource_stem":f"art/scenario/garrison/berber_units_050/{name}/{name}",
             "official_donor_rgm":donor["logical_path"],
             "official_donor_rgm_sha256":donor["native_resource_sha256"],
             "decoded_manifest":donor["decoded_manifest"],
             "decoded_manifest_sha256":digest(ROOT/donor["decoded_manifest"]),
             "native_source_rrgeom_sha256":json.loads(sources["geometry_report"].read_text(encoding="utf8"))["source_sha256"],
             "owner_pattern_source":material["pattern_source"],
             "owner_pattern_source_sha256":material["pattern_sha256"],
             "native_material_cook":"pending root serial cook",
             "native_animation":"unverified",
             "native_team_colour":"unverified; red and blue shader previews only"}
        for key,path in sources.items():
            row[key]=str(path.relative_to(ROOT))
            row[key+"_sha256"]=digest(path)
        rows.append(row)
    target=ART/"villager"/"villager-manifest.json"
    target.write_text(json.dumps({"schema":"berber-050-civilian-art/v1",
                                  "status":"villager_source_ready_native_cook_pending",
                                  "villager":rows,
                                  "excluded_technical_probes":["imam","trader","king"]},indent=2)+"\n",encoding="utf8")
    print(target,flush=True)


def regional_manifest(family: str):
    if family not in ("imam","king"):
        raise ValueError(family)
    rows=[]
    for f,age,donor in family_donors():
        if f != family:
            continue
        name=f"{family}_age0{age}"
        out=ART/family/name
        sources={
            "geometry_recipe":out/"recipe.json",
            "authored_rrgeom":out/(name+".rrgeom"),
            "geometry_report":out/"geometry-report.json",
            "editable_blend":out/(name+".blend"),
            "authored_albedo":out/"candidate-albedo.png",
            "material_source":out/"material-source.json",
            "preview_donor_lod1":out/"textured-donor.png",
            "preview_candidate_lod1":out/"textured-candidate.png",
            "preview_team_red":out/"textured-team-red.png",
            "preview_team_blue":out/"textured-team-blue.png",
        }
        missing=[k for k,p in sources.items() if not p.is_file()]
        if missing:
            raise FileNotFoundError(f"{name} missing {missing}")
        receipt=json.loads(sources["geometry_report"].read_text(encoding="utf8"))
        material=json.loads(sources["material_source"].read_text(encoding="utf8"))
        manifest=ROOT/donor["decoded_manifest"]
        recipe=json.loads(sources["geometry_recipe"].read_text(encoding="utf8"))
        if digest(manifest) != recipe["manifest_sha256"]:
            raise ValueError(f"{name} decoded donor pin changed")
        row={"family":family,"age":age,"private_variant_name":name,
             "private_resource_stem":f"art/scenario/garrison/berber_units_050/{name}/{name}",
             "official_donor_rgm":donor["logical_path"],
             "official_donor_rgm_sha256":donor["native_resource_sha256"],
             "decoded_manifest":donor["decoded_manifest"],
             "decoded_manifest_sha256":digest(manifest),
             "native_source_rrgeom_sha256":receipt["source_sha256"],
             "owner_pattern_source":material["pattern_source"],
             "owner_pattern_source_sha256":material["pattern_sha256"],
             "official_animation_owner":"base_monk" if family=="imam" else "base_swordsman",
             "native_material_cook":"pending root serial cook",
             "native_animation":"unverified",
             "native_team_colour":"unverified; red and blue shader previews only"}
        for key,path in sources.items():
            row[key]=str(path.relative_to(ROOT))
            row[key+"_sha256"]=digest(path)
        rows.append(row)
    target=ART/family/(family+"-manifest.json")
    target.write_text(json.dumps({"schema":"berber-050-civilian-art/v1",
                                  "status":f"{family}_source_ready_native_cook_pending",
                                  family:rows,
                                  "rejected_technical_probes":str((ART/family/"probes").relative_to(ROOT))},indent=2)+"\n",encoding="utf8")
    print(target,flush=True)


def trader_manifest():
    """Register the six exact horse consumers without collapsing native sex selection."""
    rows=[]
    for age,sex,donor in trader_exact_donors():
        name=f"trader_age0{age}"+("_female" if sex=="female" else "")
        out=ART/"trader"/name
        sources={
            "geometry_recipe":out/"recipe.json",
            "authored_rrgeom":out/(name+".rrgeom"),
            "geometry_report":out/"geometry-report.json",
            "editable_blend":out/(name+".blend"),
            "authored_albedo":out/"candidate-albedo.png",
            "authored_cargo_albedo":out/"candidate-cargo-albedo.png",
            "material_source":out/"material-source.json",
            "cargo_material_source":out/"material-source-cargo.json",
            "preview_donor_rider_only":out/"textured-donor-rider.png",
            "preview_candidate_rider_only":out/"textured-candidate-rider.png",
            "preview_donor_lod1":out/"textured-donor.png",
            "preview_candidate_lod1":out/"textured-candidate.png",
            "preview_team_red":out/"textured-team-red.png",
            "preview_team_blue":out/"textured-team-blue.png",
        }
        missing=[k for k,path in sources.items() if not path.is_file()]
        if missing:
            raise FileNotFoundError(f"{name} missing {missing}")
        manifest_path=ROOT/donor["decoded_manifest"]
        recipe=json.loads(sources["geometry_recipe"].read_text(encoding="utf8"))
        if digest(manifest_path) != recipe["manifest_sha256"]:
            raise ValueError(f"{name} decoded donor pin changed")
        report=json.loads(sources["geometry_report"].read_text(encoding="utf8"))
        body=json.loads(sources["material_source"].read_text(encoding="utf8"))
        cargo=json.loads(sources["cargo_material_source"].read_text(encoding="utf8"))
        if body["source_texture"] == cargo["source_texture"]:
            raise ValueError(f"{name} rider and cargo albedo slots unexpectedly alias")
        for receipt in (body,cargo):
            if digest(Path(receipt["source"])) != receipt["source_sha256"] or \
               digest(Path(receipt["pattern_source"])) != receipt["pattern_sha256"]:
                raise ValueError(f"{name} native material input changed")
        albedo_variants=[
            {"source_texture":receipt["source_texture"],
             "authored_png":str(sources[key].relative_to(ROOT)),
             "sha256":digest(sources[key])}
            for receipt,key in ((body,"authored_albedo"),(cargo,"authored_cargo_albedo"))
            if receipt["changed_pixels"] > 0
        ]
        row={"family":"trader","age":age,"sex":sex,"private_variant_name":name,
             "private_resource_stem":f"art/scenario/garrison/berber_units_050/{name}/{name}",
             "official_donor_rgm":donor["logical_path"],
             "official_donor_rgm_sha256":donor["native_resource_sha256"],
             "decoded_manifest":donor["decoded_manifest"],
             "decoded_manifest_sha256":digest(manifest_path),
             "native_source_rrgeom_sha256":report["source_sha256"],
             "albedo_variants":albedo_variants,
             "design":"Bounded native cargo-cover and rider garment tailoring; age II indigo, III sage, IV patterned blue lower clothing; native sex, cargo, tack, coat, skin and owner-mask sources retained",
             "cargo_albedo":"unchanged native pixels; retained comparison PNG is not a cooked replacement",
             "owner_pattern_sources":[
                 {"source":receipt["pattern_source"],"sha256":receipt["pattern_sha256"]}
                 for receipt in (body,cargo)],
             "native_material_cook":"pending root serial per-albedo material compose",
             "native_animation":"unverified",
             "native_team_colour":"unverified; red and blue shader previews only"}
        for key,path in sources.items():
            row[key]=str(path.relative_to(ROOT))
            row[key+"_sha256"]=digest(path)
        rows.append(row)
    target=ART/"trader"/"trader-manifest.json"
    target.write_text(json.dumps({"schema":"berber-050-civilian-art/v1",
                                  "status":"trader_exact_horse_sources_ready_native_cook_pending",
                                  "trader":rows,
                                  "rejected_camel_probes":str((ART/"trader"/"probes").relative_to(ROOT))},indent=2)+"\n",encoding="utf8")
    print(target,flush=True)


def reconcile_villager_manifests():
    """Refresh JSON pins only after proving immutable native/art input hashes."""
    rows=[]
    for family,age,donor in family_donors():
        if family != "villager":
            continue
        name=f"villager_age0{age}"
        out=ART/"villager"/name
        path=out/"recipe.json"
        recipe=json.loads(path.read_text(encoding="utf8"))
        old_recipe_sha=digest(path)
        manifest_path=ROOT/donor["decoded_manifest"]
        manifest=json.loads(manifest_path.read_text(encoding="utf8"))
        current_manifest_sha=digest(manifest_path)
        source=source_geometry(manifest_path,manifest)
        native_rgm=ROOT/donor["bucket"] / "source" / Path(donor["logical_path"]).name
        material=json.loads((out/"material-source.json").read_text(encoding="utf8"))
        expected={"geometry":recipe["geometry_sha256"],
                  "native_rgm":donor["native_resource_sha256"],
                  "albedo":material["source_sha256"],
                  "pattern":material["pattern_sha256"]}
        actual={"geometry":digest(source),"native_rgm":digest(native_rgm),
                "albedo":digest(Path(material["source"])),
                "pattern":digest(Path(material["pattern_source"]))}
        if actual != expected:
            raise ValueError(f"{name} donor input changed: {actual} != {expected}")
        candidate=out/(name+".rrgeom")
        before_candidate_sha=digest(candidate)
        row={"variant":name,"manifest":str(manifest_path.relative_to(ROOT)),
             "old_manifest_sha256":recipe["manifest_sha256"],
             "new_manifest_sha256":current_manifest_sha,
             "old_recipe_sha256":old_recipe_sha,
             "native_input_hashes":actual,"candidate_sha256_before":before_candidate_sha,
             "reason":"donor intake reused nested decoded manifest after a redundant re-decode bug was fixed"}
        recipe["manifest_sha256"]=current_manifest_sha
        path.write_text(json.dumps(recipe,indent=2)+"\n",encoding="utf8")
        receipt=remix(path)
        if receipt["output_sha256"] != before_candidate_sha:
            raise ValueError(f"{name} authored geometry changed after manifest pin refresh")
        row["new_recipe_sha256"]=digest(path)
        row["candidate_sha256_after"]=receipt["output_sha256"]
        row["status"]="native inputs and authored geometry byte-identical"
        rows.append(row)
    target=ART/"villager"/"manifest-reconciliation.json"
    target.write_text(json.dumps({"schema":"berber-050-donor-manifest-reconciliation/v1",
                                  "status":"verified_native_inputs_identical",
                                  "rows":rows},indent=2)+"\n",encoding="utf8")
    villager_manifest()
    print(target,flush=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--family",choices=["villager","imam","trader","king"])
    p.add_argument("--age",type=int)
    p.add_argument("--manifest",action="store_true")
    p.add_argument("--reconcile",action="store_true")
    a=p.parse_args()
    if a.manifest:
        if a.family in ("imam","king"):
            regional_manifest(a.family)
        elif a.family == "trader":
            trader_manifest()
        else:
            villager_manifest()
        return
    if a.reconcile:
        reconcile_villager_manifests()
        return
    for family,age,donor in family_donors():
        if a.family and family != a.family or a.age and age != a.age:
            continue
        prepare_one(family,age,donor)
    if not a.family or a.family == "trader":
        for age,sex,donor in trader_exact_donors():
            if a.age and age != a.age:
                continue
            prepare_one("trader",age,donor,f"trader_age0{age}"+("_female" if sex=="female" else ""))


if __name__=="__main__":
    main()
