# University Age IV source delivery

Live target and official decoded requirement prove Imperial-only and an 8 x 8 metre footprint. Current villager command references building_tech_university_mal. This is not a landmark, so no construction/completion age shift applies.

Architecture source: https://www.medersabenyoussef.ma/en/architecture/ (the monument's own architecture description). Evidence: central courtyard, four facades, cedar carving, stucco and geometric ornament. This asset interprets the courtyard/gallery organization in a restrained low learning complex; it does not replicate the monument or invent inscriptions. Shelves, bound manuscripts, slate tablets and reading benches are role-legibility inference, not a historical inventory claim. Slate/chalk props avoid modern freestanding classroom blackboards.

Anatomy: 7.6m square stone-ground court; two 2.60m high sheltered galleries with four hollow horseshoe arcade modules each; taller 3.34m rear library with three open study bays; centered carved entry arch, low flat roofs/parapets, neutral owner bands. No minaret, dome, ritual pool or landmark iconography. Height/silhouette are deliberately lower than the ceremonial Mosque/Madrasa landmark family.

Garrison 0.1.4 decoded the installed Abbasid Age IV university as the closest stock typology. Untouched decoded mesh positions/topology are retained in a reference blend. Final geometry is newly authored: courtyard clearance and functional library props are easier to audit with source modules than with a single dense donor stage mesh. Measured stock render bounds are recorded separately and are not gameplay footprint evidence.

Run research/buildings_batch/university/run_hidden.py with the bundled Python. It uses a hidden task-owned Blender process and private config; build_university.py is the final reproducible recipe. Earlier create_recipe.py and repair scripts preserve authoring history; final recipe includes their changes.

Maps share one atlas UV: albedo, roughness, neutral tangent normal, nonmetal, red-only owner pattern. Material ber_owner_mask annotations designate neutral friezes/banner. Maps are authored defaults, not baked donor detail. The static Garrison building shader does not yet qualify native owner-colour integration; see shared PLAYER_COLOUR_CONTRACT.md. Construction manifest is cumulative source visibility, with native stage selectors still pending.

Verification includes closed/outward finite solids, positive transforms, nonzero UV faces, 8m footprint bounds, floor and roof/table/manuscript contacts, central 1.8m source route and fitted arcade ray tests at 0.5/1.3m. These are source geometry proofs, not native walk surfaces or navigation. No mod cook or native game test is performed. Future gates: structure/native owner colour, stage/attachment/LOD binding, scale/orientation and native appearance/research behavior.
