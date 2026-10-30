"""Read-only file audit in a task-owned background Blender; never saves sources."""
import bpy,json,os,stat,traceback,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
EXTERNAL=Path('F:/aoe_4_temp/Berber_future_kingdom_ai_20261014')
OUT=EXTERNAL/'output/berber_update_1_0_5'
paths=[];extra='--diagnostics' in sys.argv
roots=[EXTERNAL/'output/berber_update_0_6_0',EXTERNAL/'output/discoveries'] if extra else [ROOT/'art',EXTERNAL/'art']
for root in roots:
 for folder,dirs,files in os.walk(root,followlinks=False):
  dirs[:]=[d for d in dirs if not (Path(folder)/d).lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT]
  paths.extend(Path(folder)/f for f in files if Path(f).suffix.lower().startswith('.blend'))
rows=[]
for i,path in enumerate(sorted(paths)):
 try:
  bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
  images=[];libraries=[]
  for image in bpy.data.images:
   if image.packed_file or image.source in ('GENERATED','VIEWER') or not image.filepath:continue
   resolved=Path(bpy.path.abspath(image.filepath,library=image.library))
   images.append({'name':image.name,'original':image.filepath,'resolved':str(resolved),'exists':resolved.is_file()})
  for library in bpy.data.libraries:
   resolved=Path(bpy.path.abspath(library.filepath))
   libraries.append({'original':library.filepath,'resolved':str(resolved),'exists':resolved.is_file()})
  rows.append({'path':str(path),'images':images,'libraries':libraries,'objects':len(bpy.data.objects),'meshes':len(bpy.data.meshes)})
 except Exception as exc:rows.append({'path':str(path),'error':str(exc),'trace':traceback.format_exc()})
 if i%10==0:print('BLEND_AUDIT',i,len(paths),flush=True)
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/('blender-diagnostic-dependencies.json' if extra else 'blender-dependencies.json')).write_text(json.dumps({'blender':bpy.app.version_string,'files':rows,'complete':i==len(paths)-1},indent=2))
print('BLEND_AUDIT_DONE',len(rows),flush=True)
