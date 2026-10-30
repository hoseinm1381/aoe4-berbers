from pathlib import Path
p=Path('art/buildings/outpost/build_outpost.py');s=p.read_text().replace("scene.render.engine='CYCLES'","scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='MATERIAL';scene.display.shading.light='STUDIO';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.render_aa='8'");p.write_text(s)
