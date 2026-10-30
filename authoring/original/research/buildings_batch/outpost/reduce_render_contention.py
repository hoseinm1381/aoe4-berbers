from pathlib import Path
p=Path('art/buildings/outpost/build_outpost.py');s=p.read_text().replace("scene=bpy.context.scene;scene.render.engine='CYCLES';", "scene=bpy.context.scene;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.engine='CYCLES';");p.write_text(s)
